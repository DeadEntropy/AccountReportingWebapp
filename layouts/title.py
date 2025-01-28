# title.py
import dash_bootstrap_components as dbc
from dash import html


def get_title():
    """generate the title of the app"""
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
