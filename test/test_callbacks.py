import unittest
from datetime import datetime

from callbacks import get_flow_range, get_value_dates, previous_month, reconcile_category, resolve_row_index
from src import defaults


class TestCallbacks(unittest.TestCase):
    def test_previous_month_wraps_to_previous_december(self):
        """January must wrap to December of the previous year (month 0 caused empty saving-rate data)."""
        self.assertEqual(previous_month(2026, 1), (2025, 12))
        self.assertEqual(previous_month(2026, 6), (2026, 5))

    def test_date_helpers_are_importable_and_distinct(self):
        """The flow window must not reach back into the previous year's closing snapshot."""
        self.assertEqual(get_value_dates(2026), [datetime(2025, 12, 31), datetime(2026, 12, 31)])
        self.assertEqual(get_flow_range(2026), [datetime(2026, 1, 1), datetime(2026, 12, 31)])


class TestReconcileCategory(unittest.TestCase):
    """The category dropdown is clearable=False, so a value outside `options` is unrecoverable."""

    def test_keeps_current_category_when_still_available(self):
        categories = ["SubType: Grocery", "Type: Travel"]
        self.assertEqual(reconcile_category(categories, "Type: Travel"), "Type: Travel")

    def test_falls_back_to_default_when_current_dropped_by_threshold(self):
        categories = ["SubType: Grocery", "Type: Travel"]
        self.assertEqual(reconcile_category(categories, "SubType: Vanished"), defaults.DEFAULT_CATEGORY)

    def test_falls_back_to_first_option_when_default_absent(self):
        categories = ["Type: Travel", "MasterType: Housing"]
        self.assertEqual(reconcile_category(categories, "SubType: Vanished"), "Type: Travel")

    def test_returns_none_when_the_year_offers_nothing(self):
        self.assertIsNone(reconcile_category([], "SubType: Grocery"))


class TestResolveRowIndex(unittest.TestCase):
    """active_cell["row"] is a view position; row_idx_to_plot indexes the unsorted source frame."""

    def test_maps_view_position_through_sorted_order(self):
        self.assertEqual(resolve_row_index(0, [3, 1, 2, 0]), 3)
        self.assertEqual(resolve_row_index(2, [3, 1, 2, 0]), 2)

    def test_falls_back_when_dash_supplies_no_indices(self):
        """Dash only populates derived_virtual_indices once sorting or filtering is enabled."""
        self.assertEqual(resolve_row_index(2, None), 2)
        self.assertEqual(resolve_row_index(2, []), 2)

    def test_falls_back_when_view_row_is_out_of_range(self):
        self.assertEqual(resolve_row_index(5, [3, 1, 2, 0]), 5)


class TestDefaults(unittest.TestCase):
    def test_year_dropdown_always_offers_the_current_year(self):
        """DEFAULT_YEAR is datetime.today().year, and the year dropdown is clearable=False."""
        self.assertIn(datetime.today().year, defaults.YEARS)
