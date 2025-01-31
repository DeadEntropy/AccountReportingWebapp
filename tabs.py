from dash import dcc, html, dash_table
from dash.dash_table.Format import Format, Scheme
import dash_bootstrap_components as dbc
from bkanalysis.ui.salary import Salary
from bkanalysis.ui import ui

ACCOUNT_TYPE = "AccountType"


def get_color(v):
    """Returns the color to apply in a card based on a float value"""
    return "text-success" if v > 0 else "text-danger" if v > 0 else "text-warning"


def get_tab_1(
    df_cash_account_type,
    total_value_end,
    total_value_start,
    salary: Salary,
    total_spend,
    capital_gain,
    fig_spend_waterfall,
    fig_wealth,
):
    """Returns the layout of the first tab"""
    assert df_cash_account_type.columns[0] == ACCOUNT_TYPE, f"Incorrect Columns, expected {ACCOUNT_TYPE} but got {df_cash_account_type.columns[0]}."
    assert len(df_cash_account_type.columns) == 3, f"Incorrect Columns count, expected 3 but got {len(df_cash_account_type.columns)}."

    first_month = df_cash_account_type.columns[1]
    last_month = df_cash_account_type.columns[2]

    capital_gain_color = get_color(capital_gain)
    yoy_wealth_change_color = get_color(total_value_end - total_value_start)

    return dbc.Container(
        [
            dbc.Row(
                [
                    # Separator
                    html.Hr(style={"borderTop": "2px solid #dee2e6", "marginTop": "10px", "marginBottom": "10px"}),
                    # Main content section
                    dbc.Row(
                        [
                            # Card displaying total value
                            dbc.Col(
                                dbc.Card(
                                    dbc.CardBody(
                                        [
                                            html.H4("Total Wealth", className="card-title"),
                                            html.H2(
                                                f"${total_value_end:,.0f}",
                                                className="card-text text-success fw-bold",
                                            ),
                                        ]
                                    ),
                                    className="mb-3",
                                )
                            ),
                            # Card displaying Year-on-Year change
                            dbc.Col(
                                dbc.Card(
                                    dbc.CardBody(
                                        [
                                            html.H4("YoY Wealth Change", className="card-title"),
                                            html.H2(
                                                f"${total_value_end - total_value_start:,.0f}",
                                                className=f"card-text {yoy_wealth_change_color} fw-bold",
                                            ),
                                        ]
                                    ),
                                    className="mb-3",
                                )
                            ),
                            # Card displaying Salary Perceived during that year value
                            dbc.Col(
                                dbc.Card(
                                    dbc.CardBody(
                                        [
                                            html.H4(
                                                "Received Salary",
                                                className="card-title",
                                            ),
                                            html.H2(
                                                f"${salary.actual_salary:,.0f}",
                                                className="card-text text-success fw-bold",
                                            ),
                                        ]
                                    ),
                                    className="mb-3",
                                )
                            ),
                            # Card displaying Missing Salary for that year value
                            dbc.Col(
                                dbc.Card(
                                    dbc.CardBody(
                                        [
                                            html.H4(
                                                "Outstanding Salary",
                                                className="card-title",
                                            ),
                                            html.H2(
                                                f"${salary.outstanding_salary:,.0f}",
                                                className="card-text text-warning fw-bold",
                                            ),
                                        ]
                                    ),
                                    className="mb-3",
                                )
                            ),
                            # Card displaying Capital Gain/Loss during that year value
                            dbc.Col(
                                dbc.Card(
                                    dbc.CardBody(
                                        [
                                            html.H4("Capital Gain", className="card-title"),
                                            html.H2(
                                                f"${capital_gain:,.0f}",
                                                className=f"card-text {capital_gain_color} fw-bold",
                                            ),
                                        ]
                                    ),
                                    className="mb-3",
                                )
                            ),
                            # Card displaying Total Spending during that year value
                            dbc.Col(
                                dbc.Card(
                                    dbc.CardBody(
                                        [
                                            html.H4("Total Spending", className="card-title"),
                                            html.H2(
                                                f"${total_spend:,.0f}",
                                                className="card-text text-danger fw-bold",
                                            ),
                                        ]
                                    ),
                                    className="mb-3",
                                )
                            ),
                        ]
                    ),
                    # Main content section
                    dbc.Row(
                        [
                            # Left column for summary
                            dbc.Col(
                                html.Div(
                                    [
                                        dcc.Graph(figure=fig_wealth),
                                        html.Div("Breakdown by Account Type"),
                                        dash_table.DataTable(
                                            columns=[
                                                {
                                                    "name": "Account Type",
                                                    "id": ACCOUNT_TYPE,
                                                    "type": "text",
                                                },
                                                {
                                                    "name": first_month,
                                                    "id": first_month,
                                                    "type": "numeric",
                                                    "format": Format(
                                                        precision=0,
                                                        scheme=Scheme.fixed,
                                                        group=True,
                                                    ),
                                                },
                                                {
                                                    "name": last_month,
                                                    "id": last_month,
                                                    "type": "numeric",
                                                    "format": Format(
                                                        precision=0,
                                                        scheme=Scheme.fixed,
                                                        group=True,
                                                    ),
                                                },
                                            ],
                                            data=df_cash_account_type.to_dict("records"),
                                            style_table={"overflowX": "auto"},  # Handle table overflow
                                            style_cell={
                                                "textAlign": "left",
                                                "padding": "5px",  # Reduced padding for smaller row height
                                                "lineHeight": "15px",  # Adjust line height for compactness
                                            },
                                            style_header={
                                                "backgroundColor": "lightgrey",
                                                "fontWeight": "bold",
                                            },
                                            style_data_conditional=[
                                                {
                                                    "if": {
                                                        "filter_query": f"{{{first_month}}} > 0",
                                                        "column_id": first_month,
                                                    },
                                                    "color": "green",
                                                    "fontWeight": "bold",
                                                },
                                                {
                                                    "if": {
                                                        "filter_query": f"{{{first_month}}} < 0",
                                                        "column_id": first_month,
                                                    },
                                                    "color": "red",
                                                    "fontWeight": "bold",
                                                },
                                                {
                                                    "if": {
                                                        "filter_query": f"{{{last_month}}} > 0",
                                                        "column_id": last_month,
                                                    },
                                                    "color": "green",
                                                    "fontWeight": "bold",
                                                },
                                                {
                                                    "if": {
                                                        "filter_query": f"{{{last_month}}} < 0",
                                                        "column_id": last_month,
                                                    },
                                                    "color": "red",
                                                    "fontWeight": "bold",
                                                },
                                            ],
                                            style_as_list_view=True,  # Render rows more compactly
                                        ),
                                    ],
                                    className="border p-3",
                                ),
                                width=6,  # Adjust column width
                            ),
                            # Right column for detailed info
                            dbc.Col(
                                html.Div(
                                    [
                                        dcc.Graph(figure=fig_spend_waterfall),
                                    ],
                                    className="border p-3",
                                ),
                                width=6,
                            ),
                        ],
                        className="mb-4",
                    ),
                ]
            )
        ],
        fluid=True,  # Allows full-width responsive layout
    )


