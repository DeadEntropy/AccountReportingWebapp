# callbacks.py
from datetime import datetime
from dash import Input, Output
from bkanalysis.salary import Salary
from src import defaults
import tabs

from bkanalysis.managers import TransformationManager, TransformationManagerCache, FigureManager


def register_callbacks(app, transformation_manager: TransformationManager | TransformationManagerCache, figure_manager: FigureManager, base_salary):
    """registers the callbacks of the dash app"""

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

        df_cash_account_type = transformation_manager.get_price_comparison_on_dates(date_range[0], date_range[1], True)

        total_value_start = df_cash_account_type.sum()[f"{date_range[0].date():%b-%y}"]
        total_value_end = df_cash_account_type.sum()[f"{date_range[1].date():%b-%y}"]
        total_spend = transformation_manager.get_flow_values(date_range[0], date_range[1], None, how="out", include_iat=False).Value.sum()

        salary = Salary(
            transformation_manager,
            date_range[1].year,
            datetime(selected_year - 1, 1, 1),
            base_salary[selected_year],
            defaults.DEFAULT_PAYROLLS_1,
            defaults.BASE_PAYROLL_1,
            None,
            defaults.DEFAULT_PAYROLLS_2,
            defaults.BASE_PAYROLL_2,
            defaults.EXCLUDE_DEFAULT,
        )

        capital_pnl = transformation_manager.get_values_by_asset(date_range, None).CapitalGain.sum()

        fig_spend_waterfall = figure_manager.get_figure_waterfall(date_range, salary_override=salary, include_capital_gain=include_capital_gain)

        fig_wealth = figure_manager.get_figure_timeseries(date_range)

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
    def update_tab_2_year(selected_year, category):
        """Update the second tab of the webapp."""
        start_date = datetime(selected_year, 1, 1)
        end_date = datetime(selected_year, 12, 31)
        date_range = [start_date, end_date]

        category_key, category_value = category.split(": ")

        total_spend = transformation_manager.get_flow_values(date_range[0], date_range[1], None, how="out", include_iat=False).Value.sum()

        category_dict = {f"Full{category_key}": category_value}
        label = "MemoMapped"

        df_category_brkdn = figure_manager.get_category_breakdown(category_dict, label, 10, date_range, None)
        fig_category_brkdn = figure_manager.get_figure_bar(category_dict, label, 5, date_range)

        fig_spend_brkdn = figure_manager.get_figure_sunburst(date_range=date_range)

        return tabs.get_tab_2(total_spend, category_value, fig_category_brkdn, fig_spend_brkdn, df_category_brkdn)
