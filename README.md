# AccountReportingWebapp

A personal-finance dashboard built with [Dash](https://dash.plotly.com/). It aggregates bank, brokerage, pension and crypto account data (prepared by the [AccountReporting](https://github.com/DeadEntropy/AccountReporting) package, `bkanalysis`) and presents an interactive year-by-year view of wealth, spending, capital gains and saving rate.

The app is designed to run as a Docker container on a home server and to read **pregenerated** data files, so no bank files are parsed and no market data is downloaded at runtime.

## Features

The dashboard is organised in four tabs, driven by a year selector, a category selector and a "Capital Gain" toggle:

1. **Wealth Breakdown** — total wealth, year-on-year change, received/outstanding salary, capital gain and total spending cards; a wealth time series with notable-transaction annotations; a breakdown by account type; and an income/spending waterfall.
2. **Spending Details** — a sunburst of all spending by category, plus a monthly bar chart and a top-items table for the selected category.
3. **Capital PnL Breakdown** — capital gain per asset with start value and yearly return; clicking a row plots the asset's quantity, price and value evolution.
4. **Saving Rate** — annual and monthly saving-rate gauges and a monthly income-vs-expenses chart.

## How it works

```
bank/broker CSV exports ──> bkanalysis (AccountReporting) ──> data_manager.csv
yahoo finance / files   ──> bkanalysis MarketManager      ──> data_market.csv (+ _asset_map.csv)
                                                                  │
                                              DATA_PATH (default /data)
                                                                  │
                                       app.py (Dash) ── managers from bkanalysis
```

- `app.py` — entry point: builds the layout, initialises managers and registers callbacks. Serves on `0.0.0.0:8050`.
- `app_initialisation.py` — loads `data_manager.csv`, `data_market.csv` and `data_market_asset_map.csv` from `DATA_PATH` and builds the `DataManager`, `MarketManager`, `TransformationManager` and `FigureManager`.
- `callbacks.py` — Dash callbacks that update each tab when the year/category selection changes.
- `tabs.py` — layout of the content of each tab.
- `layouts/` — title, control panel and tab container layout.
- `src/defaults.py` — user-specific settings: year range, salary/payroll configuration, income types, default category.
- `config/config.ini` — `bkanalysis` configuration (account formats, mappings, market sources).

### Generating the input data

The input CSVs are produced with the `AccountReporting` package (see `notebooks/run_data_manager.ipynb` in that repo):

```python
from bkanalysis.managers import DataManager, MarketManager

data_manager = DataManager()
data_manager.load_data_from_disk()       # parses the raw bank files
data_manager.to_disk("data_manager.csv")

market_manager = MarketManager("USD")
market_manager.load_prices(data_manager) # downloads market prices
market_manager.to_disk("data_market.csv")
```

Copy the resulting `data_manager.csv`, `data_market.csv` and `data_market_asset_map.csv` to the folder pointed to by `DATA_PATH`.

## Running locally

```bash
pip install -r requirements.txt   # installs bkanalysis from GitHub
set DATA_PATH=D:\path\to\data     # defaults to /data if unset
python app.py
```

Then open http://localhost:8050.

## Running with Docker

```bash
docker build -t account_reporting_ui .
docker run -p 8050:8050 -v /path/to/data:/data account_reporting_ui
```

`BUILD_HELP.bat` contains the commands used to build, tag and push the image to Docker Hub (`deadentropy/account_reporting_ui`).

## Tests

`test/` contains integration tests (`test_core.py`, `test_salary.py`) that exercise manager initialisation and the salary calculations. They require a populated `DATA_PATH` with real data, so they are meant to be run locally, not in CI:

```bash
python -m unittest discover test
```

`performance_testing.py` profiles a tab callback with `cProfile` and dumps a `.prof` file for analysis.

## Configuration notes

- The reporting currency is set in `app.py` (`REF_CURRENCY = "USD"`).
- The year dropdown range and the salary/payroll definitions live in `src/defaults.py` and must be kept up to date (e.g. extend `YEARS` at the start of a new year).
