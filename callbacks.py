# callbacks.py
from datetime import datetime
from dash import Input, Output, State, exceptions

from bkanalysis.salary import Salary, SalaryLegacy
from bkanalysis.managers import TransformationManager, TransformationManagerCache, FigureManager

from src import defaults
import tabs


def register_callbacks(app, transformation_manager: TransformationManager | TransformationManagerCache, figure_manager: FigureManager, base_salary, categories):
    """registers the callbacks of the dash app"""

    HOW = "out"  # default value for how to get the spending data

    @staticmethod
    def get_date_range(selected_year):
        """Helper function to get the date range for the selected year."""
        start_date = datetime(selected_year - 1, 12, 31)
        end_date = datetime(selected_year, 12, 31)
        return [start_date, end_date]

    @app.callback(
        Output("tab1", "children"),
        [Input("year-dropdown", "value"), Input("capital-gain-checkbox", "value")],
    )
    def update_tab_1(selected_year, include_capital_gain):
        """Callback to update the 'Wealth Breakdown' tab."""
        include_capital_gain = "include_capital_gain" in include_capital_gain  # Convert the list to a boolean
        date_range = get_date_range(selected_year)

        df_cash_account_type = transformation_manager.get_price_comparison_on_dates(date_range[0], date_range[1], True)

        total_value_start = df_cash_account_type.sum()[f"{date_range[0].date():%b-%y}"]
        total_value_end = df_cash_account_type.sum()[f"{date_range[1].date():%b-%y}"]
        total_spend = transformation_manager.get_flow_values(date_range[0], date_range[1], None, how=HOW, include_iat=False).Value.sum()

        salary = prepare_salary(selected_year, date_range)

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

    def prepare_salary(selected_year, date_range):
        """Prepare the salary object for the selected year."""

        if defaults.USE_LEGACY_SALARY_CLASS:
            return SalaryLegacy(
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

        return Salary(
            transformation_manager,
            date_range[1].year,
            datetime(selected_year - 1, 1, 1),
            defaults.SALARY_CONFIG,
            defaults.EXCLUDE_DEFAULT.copy(),
        )

    @app.callback(
        Output("tab2", "children"),
        [Input("year-dropdown", "value"), Input("category-dropdown", "value")],
    )
    def update_tab_2(selected_year, category):
        """Callback to update the 'Spending Detail' tab."""
        date_range = get_date_range(selected_year)

        fig_spend_brkdn = figure_manager.get_figure_sunburst(
            date_range,
            None,
            include_iat=False,
            how=HOW,
        )
        total_spend = transformation_manager.get_flow_values(date_range[0], date_range[1], None, how=HOW, include_iat=False).Value.sum()

        category_key, category_value = category.split(": ")
        category_dict = {f"Full{category_key}": category_value}
        label = "MemoMapped"

        df_category_brkdn = figure_manager.get_category_breakdown(category_dict, label, 10, date_range, None, how=HOW)
        fig_category_brkdn = figure_manager.get_figure_bar(category_dict, label, None, date_range, how=HOW)

        return tabs.get_tab_2(total_spend, category_value, fig_category_brkdn, fig_spend_brkdn, df_category_brkdn)

    @app.callback(
        Output("tab3", "children"),
        [Input("year-dropdown", "value")],
    )
    def update_tab_3(selected_year):
        """Callback to update the 'Capital Gain Breakdown' tab"""
        date_range = get_date_range(selected_year)

        df_capital, fig_capital_default = figure_manager.get_capital_gain_brkdn(date_range=date_range)

        return tabs.get_tab_3(df_capital.reset_index(), fig_capital_default)

    @app.callback(
        Output("capital_fig", "figure"),
        Input("capital_tbl", "active_cell"),  # fires on click
        State("year-dropdown", "value"),
    )
    def update_capital(active_cell, selected_year):
        if not active_cell:
            # no click yet → don’t change graph
            raise exceptions.PreventUpdate

        date_range = get_date_range(selected_year)
        row_idx = active_cell["row"]

        # re-build plot base on the new selected row
        fig = figure_manager.get_capital_gain_brkdn(date_range=date_range, row_idx_to_plot=row_idx)[1]
        return fig

    @app.callback(
        Output("tab4", "children"),
        [Input("year-dropdown", "value")],
    )
    def update_tab_4(selected_year):
        """Callback to update the 'Capital Gain Breakdown' tab"""
        date_range = get_date_range(selected_year)

        saving_ratio_annual = figure_manager.get_saving_rate_gauge(
            figure_manager.get_saving_ratio(selected_year) * 100,
            figure_manager.get_saving_ratio(selected_year - 1) * 100,
            f"Saving Rate for Year {selected_year} (vs previous year)",
        )
        saving_ratio_monthly = figure_manager.get_saving_rate_gauge(
            figure_manager.get_saving_ratio(selected_year, datetime.today().month - 1) * 100,
            figure_manager.get_saving_ratio(selected_year, datetime.today().month - 2) * 100,
            f"Saving Rate for Month {selected_year}-{datetime.today().month - 1} (vs previous month)",
        )

        income_vs_expenses = figure_manager.get_income_vs_expenses(date_range, True, True)

        return tabs.get_tab_4(income_vs_expenses, saving_ratio_annual, saving_ratio_monthly)
