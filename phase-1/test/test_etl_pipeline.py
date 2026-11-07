import unittest
import pandas as pd
import tempfile
from pathlib import Path
from unittest.mock import patch
import sys

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "src"),
)

import etl_pipeline


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


    def test_reversed_leave_dates_are_detected(self):
        leave = pd.DataFrame({
            "start_date": ["2026-02-20", "2026-02-18"],
            "end_date": ["2026-02-19", "2026-02-20"],
        })

        start_date = pd.to_datetime(
            leave["start_date"],
            errors="coerce",
        )
        end_date = pd.to_datetime(
            leave["end_date"],
            errors="coerce",
        )

        reversed_dates = (
            start_date.notna()
            & end_date.notna()
            & start_date.gt(end_date)
        )

        self.assertEqual(
            int(reversed_dates.sum()),
            1,
        )
        self.assertTrue(bool(reversed_dates.iloc[0]))
        self.assertFalse(bool(reversed_dates.iloc[1]))

    def test_clean_table_rejects_reversed_leave_dates(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            data_dir = root / "data"
            output_dir = root / "cleaned"
            rejected_dir = root / "rejected"
            logs_dir = root / "logs"

            for folder in [
                data_dir,
                output_dir,
                rejected_dir,
                logs_dir,
            ]:
                folder.mkdir(parents=True, exist_ok=True)

            source_file = (
                data_dir / "sample_fact_leave.csv"
            )

            pd.DataFrame({
                "leave_request_id": ["LR-TEST-1", "LR-TEST-2"],
                "employee_id": ["EMP-1", "EMP-2"],
                "start_date": ["2026-02-20", "2026-02-18"],
                "end_date": ["2026-02-19", "2026-02-20"],
                "status": ["Rejected", "Approved"],
            }).to_csv(source_file, index=False)

            with (
                patch.object(etl_pipeline, "PROJECT", root),
                patch.object(etl_pipeline, "DATA_FOLDER", data_dir),
                patch.object(etl_pipeline, "OUTPUT", output_dir),
                patch.object(etl_pipeline, "REJECTED", rejected_dir),
                patch.object(etl_pipeline, "LOGS", logs_dir),
            ):
                result = etl_pipeline.clean_table(
                    "fact_leave",
                    {
                        "required": ["employee_id"],
                        "id": None,
                        "dates": [],
                        "money": [],
                    },
                )

            rejected = pd.read_csv(
                rejected_dir / "rejected_fact_leave.csv"
            )
            clean = pd.read_csv(
                output_dir / "cleaned_fact_leave.csv"
            )

            self.assertEqual(result["input_rows"], 2)
            self.assertEqual(result["clean_rows"], 1)
            self.assertEqual(result["rejected_rows"], 1)
            self.assertEqual(
                rejected.iloc[0]["leave_request_id"],
                "LR-TEST-1",
            )
            self.assertEqual(
                rejected.iloc[0]["reject_reason"],
                "start_date is after end_date",
            )
            self.assertEqual(
                clean.iloc[0]["leave_request_id"],
                "LR-TEST-2",
            )

if __name__ == "__main__":
    unittest.main()
