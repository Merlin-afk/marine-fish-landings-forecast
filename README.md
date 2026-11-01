# Marine Fish Landings Forecasting (Simple Version)

## What this project does
- Collects state-wise marine fish landing tables from CMFRI pages where available.
- Cleans the data into one CSV file.
- Produces a simple 2026 forecast using a linear trend for each state.
- Saves a graph and result files.

## Data source
ICAR-CMFRI: https://www.cmfri.org.in/fish-catch-estimates
CMFRI annual data: https://www.cmfri.org.in/annual-data

## Requirements
Python 3.10 or newer.

## Setup (Windows)
Open Command Prompt in this folder and run:

    py -m venv .venv
    .venv\Scripts\activate
    python -m pip install -r requirements.txt
    python run_project.py

If you already have a working .venv, just activate it, install requirements, and run the script.

## Important data note
CMFRI's online state-wise pages currently list 2013-2025. The script tries those year pages.
Older historical state-year data may be present in CMFRI's annual-data resource, but the website's table layout can vary. The script will report exactly which years it successfully extracted. It will not invent missing values.
A state needs at least 5 annual observations for a trend forecast. If fewer are available, it is listed as insufficient data rather than receiving a made-up forecast.

## Output
- data/state_landings.csv: extracted source data
- outputs/forecast_2026.csv: forecast results
- outputs/landings_trend.png: chart
- outputs/source_log.csv: years attempted and extraction status

## Suggested project title
Forecasting State-Wise Marine Fish Landings in India Using Historical Trends

## Methodology in brief
The project uses historical annual marine fish landing estimates published by CMFRI. The data are cleaned and grouped by state. A linear regression trend model is fitted separately for each state, and the fitted trend is extended to 2026. This is a simple baseline forecasting method, not a guarantee of actual future landings.
