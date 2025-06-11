# app.py
from datetime import datetime

import dash_bootstrap_components as dbc
import plotly.io as pio
from dash import Dash, dcc, html

from app_initialisation import initialize_managers
from callbacks import register_callbacks
from layouts.control_panel import get_control_panel
from layouts.tabs_container import get_tabs
from layouts.title import get_title
from src import defaults

USE_DARK_MODE = False

if USE_DARK_MODE:
    pio.templates.default = "plotly_dark"  # or your custom template

REF_CURRENCY = "USD"
DEFAULT_YEAR = datetime.today().year
BASE_SALARY = {**{y: None for y in defaults.YEARS}, **{2024: defaults.BASE_SALARY_1}}

data_manager, market_manager, transformation_manager, figure_manager = initialize_managers(REF_CURRENCY, DEFAULT_YEAR)

CATEGORIES = transformation_manager.get_all_categories([datetime(DEFAULT_YEAR, 1, 1), datetime(DEFAULT_YEAR, 12, 31)], defaults.THRESHOLD)

app = Dash(__name__, external_stylesheets=[dbc.themes.CYBORG if USE_DARK_MODE else dbc.themes.BOOTSTRAP])

app.layout = dbc.Container(
    [
        get_title(),
        html.Hr(style={"borderTop": "2px solid", "marginTop": "10px", "marginBottom": "10px"}),
        dcc.Loading(
            id="loading-indicator",
            type="circle",
            overlay_style={"visibility": "visible", "filter": "blur(2px)"},
            children=[
                get_control_panel(DEFAULT_YEAR, CATEGORIES),
                get_tabs(),
            ],
        ),
    ],
    fluid=True,
    style={"padding": "10px", "position": "relative"},  # Added relative position
)

register_callbacks(app, transformation_manager, figure_manager, BASE_SALARY, CATEGORIES)

if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050, debug=False)
