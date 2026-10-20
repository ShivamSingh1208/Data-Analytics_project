import unittest
import pandas as pd


class TestETLValidation(unittest.TestCase):

    def test_date_key_matches_period_end_date(self):
        dates = pd.to_datetime(
            pd.Series(["2025-04-30"])
        )

        expected_key = pd.to_numeric(
            dates.dt.strftime("%Y%m%d"),
            errors="coerce",
        )

        actual_key = pd.Series([20250430])

        self.assertTrue(
            actual_key.equals(expected_key)
        )

    def test_date_key_mismatch_is_detected(self):
        dates = pd.to_datetime(
            pd.Series(["2025-04-30"])
        )

        expected_key = pd.to_numeric(
            dates.dt.strftime("%Y%m%d"),
            errors="coerce",
        )

        actual_key = pd.Series([20250429])

        mismatch = actual_key.ne(expected_key)

        self.assertTrue(bool(mismatch.iloc[0]))

    def test_negative_payroll_amount_is_detected(self):
        amounts = pd.Series([1000.0, -50.0, 0.0])

        negative = amounts.lt(0)

        self.assertEqual(
            int(negative.sum()),
            1,
        )

    def test_duplicate_identifiers_are_detected(self):
        identifiers = pd.Series(
            ["PI-001", "PI-002", "PI-001"]
        )

        duplicates = identifiers.duplicated(
            keep=False
        )

        self.assertEqual(
            int(duplicates.sum()),
            2,
        )

    def test_open_ended_valid_to_date(self):
        values = pd.Series(
            ["2025-01-01", "9999-12-31"]
        )

        values = values.replace(
            "9999-12-31",
            pd.NA,
        )

        self.assertTrue(
            pd.isna(values.iloc[1])
        )


if __name__ == "__main__":
    unittest.main()