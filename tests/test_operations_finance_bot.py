import tempfile
import unittest
from pathlib import Path

from bots import operations_finance_bot


class OperationsFinanceBotTests(unittest.TestCase):
    def test_calculate_outputs_returns_positive_recommended_fee(self) -> None:
        inputs = operations_finance_bot.load_inputs()
        outputs = operations_finance_bot.calculate_outputs(inputs)

        self.assertGreater(outputs.recommended_monthly_fee, outputs.min_monthly_fee)
        self.assertGreater(outputs.inventory_cost_total_month, 0)
        self.assertGreaterEqual(outputs.gross_margin_after_inventory, 0)

    def test_write_outputs_creates_archive_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            output_dir = root / "operations" / "output"
            archive_dir = output_dir / "archive"

            original_root = operations_finance_bot.ROOT
            original_output = operations_finance_bot.OUTPUT_DIR
            original_archive = operations_finance_bot.ARCHIVE_DIR
            try:
                operations_finance_bot.ROOT = root
                operations_finance_bot.OUTPUT_DIR = output_dir
                operations_finance_bot.ARCHIVE_DIR = archive_dir

                inputs = operations_finance_bot.load_inputs()
                outputs = operations_finance_bot.calculate_outputs(inputs)

                operations_finance_bot.write_outputs(inputs, outputs)
                expected = archive_dir / f"{outputs.run_utc.replace('+00:00', 'Z').replace(':', '')}.md"
                self.assertTrue(expected.exists())
                self.assertTrue((output_dir / "latest.md").exists())
                self.assertTrue((output_dir / "latest.json").exists())
            finally:
                operations_finance_bot.ROOT = original_root
                operations_finance_bot.OUTPUT_DIR = original_output
                operations_finance_bot.ARCHIVE_DIR = original_archive


if __name__ == "__main__":
    unittest.main()
