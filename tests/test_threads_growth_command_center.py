from pathlib import Path

SCRIPT = Path("ThreadsGrowthCommandCenter.ps1")


def test_threads_script_is_v3_manual_and_compliant():
    text = SCRIPT.read_text(encoding="utf-8")
    lowered = text.lower()
    assert "threads growth command center v3" in lowered
    assert "aggressive execution model" in lowered
    assert "zero botting. zero scraping." in lowered
    assert "manual-only" in lowered
    assert "auto-posts" in lowered
    assert "mass-dms" in lowered or "mass dms" in lowered
    assert "credential" in lowered


def test_threads_script_supports_modes_and_kpi_entry():
    text = SCRIPT.read_text(encoding="utf-8")
    assert '[ValidateSet("Init", "Daily", "AddKPI", "Dashboard", "All")]' in text
    assert 'function Add-KpiEntry' in text
    for metric in ["Followers", "Posts", "Replies", "Likes", "Reposts", "Impressions", "ProfileVisits", "Notes"]:
        assert metric in text
    assert 'Backup-FileSafe -Path $KpiPath' in text


def test_threads_script_creates_v3_command_center_assets():
    text = SCRIPT.read_text(encoding="utf-8")
    for folder in ["Drafts", "Calendars", "Analytics", "Engagement", "DailyPlans", "Reports", "Backups"]:
        assert folder in text
    for filename in [
        "ContentCalendar.csv",
        "ThreadsKPITracker.csv",
        "EngagementTracker.csv",
        "FormatReview.csv",
        "ThreadsGrowthDashboard.html",
    ]:
        assert filename in text
    assert "$i -lt 30" in text
    assert "40 REPLIES MINIMUM" in text


def test_threads_script_has_format_pruning_and_dashboard_tables():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "If a format fails twice, kill it." in text
    assert "function Convert-RowsToHtmlTable" in text
    assert "Upcoming Firepower" in text
    assert "Telemetry Logs" in text
    assert "Format Kill List" in text
