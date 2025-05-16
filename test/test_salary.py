import unittest
from datetime import datetime
from bkanalysis.salary import Salary, SalaryLegacy
import app_initialisation
from src import defaults

BASE_SALARY = {**{y: None for y in defaults.YEARS}, **{2024: defaults.BASE_SALARY_1}}


class TestSalary(unittest.TestCase):
    def test_salary_legacy(self):
        """Test the Legacy Salary class."""
        ref_currency = "USD"
        selected_year = 2024

        _, _, transformation_manager, _ = app_initialisation.initialize_managers(ref_currency, selected_year)

        start_date = datetime(selected_year - 1, 12, 31)
        end_date = datetime(selected_year, 12, 31)
        date_range = [start_date, end_date]

        salary = SalaryLegacy(
            transformation_manager,
            date_range[1].year,
            datetime(selected_year - 1, 1, 1),
            BASE_SALARY[selected_year],
            defaults.DEFAULT_PAYROLLS_1.copy(),
            defaults.BASE_PAYROLL_1,
            None,
            defaults.DEFAULT_PAYROLLS_2.copy(),
            defaults.BASE_PAYROLL_2,
            defaults.EXCLUDE_DEFAULT.copy(),
        )

        assert salary.actual_salaries is not None, "actual_salaries should be initialized."
        assert isinstance(salary.actual_salary, float), "actual_salary should be a float."
        self.assertAlmostEqual(salary.actual_salary, sum(salary.actual_salaries.values()), delta=0.01, msg="actual_salary should be equal to the sum of actual_salaries.")

        assert salary.monthly_salaries is not None, "monthly_salaries should be initialized."

        assert salary.outstanding_salaries is not None, "outstanding_salaries should be initialized."
        assert isinstance(salary.outstanding_salary, float), "outstanding_salary should be a float."
        self.assertAlmostEqual(
            salary.outstanding_salary, sum(salary.outstanding_salaries.values()), delta=0.01, msg="outstanding_salary should be equal to the sum of outstanding_salaries."
        )

        assert salary.total_received_salaries is not None, "total_received_salaries should be initialized."
        assert isinstance(salary.total_received_salary, float), "total_received_salary should be a float."
        self.assertAlmostEqual(
            salary.total_received_salary,
            sum(salary.total_received_salaries.values()),
            delta=0.01,
            msg="total_received_salary should be equal to the sum of total_received_salaries.",
        )

        assert salary.total_received_salaries_from_previous_year is not None, "total_received_salaries_from_previous_year should be initialized."
        assert isinstance(salary.total_received_salary_from_previous_year, float), "total_received_salary_from_previous_year should be a float."
        self.assertAlmostEqual(
            salary.total_received_salary_from_previous_year,
            sum(salary.total_received_salaries_from_previous_year.values()),
            delta=0.01,
            msg="total_received_salary_from_previous_year should be equal to the sum of total_received_salaries_from_previous_year.",
        )

        assert isinstance(salary.payrolls, list), "payrolls should be a list."

        self.assertEqual(salary.anchor_date, datetime(selected_year - 1, 1, 1), msg="anchor_date should be equal to the provided date.")
        self.assertAlmostEqual(salary.actual_salary, 348441.45, delta=0.01, msg="actual_salary should be equal to the expected value.")
        self.assertAlmostEqual(salary.outstanding_salary, 61532.03, delta=0.01, msg="outstanding_salary should be equal to the expected value.")
        self.assertAlmostEqual(salary.total_received_salary, 375605.65, delta=0.01, msg="total_received_salary should be equal to the expected value.")
        self.assertAlmostEqual(
            salary.total_received_salary_from_previous_year, 27164.20, delta=0.01, msg="total_received_salary_from_previous_year should be equal to the expected value."
        )

    def test_salary(self):
        """Test the Salary class."""
        ref_currency = "USD"
        selected_year = 2024

        _, _, transformation_manager, _ = app_initialisation.initialize_managers(ref_currency, selected_year)

        start_date = datetime(selected_year - 1, 12, 31)
        end_date = datetime(selected_year, 12, 31)
        date_range = [start_date, end_date]

        salary_config = {
            "NAYA_CYTOVIA": {
                "base_salary": 13250,
                "payrolls": [
                    "NAYA BIOSCIENCES PAYROLL",
                    "CYTOVIA THERAPEUTICS",
                    "NAYA ONCOLOGY",
                    "TRINET HR CORPORATE PAYROLL",
                ],
            },
            "UBS": {
                "base_salary": None,
                "payrolls": ["UBS SALARY", "UBS BONUS"],
            },
        }

        salary = Salary(
            transformation_manager,
            date_range[1].year,
            datetime(selected_year - 1, 1, 1),
            salary_config,
            defaults.EXCLUDE_DEFAULT.copy(),
        )

        assert salary.actual_salaries is not None, "actual_salaries should be initialized."
        assert isinstance(salary.actual_salary, float), "actual_salary should be a float."
        self.assertAlmostEqual(salary.actual_salary, sum(salary.actual_salaries.values()), delta=0.01, msg="actual_salary should be equal to the sum of actual_salaries.")

        assert salary.monthly_salaries is not None, "monthly_salaries should be initialized."

        assert salary.outstanding_salaries is not None, "outstanding_salaries should be initialized."
        assert isinstance(salary.outstanding_salary, float), "outstanding_salary should be a float."
        self.assertAlmostEqual(
            salary.outstanding_salary, sum(salary.outstanding_salaries.values()), delta=0.01, msg="outstanding_salary should be equal to the sum of outstanding_salaries."
        )

        assert salary.total_received_salaries is not None, "total_received_salaries should be initialized."
        assert isinstance(salary.total_received_salary, float), "total_received_salary should be a float."
        self.assertAlmostEqual(
            salary.total_received_salary,
            sum(salary.total_received_salaries.values()),
            delta=0.01,
            msg="total_received_salary should be equal to the sum of total_received_salaries.",
        )

        assert salary.total_received_salaries_from_previous_year is not None, "total_received_salaries_from_previous_year should be initialized."
        assert isinstance(salary.total_received_salary_from_previous_year, float), "total_received_salary_from_previous_year should be a float."
        self.assertAlmostEqual(
            salary.total_received_salary_from_previous_year,
            sum(salary.total_received_salaries_from_previous_year.values()),
            delta=0.01,
            msg="total_received_salary_from_previous_year should be equal to the sum of total_received_salaries_from_previous_year.",
        )

        assert isinstance(salary.payrolls, list), "payrolls should be a list."

        self.assertEqual(salary.anchor_date, datetime(selected_year - 1, 1, 1), msg="anchor_date should be equal to the provided date.")
        self.assertAlmostEqual(salary.actual_salary, 348441.45, delta=0.01, msg="actual_salary should be equal to the expected value.")
        self.assertAlmostEqual(salary.outstanding_salary, 61532.03, delta=0.01, msg="outstanding_salary should be equal to the expected value.")
        self.assertAlmostEqual(salary.total_received_salary, 375605.65, delta=0.01, msg="total_received_salary should be equal to the expected value.")
        self.assertAlmostEqual(
            salary.total_received_salary_from_previous_year, 27164.20, delta=0.01, msg="total_received_salary_from_previous_year should be equal to the expected value."
        )
