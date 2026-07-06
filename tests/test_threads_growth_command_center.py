# Copyright (c) 2024-2026 ClearGlass Inc. All Rights Reserved.
# Proprietary and confidential. See LICENSE for terms.
import tempfile
import unittest
from pathlib import Path

from bots.threads_growth_command_center import CommandCenterPaths, KpiEntry, read_csv, run


class ThreadsGrowthCommandCenterTests(unittest.TestCase):
    def test_all_mode_builds_workspace_daily_assets_and_dashboard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            paths = CommandCenterPaths.from_root(Path(tmp_dir))

            outputs = run("all", paths, "ClearGlassInc", "AI security", KpiEntry())

            self.assertIn(paths.calendar_path, outputs)
            self.assertTrue(paths.calendar_path.exists())
            self.assertTrue(paths.kpi_path.exists())
            self.assertTrue(paths.engagement_path.exists())
            self.assertTrue(paths.dashboard_path.exists())
            self.assertTrue(paths.manifest_path.exists())
            self.assertGreaterEqual(len(list(paths.drafts.glob("*.txt"))), 1)
            self.assertIn("zero botting", paths.dashboard_path.read_text(encoding="utf-8").lower())

    def test_add_kpi_calculates_rates_and_preserves_backup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            paths = CommandCenterPaths.from_root(Path(tmp_dir))
            run("init", paths, "ClearGlassInc", "AI security", KpiEntry())

            run(
                "add-kpi",
                paths,
                "ClearGlassInc",
                "AI security",
                KpiEntry(
                    followers=100,
                    posts=3,
                    replies=40,
                    likes=80,
                    reposts=10,
                    impressions=1000,
                    profile_visits=25,
                    notes="Manual daily closeout",
                ),
            )

            rows = read_csv(paths.kpi_path)
            self.assertEqual(rows[-1]["followers"], "100")
            self.assertEqual(rows[-1]["engagement_rate"], "0.1300")
            self.assertEqual(rows[-1]["profile_visit_rate"], "0.0250")
            self.assertGreaterEqual(len(list(paths.backups.glob("*_ThreadsKPITracker.csv"))), 1)


if __name__ == "__main__":
    unittest.main()
