from io import StringIO
import os
import re
import warnings
import requests
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT, "data")
OUT_DIR = os.path.join(ROOT, "outputs")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

YEARS = range(2013, 2026)
BASE_URL = "https://www.cmfri.org.in/state{}"
STATE_NAMES = [
    "West Bengal", "Odisha", "Orissa", "Andhra Pradesh", "Tamil Nadu",
    "Puducherry", "Pondicherry", "Kerala", "Karnataka", "Goa",
    "Maharashtra", "Gujarat", "Daman and Diu", "Daman & Diu",
    "Andaman and Nicobar Islands"
]

def clean_num(value):
    if pd.isna(value):
        return np.nan
    s = str(value).replace(",", "").strip()
    try:
        return float(s)
    except ValueError:
        return np.nan

def flatten_columns(df):
    df = df.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [" ".join(str(x) for x in col if str(x) != "nan").strip() for col in df.columns]
    else:
        df.columns = [str(c).strip() for c in df.columns]
    return df

def extract_from_table(table, year):
    df = flatten_columns(table)
    # Some pages have no proper header row; inspect the first rows as text too.
    cols = [re.sub(r"[^a-z]", "", c.lower()) for c in df.columns]
    state_col = next((i for i,c in enumerate(cols) if "state" in c), None)
    total_col = next((i for i,c in enumerate(cols) if "total" in c or "landing" in c), None)
    year_col = next((i for i,c in enumerate(cols) if c == "year"), None)

    if state_col is None:
        # Try tables where the first row contains the column headings.
        for ridx in range(min(3, len(df))):
            row = [re.sub(r"[^a-z]", "", str(x).lower()) for x in df.iloc[ridx].tolist()]
            if any("state" in x for x in row) and any("total" in x or "landing" in x for x in row):
                df.columns = [str(x).strip() for x in df.iloc[ridx].tolist()]
                df = df.iloc[ridx+1:].reset_index(drop=True)
                return extract_from_table(df, year)
        return []

    if total_col is None:
        # Total is often the final column in CMFRI state-wise assemblage tables.
        total_col = len(df.columns) - 1

    rows = []
    for _, row in df.iterrows():
        state = str(row.iloc[state_col]).strip()
        if state.lower() in ("nan", "state", ""):
            continue
        aliases = {
    "orissa": "Odisha",
    "odisha": "Odisha",
    "pondicherry": "Puducherry",
    "puducherry": "Puducherry"
}
        matched = next((s for s in STATE_NAMES if s.lower() == state.lower()), None)
        if not matched:
            continue

def main():
    all_rows, logs = [], []
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (compatible; student research project)"})

    print("Collecting CMFRI state-wise tables...")
    for year in YEARS:
        url = BASE_URL.format(year)
        try:
            response = session.get(url, timeout=30)
            response.raise_for_status()
            tables = pd.read_html(StringIO(response.text))
            found = []
            for table in tables:
                found.extend(extract_from_table(table, year))
            # Keep one row per state/year in case multiple tables repeat records.
            found = pd.DataFrame(found).drop_duplicates(["state", "year"], keep="last").to_dict("records") if found else []
            all_rows.extend(found)
            logs.append({"year": year, "status": "records found" if found else "page loaded; no matching state table", "records": len(found), "url": url})
            print(f"{year}: {len(found)} state records")
        except Exception as e:
            logs.append({"year": year, "status": "download/read failed: " + str(e)[:180], "records": 0, "url": url})
            print(f"{year}: could not read page ({type(e).__name__})")

    log_path = os.path.join(OUT_DIR, "source_log.csv")
    pd.DataFrame(logs).to_csv(log_path, index=False)

    if not all_rows:
        print("\\nNo state-wise rows were recognized automatically.")
        print("The year-by-year status is saved in outputs/source_log.csv.")
        print("Do not use invented data. Open the CMFRI state-wise page and check the table layout.")
        return

    data = pd.DataFrame(all_rows).drop_duplicates(["state", "year"]).sort_values(["state", "year"])
    data_path = os.path.join(DATA_DIR, "state_landings.csv")
    data.to_csv(data_path, index=False)
    print(f"\\nSaved {len(data)} observations to data/state_landings.csv")

    forecasts = []
    for state, group in data.groupby("state"):
        group = group.dropna(subset=["landings_tonnes"]).sort_values("year")
        if group["year"].nunique() < 5:
            forecasts.append({"state": state, "forecast_2026_tonnes": np.nan,
                              "observations": len(group), "status": "insufficient historical years"})
            continue
        model = LinearRegression()
        X = group[["year"]].values
        y = group["landings_tonnes"].values
        model.fit(X, y)
        prediction = float(model.predict(np.array([[2026]]))[0])
        forecasts.append({"state": state, "forecast_2026_tonnes": max(0, round(prediction, 2)),
                          "observations": len(group), "status": "trend model"})
    forecast_df = pd.DataFrame(forecasts).sort_values("state")
    forecast_df.to_csv(os.path.join(OUT_DIR, "forecast_2026.csv"), index=False)

    plt.figure(figsize=(11, 6))
    for state, group in data.groupby("state"):
        plt.plot(group["year"], group["landings_tonnes"], marker="o", linewidth=1, label=state)
    plt.title("State-wise Marine Fish Landings (CMFRI data)")
    plt.xlabel("Year")
    plt.ylabel("Landings (tonnes)")
    plt.legend(fontsize=7, ncol=2)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "landings_trend.png"), dpi=180)
    plt.close()

    print("\\n2026 forecast preview:")
    print(forecast_df.to_string(index=False))
    print("\\nDone. Check data/ and outputs/ folders.")

if __name__ == "__main__":
    main()
