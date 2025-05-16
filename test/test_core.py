import unittest
from datetime import datetime
import app_initialisation, callbacks


class TestCore(unittest.TestCase):
    def test_initialize_managers(self):
        """Test the initialization of managers."""
        ref_currency = "USD"
        selected_year = 2024

        data_manager, market_manager, transformation_manager, figure_manager = app_initialisation.initialize_managers(ref_currency, selected_year)

        assert data_manager is not None, "DataManager should be initialized."
        assert market_manager is not None, "MarketManager should be initialized."
        assert transformation_manager is not None, "TransformationManager should be initialized."
        assert figure_manager is not None, "FigureManager should be initialized."

    def test_get_price_comparison_on_dates(self):
        """Test the initialization of managers."""
        ref_currency = "USD"
        selected_year = 2024

        _, _, transformation_manager, _ = app_initialisation.initialize_managers(ref_currency, selected_year)

        total_value_start_1, total_value_end_1 = self._get_total_values(selected_year, transformation_manager)

        assert isinstance(total_value_start_1, float), "total_value_start should be a float."
        assert isinstance(total_value_end_1, float), "total_value_end should be a float."

        total_value_start_2, total_value_end_2 = self._get_total_values(selected_year + 1, transformation_manager)

        assert total_value_start_1 != total_value_start_2, "total_value_start should be different in 2024 and 2025."
        assert total_value_end_1 != total_value_end_2, "total_value_end should be different in 2024 and 2025."
        assert total_value_end_1 == total_value_start_2, "total_value_start_2 and total_value_end_1 should be the same."

    def _get_total_values(self, selected_year, transformation_manager):
        start_date = datetime(selected_year - 1, 12, 31)
        end_date = datetime(selected_year, 12, 31)
        date_range = [start_date, end_date]

        df_cash_account_type = transformation_manager.get_price_comparison_on_dates(date_range[0], date_range[1], True)

        total_value_start = df_cash_account_type.sum()[f"{date_range[0].date():%b-%y}"]
        total_value_end = df_cash_account_type.sum()[f"{date_range[1].date():%b-%y}"]
        return total_value_start, total_value_end
