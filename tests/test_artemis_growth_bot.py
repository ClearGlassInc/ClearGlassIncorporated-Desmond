import tempfile
import unittest
from pathlib import Path

from bots import artemis_growth_bot


class ArtemisGrowthBotTests(unittest.TestCase):
    def test_write_outputs_creates_site_and_archive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            output_dir = root / "marketing" / "output"
            archive_dir = output_dir / "threads_archive"
            site_page = root / "threads.html"

            original_root = artemis_growth_bot.ROOT
            original_output = artemis_growth_bot.OUTPUT_DIR
            original_archive = artemis_growth_bot.THREADS_ARCHIVE_DIR
            original_site = artemis_growth_bot.SITE_PAGE
            original_json = artemis_growth_bot.THREADS_JSON
            original_md = artemis_growth_bot.THREADS_MD

            try:
                artemis_growth_bot.ROOT = root
                artemis_growth_bot.OUTPUT_DIR = output_dir
                artemis_growth_bot.THREADS_ARCHIVE_DIR = archive_dir
                artemis_growth_bot.SITE_PAGE = site_page
                artemis_growth_bot.THREADS_JSON = output_dir / "threads_latest.json"
                artemis_growth_bot.THREADS_MD = output_dir / "threads_latest.md"

                run = artemis_growth_bot.write_outputs("ClearGlassInc Artemis")

                self.assertEqual(run.total_threads, 5)
                self.assertTrue(site_page.exists())
                self.assertTrue((output_dir / "threads_latest.md").exists())
                self.assertTrue((output_dir / "threads_latest.json").exists())
                archive_files = list(archive_dir.glob("*.md"))
                self.assertEqual(len(archive_files), 1)
            finally:
                artemis_growth_bot.ROOT = original_root
                artemis_growth_bot.OUTPUT_DIR = original_output
                artemis_growth_bot.THREADS_ARCHIVE_DIR = original_archive
                artemis_growth_bot.SITE_PAGE = original_site
                artemis_growth_bot.THREADS_JSON = original_json
                artemis_growth_bot.THREADS_MD = original_md


if __name__ == "__main__":
    unittest.main()
