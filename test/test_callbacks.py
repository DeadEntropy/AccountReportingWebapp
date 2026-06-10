import unittest

from callbacks import previous_month


class TestCallbacks(unittest.TestCase):
    def test_previous_month_wraps_to_previous_december(self):
        """January must wrap to December of the previous year (month 0 caused empty saving-rate data)."""
        self.assertEqual(previous_month(2026, 1), (2025, 12))
        self.assertEqual(previous_month(2026, 6), (2026, 5))
