# app.py
import configparser
from datetime import datetime

import dash_bootstrap_components as dbc
from bkanalysis.ui import ui, ui_old
from bkanalysis.ui.salary import Salary
from bkanalysis.config import config_helper as ch
from dash import Dash, Input, Output, dcc, html

import tabs
from lib import utils, defaults


DEFAULT_YEAR = datetime.today().year - 1
BASE_SALARY = {**{y: None for y in defaults.YEARS}, **{2024: defaults.BASE_SALARY_1}}
DEFAULT_CONFIG = ch.source

config = configparser.ConfigParser()
if len(config.read(ch.source)) != 1:
    raise OSError(f"no config found in {ch.source}")

### Get Data From Cache
fd = utils.read_csv("data", defaults.REF_CURRENCY, config)
CATEGORIES = fd.get_all_categories([datetime(DEFAULT_YEAR, 1, 1), datetime(DEFAULT_YEAR, 12, 31)], defaults.THRESHOLD)

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

tabs_styles = {"height": "44px", "align-items": "center"}
tab_style = {
    "borderBottom": "1px solid #d6d6d6",
    "padding": "6px",
    "fontWeight": "bold",
    "border-radius": "15px",
    "background-color": "#F2F2F2",
    "box-shadow": "4px 4px 4px 4px lightgrey",
}

tab_selected_style = {
    "borderTop": "1px solid #d6d6d6",
    "borderBottom": "1px solid #d6d6d6",
    "backgroundColor": "#119DFF",
    "color": "white",
    "padding": "6px",
    "border-radius": "15px",
}


def get_control_panel():
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
                                        value=DEFAULT_YEAR,
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
                                        options=[{"label": category, "value": category} for category in CATEGORIES],
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


def get_tabs():
    return dbc.Row(
        dbc.Col(
            dcc.Tabs(
                [
                    dcc.Tab(label="Tab 1: Wealth Breakdown", id="tab1", style=tab_style, selected_style=tab_selected_style),
                    dcc.Tab(label="Tab 2: Spending Details", id="tab2", style=tab_style, selected_style=tab_selected_style),
                ],
                style=tabs_styles,  # Adjusted margin
            ),
            width=12,
        ),
    )


def get_title():
    return dbc.Row(
        dbc.Col(
            html.H1(
                "Year-End Spending Analysis",
                className="text-center",
                style={
                    "color": "#2c3e50",
                    "fontWeight": "bold",
                    "fontSize": "1.8rem",  # Reduced font size
                    "marginBottom": "15px",  # Reduced margin
                    "marginTop": "15px",  # Reduced margin
                },
            ),
            width=12,
        )
    )


app.layout = dbc.Container(
    [
        get_title(),
        html.Hr(style={"borderTop": "2px solid #dee2e6", "marginTop": "10px", "marginBottom": "10px"}),
        dcc.Loading(
            id="loading-indicator",
            type="circle",
            overlay_style={"visibility": "visible", "filter": "blur(2px)"},
            children=[
                get_control_panel(),
                get_tabs(),
            ],
        ),
    ],
    fluid=True,
    style={"backgroundColor": "#f8f9fa", "padding": "10px", "position": "relative"},  # Added relative position
)


# Callback to update the first tab
@app.callback(
    Output("tab1", "children"),
    [Input("year-dropdown", "value"), Input("capital-gain-checkbox", "value")],
)
def update_tab_1(selected_year, include_capital_gain):
    """Update the first tab of the webapp."""
    include_capital_gain = "include_capital_gain" in include_capital_gain  # Convert the list to a boolean

    start_date = datetime(selected_year, 1, 1)
    end_date = datetime(selected_year, 12, 31)
    date_range = [start_date, end_date]

    df_cash_account_type = fd.get_wealth_by_account_type(date_range)
    total_value_end, total_value_start, total_spend = fd.get_total_wealth(date_range)
    salary = Salary(
        fd.df_exp,
        date_range[1].year,
        datetime(selected_year - 1, 1, 1),
        BASE_SALARY[selected_year],
        defaults.DEFAULT_PAYROLLS_1,
        defaults.BASE_PAYROLL_1,
        None,
        defaults.DEFAULT_PAYROLLS_2,
        defaults.BASE_PAYROLL_2,
        defaults.EXCLUDE_DEFAULT,
    )

    capital_pnl = fd.get_capital_gain(date_range)

    ### Get Figures
    fig_spend_waterfall = ui.plot_spend_waterfall(
        fd.df_exp,
        date_range,
        salary_override=salary,
        inc_title=True,
        include_capital_gain=include_capital_gain,
    )

    fig_wealth = ui.plot_wealth(
        fd.df,
        date_range=date_range,
        by=([ui.CUMULATED_AMOUNT_CCY_EXCL_CAPITAL, ui.CUMULATED_AMOUNT_CCY] if include_capital_gain else ui.CUMULATED_AMOUNT_CCY_EXCL_CAPITAL),
        top_items_count=5,
        rename={
            ui.CUMULATED_AMOUNT_CCY: "With Cap Gain",
            ui.CUMULATED_AMOUNT_CCY_EXCL_CAPITAL: "No Cap Gain",
        },
    )

    return tabs.get_tab_1(
        df_cash_account_type,
        total_value_end,
        total_value_start,
        salary,
        total_spend,
        capital_pnl,
        fig_spend_waterfall,
        fig_wealth,
    )


# Callback to update the second tab
@app.callback(
    Output("tab2", "children"),
    [Input("year-dropdown", "value"), Input("category-dropdown", "value")],
)
def update_tab_2(selected_year, category):
    """Update the second tab of the webapp."""
    start_date = datetime(selected_year, 1, 1)
    end_date = datetime(selected_year, 12, 31)
    date_range = [start_date, end_date]

    category_key, category_value = category.split(": ")
    _, _, total_spend = fd.get_total_wealth(date_range)

    ### Get Figures
    df_category_brkdn = fd.get_category_breakdown(date_range, f"Full{category_key}", category_value, defaults.CATEGORY_MAP[category_key], 10)
    fig_category_brkdn = ui.plot_category_breakdown(
        fd.df_exp,
        f"Full{category_key}",
        category_value,
        defaults.CATEGORY_MAP[category_key],
        date_range,
        None,
        5,
        [],
    )

    fig_spend_brkdn = ui_old.plot_sunburst(
        fd.df_exp,
        ["FullType", "FullSubType", "MemoMapped"],
        date_range=date_range,
        values=ui.AMOUNT_CCY,
    )

    return tabs.get_tab_2(total_spend, category_value, fig_category_brkdn, fig_spend_brkdn, df_category_brkdn)


if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050, debug=False)
