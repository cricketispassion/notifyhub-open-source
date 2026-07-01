from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.worker.main import load_config, run_workflow, run_birthdays_workflow, load_birthdays, birthdays_for_date, parse_birthday
from services.worker.main import should_run_now, resolve_driver_class


def test_run_workflow_returns_ready_summary():
    config_path = ROOT / "config" / "config.yml"
    config = load_config(config_path)

    summary = run_workflow(config, plugins=["birthday"])

    assert summary["timezone"] == "Asia/Kolkata"
    assert summary["send_time"] == "20:42"
    assert summary["plugins"] == ["birthday"]
    assert summary["status"] == "ready"


def test_run_workflow_can_send_via_whatsapp_driver():
    config_path = ROOT / "config" / "config.yml"
    config = load_config(config_path)

    summary = run_workflow(
        config,
        plugins=["birthday"],
        driver_config={"type": "whatsapp-playwright", "dry_run": True},
        recipient="demo-user",
    )

    assert summary["driver"]["status"] == "simulated"
    assert summary["driver"]["recipient"] == "demo-user"


def test_run_workflow_uses_configured_recipient_and_message():
    config_path = ROOT / "config" / "config.yml"
    config = load_config(config_path)

    summary = run_workflow(config)

    assert summary["driver"]["recipient"] == config["recipient"]
    assert summary["message"] == config["message"]


def test_should_run_now_matches_send_time():
    assert should_run_now("09:00", "UTC", datetime(2026, 6, 30, 9, 0, tzinfo=ZoneInfo("UTC"))) is True
    assert should_run_now("09:00", "UTC", datetime(2026, 6, 30, 9, 1, tzinfo=ZoneInfo("UTC"))) is False


def test_should_run_now_respects_timezone():
    assert should_run_now("09:00", "Asia/Kolkata", datetime(2026, 6, 30, 3, 30, tzinfo=ZoneInfo("UTC"))) is True


def test_resolve_driver_class_prefers_desktop_driver():
    driver_class = resolve_driver_class("whatsapp-desktop")
    assert driver_class.__name__ == "WhatsAppDesktopDriver"

def test_run_workflow_can_use_desktop_driver_in_dry_run_mode():
    summary = run_workflow(
        {"recipient": "demo-user", "message": "Hello"},
        driver_config={"type": "whatsapp-desktop", "dry_run": True},
    )

    assert summary["driver"]["type"] == "whatsapp-desktop"
    assert summary["driver"]["status"] == "simulated"


def test_load_birthdays_reads_csv_rows(tmp_path):
    data_file = tmp_path / "birthdays.csv"
    data_file.write_text("name,recipient,birthday,message\nAlice,alice,06-30,Happy Birthday!\n")

    rows = load_birthdays(data_file)

    assert len(rows) == 1
    assert rows[0]["name"] == "Alice"
    assert rows[0]["recipient"] == "alice"


def test_birthdays_for_date_picks_today():
    rows = [
        {"name": "Alice", "recipient": "alice", "birthday": "06-30", "message": "Happy Birthday!"},
        {"name": "Bob", "recipient": "bob", "birthday": "07-01", "message": "Hi Bob"},
    ]

    matches = birthdays_for_date(rows, today=date(2026, 6, 30))

    assert len(matches) == 1
    assert matches[0]["name"] == "Alice"


def test_parse_birthday_supports_month_day_formats():
    assert parse_birthday("06-30") == date(1900, 6, 30)
    assert parse_birthday("06/30") == date(1900, 6, 30)
    assert parse_birthday("30.06") == date(1900, 6, 30)


def test_run_birthdays_workflow_returns_matches(tmp_path):
    data_file = tmp_path / "birthdays.csv"
    data_file.write_text("name,recipient,birthday,message\nAlice,alice,06-30,Happy Birthday!\n")

    config_path = ROOT / "config" / "config.yml"
    config = load_config(config_path)
    summary = run_birthdays_workflow(
        config,
        birthday_path=str(data_file),
        driver_config={"type": "whatsapp-playwright", "dry_run": True},
        today=date(2026, 6, 30),
    )

    assert summary["birthday_count"] == 1
    assert summary["status"] == "partial_failure"
    assert summary["results"][0]["recipient"] == "alice"
