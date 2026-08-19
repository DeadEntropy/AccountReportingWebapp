# tabs.py
import dash_bootstrap_components as dbc
from dash import dcc

TAB_BORDER = "1px solid #d6d6d6"

tabs_styles = {"height": "44px", "alignItems": "center"}
tab_style = {
    "borderBottom": TAB_BORDER,
    "padding": "6px",
    "fontWeight": "bold",
    "borderRadius": "15px",
    "backgroundColor": "#F2F2F2",
    "boxShadow": "4px 4px 4px 4px lightgrey",
}

tab_selected_style = {
    "borderTop": TAB_BORDER,
    "borderBottom": TAB_BORDER,
    "backgroundColor": "#119DFF",
    "color": "white",
    "padding": "6px",
    "borderRadius": "15px",
}


def get_tabs():
    """generate the container for the apps' tabs"""
    return dbc.Row(
        dbc.Col(
            dcc.Tabs(
                [
                    dcc.Tab(label="Tab 1: Wealth Breakdown", id="tab1", style=tab_style, selected_style=tab_selected_style),
                    dcc.Tab(label="Tab 2: Spending Details", id="tab2", style=tab_style, selected_style=tab_selected_style),
                    dcc.Tab(label="Tab 3: Capital PnL Breakdown", id="tab3", style=tab_style, selected_style=tab_selected_style),
                    dcc.Tab(label="Tab 4: Saving Rate", id="tab4", style=tab_style, selected_style=tab_selected_style),
                ],
                style=tabs_styles,  # Adjusted margin
            ),
            width=12,
        ),
    )
