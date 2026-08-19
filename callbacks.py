# callbacks.py
from datetime import datetime
from dash import Input, Output, State, exceptions

from bkanalysis.salary import Salary, SalaryLegacy
from bkanalysis.managers import TransformationManager, FigureManager

from src import defaults
import tabs


HOW = "both"  # default value for how to get the spending data


def previous_month(year, month):
    """Returns the (year, month) pair of the month preceding the given one."""
    return (year - 1, 12) if month == 1 else (year, month - 1)


def get_value_dates(selected_year):
    """Snapshot dates used to measure wealth.

    The opening balance of a year is the close of 31-Dec of the *previous* year, so these are
    the two points a year-on-year change is measured between."""
    return [datetime(selected_year - 1, 12, 31), datetime(selected_year, 12, 31)]


def get_flow_range(selected_year):
    """Window used for anything flow- or capital-gain-based: 1-Jan to 31-Dec inclusive.

    Deliberately distinct from get_value_dates(): the filters downstream are inclusive at both
    ends, so reusing the 31-Dec-of-previous-year snapshot date here would count that day's
    transactions and price move in both the opening balance and the current year."""
    return [datetime(selected_year, 1, 1), datetime(selected_year, 12, 31)]


def get_categories_for_year(transformation_manager: TransformationManager, selected_year, threshold=None):
    """Category dropdown options for one year, as a plain list of strings.

    get_all_categories returns a Series whose index is meaningless here, and `x in series` tests the
    index rather than the values, so every caller wants a list."""
    threshold = defaults.THRESHOLD if threshold is None else threshold
    return list(transformation_manager.get_all_categories(get_flow_range(selected_year), threshold))


def reconcile_category(categories, current_category):
    """Category to keep selected once the option list has been rebuilt for a new year.

    The dropdown is clearable=False, so a value outside `options` is one the user can never
    re-select. Keep the current choice when it survives the year change, otherwise fall back to the
    configured default and finally to whatever the year does offer."""
    if current_category in categories:
        return current_category
    if defaults.DEFAULT_CATEGORY in categories:
        return defaults.DEFAULT_CATEGORY
    return categories[0] if categories else None


def resolve_row_index(view_row, derived_virtual_indices):
    """Map a DataTable view position back to the index of the underlying data row.

    derived_virtual_indices is the post-sort, post-filter ordering of the source rows. Dash only
    supplies it once sorting or filtering is enabled, so fall back to the view position."""
    if not derived_virtual_indices or view_row is None or view_row >= len(derived_virtual_indices):
        return view_row
    return derived_virtual_indices[view_row]


