# callbacks.py
from datetime import datetime
from dash import Input, Output

from bkanalysis.salary import Salary, SalaryLegacy
from bkanalysis.managers import TransformationManager, TransformationManagerCache, FigureManager

from src import defaults
import tabs


def register_callbacks(app, transformation_manager: TransformationManager | TransformationManagerCache, figure_manager: FigureManager, base_salary, categories):
    """registers the callbacks of the dash app"""

    @app.callback(
        Output("tab1", "children"),
        [Input("year-dropdown", "value"), Input("capital-gain-checkbox", "value")],
    )
    def update_tab_1(selected_year, include_capital_gain):
        """Callback to update the 'Wealth Breakdown' tab."""
        include_capital_gain = "include_capital_gain" in include_capital_gain  # Convert the list to a boolean

        start_date = datetime(selected_year - 1, 12, 31)
        end_date = datetime(selected_year, 12, 31)
        date_range = [start_date, end_date]

        df_cash_account_type = transformation_manager.get_price_comparison_on_dates(date_range[0], date_range[1], True)

        total_value_start = df_cash_account_type.sum()[f"{date_range[0].date():%b-%y}"]
        total_value_end = df_cash_account_type.sum()[f"{date_range[1].date():%b-%y}"]
        total_spend = transformation_manager.get_flow_values(date_range[0], date_range[1], None, how="out", include_iat=False).Value.sum()

        salary = SalaryLegacy(
            transformation_manager,
            date_range[1].year,
            datetime(selected_year - 1, 1, 1),
            base_salary[selected_year],
            defaults.DEFAULT_PAYROLLS_1.copy(),
            defaults.BASE_PAYROLL_1,
            None,
            defaults.DEFAULT_PAYROLLS_2.copy(),
            defaults.BASE_PAYROLL_2,
            defaults.EXCLUDE_DEFAULT.copy(),
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

    #
    @app.callback(
        Output("tab2", "children"),
        [Input("year-dropdown", "value"), Input("category-dropdown", "value")],
    )
    def update_tab_2(selected_year, category):
        """Callback to update the 'Spending Detail' tab."""
        start_date = datetime(selected_year, 1, 1)
        end_date = datetime(selected_year, 12, 31)
        date_range = [start_date, end_date]
        how = "out"

        fig_spend_brkdn = figure_manager.get_figure_sunburst(date_range=date_range, how=how)
        total_spend = transformation_manager.get_flow_values(date_range[0], date_range[1], None, how=how, include_iat=False).Value.sum()

        category_key, category_value = category.split(": ")
        category_dict = {f"Full{category_key}": category_value}
        label = "MemoMapped"

        df_category_brkdn = figure_manager.get_category_breakdown(category_dict, label, 10, date_range, None, how=how)
        fig_category_brkdn = figure_manager.get_figure_bar(category_dict, label, None, date_range, how=how)

        return tabs.get_tab_2(total_spend, category_value, fig_category_brkdn, fig_spend_brkdn, df_category_brkdn)

    """
    @app.callback(Output("fig_category_brkdn", "figure"), Input("fig_spend_brkdn", "clickData"))
    def update_bar_chart(clickData):
        selected_year = 2024

        start_date = datetime(selected_year, 1, 1)
        end_date = datetime(selected_year, 12, 31)
        date_range = [start_date, end_date]

        if clickData:
            selected_category = clickData["points"][0]["id"]  # Get clicked category or subcategory
            if "/" in selected_category:
                selected_category = selected_category.split("/")[-1]
            full_categories = [c for c in categories if selected_category in c]
            if len(full_categories) == 0:
                raise ValueError(f"Failed to find full_category for {selected_category}.")
            elif len(full_categories) > 1:
                raise ValueError(f"Found more than 1 full_category for {selected_category}.")
            full_category = full_categories[0]
            full_category_key = full_category.split(":")[0].strip()
            full_category_value = full_category.split(":")[1].strip()
            category_dict = {full_category_key: full_category_value}
        else:
            return

        label = "MemoMapped"
        fig_category_brkdn = figure_manager.get_figure_bar(category_dict, label, None, date_range)
        return fig_category_brkdn
    """

    @app.callback(
        Output("tab3", "children"),
        [Input("year-dropdown", "value")],
    )
    def update_tab_3(selected_year):
        """Callback to update the 'Capital Gain Breakdown' tab"""
        start_date = datetime(selected_year, 1, 1)
        end_date = datetime(selected_year, 12, 31)
        date_range = [start_date, end_date]

        df_capital, fig_capital_default = figure_manager.get_capital_gain_brkdn(date_range=date_range)

        return tabs.get_tab_3(df_capital.reset_index(), fig_capital_default)
