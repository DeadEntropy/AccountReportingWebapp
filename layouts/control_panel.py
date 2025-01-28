# control_panel.py
import dash_bootstrap_components as dbc
from dash import dcc, html
from src import defaults


def get_control_panel(default_year, categories):
    """generates the control panel of the app"""
    return dbc.Row(
        dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    html.Div(
                        [
                            # Year Dropdown
                            html.Div(
                                [
                                    html.Label("Select Year:", className="fw-bold me-2"),  # Label next to dropdown
                                    dcc.Dropdown(
                                        id="year-dropdown",
                                        options=[{"label": str(year), "value": year} for year in defaults.YEARS],
                                        value=default_year,
                                        clearable=False,
                                        style={"width": "200px"},  # Adjusted width
                                    ),
                                ],
                                className="d-flex align-items-center me-4",  # Align items and add spacing
                            ),
                            # Checkbox
                            html.Div(
                                [
                                    dcc.Checklist(
                                        id="capital-gain-checkbox",
                                        options=[
                                            {
                                                "label": html.Span("Capital Gain", className="fw-bold"),  # Bold label
                                                "value": "include_capital_gain",
                                            }
                                        ],
                                        value=[],
                                    ),
                                ],
                                className="d-flex align-items-center me-4 mt-1",  # Align and space
                            ),
                            # Category Dropdown
                            html.Div(
                                [
                                    html.Label("Select Category:", className="fw-bold me-2"),  # Label next to dropdown
                                    dcc.Dropdown(
                                        id="category-dropdown",
                                        options=[{"label": category, "value": category} for category in categories],
                                        value=defaults.DEFAULT_CATEGORY,
                                        clearable=False,
                                        style={"width": "300px"},  # Larger width for longer categories
                                    ),
                                ],
                                className="d-flex align-items-center",  # Align items
                            ),
                        ],
                        className="d-flex justify-content-center align-items-center",  # Align items horizontally and center
                    )
                ),
                className="shadow-sm mb-3 bg-light rounded",  # Adjusted margin
            ),
            width=12,
        ),
    )