def register_callbacks(
    app,
    transformation_manager: TransformationManager,
    figure_manager: FigureManager,
    base_salary,
    categories_by_year=None,
):
    """registers the callbacks of the dash app, and returns them keyed by name for profiling/tests"""

    # Salary construction is expensive and the underlying data is immutable after
    # startup, so build it at most once per selected year.
    salary_cache = {}

    # Categories are derived from the same immutable data, and app.py has already paid for the
    # default year to render the initial layout, so seed the cache with what it computed.
    category_cache = dict(categories_by_year or {})

    @app.callback(
        Output("tab1", "children"),
        [Input("year-dropdown", "value"), Input("capital-gain-checkbox", "value")],
    )
    def update_tab_1(selected_year, include_capital_gain):
        """Callback to update the 'Wealth Breakdown' tab."""
        include_capital_gain = "include_capital_gain" in include_capital_gain  # Convert the list to a boolean
        value_dates = get_value_dates(selected_year)
        flow_range = get_flow_range(selected_year)

        df_cash_account_type = transformation_manager.get_price_comparison_on_dates(value_dates[0], value_dates[1], True)

        total_value_start = df_cash_account_type[f"{value_dates[0].date():%b-%y}"].sum()
        total_value_end = df_cash_account_type[f"{value_dates[1].date():%b-%y}"].sum()
        df_total_flow = transformation_manager.get_flow_values(flow_range[0], flow_range[1], None, how=HOW, include_iat=False)
        df_total_spend = df_total_flow[~df_total_flow.FullType.isin(defaults.INCOME_TYPES)]
        total_spend = df_total_spend.Value.sum()

        salary = prepare_salary(selected_year, flow_range)

        # These FullTypes are excluded from both total_spend and Received Salary above; sum them,
        # along with the Outstanding Salary, into a single card so no flow is invisible to the
        # reconciliation.
        other_income = (
            df_total_flow[df_total_flow.FullType.isin(["Capital Earnings", "Capital Gain", "Exceptional Income", "Tax"])].Value.sum()
            + salary.outstanding_salary
        )

        capital_pnl = transformation_manager.get_values_by_asset(flow_range, None).CapitalGain.sum()

        # IAT legs are excluded from every flow-based figure but still move the balances, so any
        # residual is precisely the amount by which the cards above cannot reconcile to each other.
        iat_imbalance, _ = transformation_manager.get_iat_imbalance(flow_range[0], flow_range[1])

        fig_spend_waterfall = figure_manager.get_figure_waterfall(flow_range, salary_override=salary, include_capital_gain=include_capital_gain)

        # the wealth chart is anchored on the opening balance so it lines up with the YoY card
        fig_wealth = figure_manager.get_figure_timeseries(value_dates)

        return tabs.get_tab_1(
            df_cash_account_type,
            total_value_end,
            total_value_start,
            salary,
            total_spend,
            capital_pnl,
            fig_spend_waterfall,
            fig_wealth,
            iat_imbalance,
            other_income,
        )

    def prepare_salary(selected_year, date_range):
        """Prepare the salary object for the selected year (cached per year)."""
        if selected_year not in salary_cache:
            salary_cache[selected_year] = build_salary(selected_year, date_range)
        return salary_cache[selected_year]

    def build_salary(selected_year, date_range):
        """Build the salary object for the selected year."""

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

    def prepare_categories(selected_year):
        """Category options for the selected year (cached per year)."""
        if selected_year not in category_cache:
            category_cache[selected_year] = get_categories_for_year(transformation_manager, selected_year)
        return category_cache[selected_year]

    @app.callback(
        [Output("category-dropdown", "options"), Output("category-dropdown", "value")],
        Input("year-dropdown", "value"),
        State("category-dropdown", "value"),
    )
    def update_category_options(selected_year, current_category):
        """Rebuild the category dropdown whenever the year changes.

        get_all_categories drops anything below THRESHOLD, so the material categories differ from
        year to year. Options built once for the default year would let the user pick a category
        with no data in the selected year (tab 2 renders empty) and hide ones that do have data."""
        categories = prepare_categories(selected_year)
        return [{"label": category, "value": category} for category in categories], reconcile_category(categories, current_category)

    @app.callback(
        Output("tab2", "children"),
        [Input("year-dropdown", "value"), Input("category-dropdown", "value")],
    )
    def update_tab_2(selected_year, category):
        """Callback to update the 'Spending Detail' tab."""
        flow_range = get_flow_range(selected_year)

        fig_spend_brkdn = figure_manager.get_figure_sunburst(
            flow_range,
            None,
            include_iat=False,
            how=HOW,
            exclude_types=defaults.INCOME_TYPES,
        )

        df_total_flow = transformation_manager.get_flow_values(flow_range[0], flow_range[1], None, how=HOW, include_iat=False)
        df_total_spend = df_total_flow[~df_total_flow.FullType.isin(defaults.INCOME_TYPES)]
        total_spend = df_total_spend.Value.sum()

        # Category names come from the data and may themselves contain ": ", so only the first
        # separator delimits the key.
        category_key, category_value = category.split(": ", 1)
        category_dict = {f"Full{category_key}": category_value}
        label = "MemoMapped"

        df_category_brkdn = figure_manager.get_category_breakdown(category_dict, label, 10, flow_range, None, how=HOW)
        fig_category_brkdn = figure_manager.get_figure_bar(category_dict, label, None, flow_range, how=HOW)

        return tabs.get_tab_2(total_spend, category_value, fig_category_brkdn, fig_spend_brkdn, df_category_brkdn)

    @app.callback(
        Output("tab3", "children"),
        [Input("year-dropdown", "value")],
    )
    def update_tab_3(selected_year):
        """Callback to update the 'Capital Gain Breakdown' tab"""
        flow_range = get_flow_range(selected_year)

        df_capital, fig_capital_default = figure_manager.get_capital_gain_brkdn(date_range=flow_range)

        return tabs.get_tab_3(df_capital.reset_index(), fig_capital_default)

    @app.callback(
        Output("capital_fig", "figure"),
        Input("capital_tbl", "active_cell"),  # fires on click
        State("capital_tbl", "derived_virtual_indices"),
        State("year-dropdown", "value"),
    )
    def update_capital(active_cell, derived_virtual_indices, selected_year):
        """Callback to re-plot the 'Capital Gain Breakdown' chart for the clicked asset."""
        if not active_cell:
            # no click yet -> do not change graph
            raise exceptions.PreventUpdate

        flow_range = get_flow_range(selected_year)
        # active_cell["row"] is a position in the rendered rows, while row_idx_to_plot indexes the
        # freshly computed frame in its original order. They only coincide while the table is
        # neither sorted nor filtered; derived_virtual_indices maps the view position back.
        row_idx = resolve_row_index(active_cell["row"], derived_virtual_indices)

        # re-build plot base on the new selected row
        fig = figure_manager.get_capital_gain_brkdn(date_range=flow_range, row_idx_to_plot=row_idx)[1]
        return fig

    @app.callback(
        Output("tab4", "children"),
        [Input("year-dropdown", "value")],
    )
    def update_tab_4(selected_year):
        """Callback to update the 'Saving Rate' tab"""
        flow_range = get_flow_range(selected_year)

        last_month_year, last_month = previous_month(selected_year, datetime.today().month)
        prev_month_year, prev_month = previous_month(last_month_year, last_month)

        saving_ratio_annual = figure_manager.get_saving_rate_gauge(
            figure_manager.get_saving_ratio(selected_year) * 100,
            figure_manager.get_saving_ratio(selected_year - 1) * 100,
            f"Saving Rate for Year {selected_year} (vs previous year)",
        )
        saving_ratio_monthly = figure_manager.get_saving_rate_gauge(
            figure_manager.get_saving_ratio(last_month_year, last_month) * 100,
            figure_manager.get_saving_ratio(prev_month_year, prev_month) * 100,
            f"Saving Rate for Month {last_month_year}-{last_month:02d} (vs previous month)",
        )

        income_vs_expenses = figure_manager.get_income_vs_expenses(flow_range, True, True)

        return tabs.get_tab_4(income_vs_expenses, saving_ratio_annual, saving_ratio_monthly)

    return {
        "update_tab_1": update_tab_1,
        "update_tab_2": update_tab_2,
        "update_tab_3": update_tab_3,
        "update_tab_4": update_tab_4,
        "update_capital": update_capital,
        "update_category_options": update_category_options,
    }