def get_tab_2(total_spend, category, fig_category_brkdn, fig_spend_brkdn, df_category_brkdn):
    """Returns the layout of the second tab"""

    category_spend = df_category_brkdn["Value"].sum()
    category_spend_color = get_color(category_spend)

    return dbc.Row(
        [
            # Separator
            html.Hr(style={"borderTop": "2px solid #dee2e6", "marginTop": "10px", "marginBottom": "10px"}),
            dbc.Col(
                [
                    dbc.Row(
                        [
                            # Card displaying Total Spending during that year value
                            dbc.Col(
                                dbc.Card(
                                    dbc.CardBody(
                                        [
                                            html.H4("Total Spending", className="card-title"),
                                            html.H2(
                                                f"${total_spend:,.0f}",
                                                className="card-text text-danger fw-bold",
                                            ),
                                        ]
                                    ),
                                    id="total-spending-card",
                                    className="mb-3",
                                )
                            ),
                            # Card displaying Category Spending during that year value
                            dbc.Col(
                                dbc.Card(
                                    dbc.CardBody(
                                        [
                                            html.H4(f"{category} Spending", className="card-title"),
                                            html.H2(
                                                f"${category_spend:,.0f}",
                                                className=f"card-text {category_spend_color} fw-bold",
                                            ),
                                        ]
                                    ),
                                    className="mb-3",
                                )
                            ),
                        ]
                    ),
                    dcc.Graph(figure=fig_spend_brkdn, style={"height": "600px"}),
                ],  # Top-right
                width=6,
                style={"display": "flex", "flexDirection": "column", "height": "100%"},
            ),
            dbc.Col(
                [
                    dcc.Graph(figure=fig_category_brkdn),  # Bottom-left
                    dash_table.DataTable(
                        columns=[
                            {
                                "name": df_category_brkdn.columns[0],
                                "id": df_category_brkdn.columns[0],
                                "type": "text",
                            },
                            {
                                "name": df_category_brkdn.columns[1],
                                "id": df_category_brkdn.columns[1],
                                "type": "numeric",
                                "format": Format(precision=0, scheme=Scheme.fixed, group=True),
                            },
                        ],
                        data=df_category_brkdn.to_dict("records"),
                        style_table={"overflowX": "auto"},  # Handle table overflow
                        style_cell={
                            "textAlign": "left",
                            "padding": "5px",  # Reduced padding for smaller row height
                            "lineHeight": "15px",  # Adjust line height for compactness
                        },
                        style_header={
                            "fontWeight": "bold",
                        },
                        style_data_conditional=[],
                        style_as_list_view=True,  # Render rows more compactly
                    ),  # Bottom-right
                ],
                width=6,
                style={"display": "flex", "flexDirection": "column", "height": "100%"},
            ),
        ]
    )
