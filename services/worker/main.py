from __future__ import annotations

import argparse
import csv
import importlib.util
from datetime import date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


DEFAULT_PLUGIN = "birthday"
ROOT = Path(__file__).resolve().parents[2]


def _load_desktop_driver_class() -> type[Any]:
    module_path = ROOT / "drivers" / "whatsapp-playwright" / "desktop_driver.py"
    spec = importlib.util.spec_from_file_location("notifyhub_desktop_driver", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load desktop WhatsApp driver from {module_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.WhatsAppDesktopDriver


WhatsAppDesktopDriver = _load_desktop_driver_class()

import yaml




def _load_whatsapp_driver_class() -> type[Any]:
    module_path = ROOT / "drivers" / "whatsapp-playwright" / "driver.py"
    spec = importlib.util.spec_from_file_location("notifyhub_whatsapp_driver", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load WhatsApp driver from {module_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.WhatsAppPlaywrightDriver


WhatsAppPlaywrightDriver = _load_whatsapp_driver_class()


def parse_birthday(value: str | None) -> date | None:
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def load_birthdays(path: str | Path | None = None) -> list[dict[str, str]]:
    birthday_path = Path(path or ROOT / "data" / "birthdays.csv")
    if not birthday_path.exists():
        return []

    with birthday_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [row for row in reader if row.get("recipient") or row.get("name")]


def birthdays_for_date(rows: list[dict[str, str]], today: date | None = None) -> list[dict[str, str]]:
    today = today or date.today()
    results: list[dict[str, str]] = []
    for row in rows:
        birthday = parse_birthday(row.get("birthday"))
        if birthday is None:
            continue
        if birthday.month == today.month and birthday.day == today.day:
            results.append(row)
    return results


def _send_birthdays(
    config: dict[str, Any],
    birthdays: list[dict[str, str]],
    driver_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    driver_config = driver_config or {"type": "whatsapp-playwright", "dry_run": True}
    driver_type = driver_config.get("type", "whatsapp-playwright")
    driver_class = resolve_driver_class(driver_type)
    matched = birthdays_for_date(birthdays)

    results: list[dict[str, Any]] = []
    for row in matched:
        recipient = row.get("recipient") or row.get("name") or "unknown"
        message = row.get("message") or str(config.get("message", "Happy birthday!"))
        if driver_class is not None:
            driver = driver_class()
            driver_result = driver.send_message(recipient, message, dry_run=driver_config.get("dry_run", True))
        else:
            driver_result = {"status": "skipped", "detail": "No driver configured", "recipient": recipient}
        results.append({"recipient": recipient, "message": message, **driver_result})

    overall_status = "no_birthdays_today"
    if matched:
        overall_status = "success" if any(r.get("status") == "sent" for r in results) else "partial_failure"

    return {
        "status": overall_status,
        "timezone": config.get("timezone", "UTC"),
        "send_time": config.get("send_time", "09:00"),
        "birthday_count": len(matched),
        "results": results,
    }


def run_birthdays_workflow(
    config: dict[str, Any],
    birthday_path: str | Path | None = None,
    driver_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    birthdays = load_birthdays(birthday_path)
    return _send_birthdays(config, birthdays=birthdays, driver_config=driver_config)


def resolve_driver_class(driver_type: str | None = None) -> type[Any]:
    if driver_type == "whatsapp-desktop":
        return WhatsAppDesktopDriver
    return WhatsAppPlaywrightDriver


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    config_path = Path(path or ROOT / "config" / "config.yml")
    with config_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def should_run_now(send_time: str, timezone: str = "UTC", current_time: datetime | None = None) -> bool:
    tz = ZoneInfo(timezone or "UTC")
    now = current_time or datetime.now(tz)
    if now.tzinfo is None:
        now = now.replace(tzinfo=tz)
    else:
        now = now.astimezone(tz)
    return now.strftime("%H:%M") == send_time


def run_workflow(
    config: dict[str, Any],
    plugins: list[str] | None = None,
    driver_config: dict[str, Any] | None = None,
    recipient: str | None = None,
) -> dict[str, Any]:
    plugin_names = plugins or ["birthday"]
    driver_config = driver_config or {"type": "whatsapp-playwright", "dry_run": True}
    recipient_name = recipient or str(config.get("recipient", "unknown"))
    message = str(config.get("message", "Happy birthday!"))

    driver_type = driver_config.get("type", "whatsapp-playwright")
    driver_class = resolve_driver_class(driver_type)
    if driver_class is not None:
        driver = driver_class()
        if driver_config.get("dry_run"):
            driver_result = driver.send_message(recipient_name, message, dry_run=True)
            driver_status = driver_result["status"]
        else:
            driver_result = driver.send_message(recipient_name, message, dry_run=False)
            driver_status = driver_result["status"]
    else:
        driver_result = {"status": "skipped", "detail": "No driver configured"}
        driver_status = driver_result["status"]

    return {
        "status": "ready",
        "timezone": config.get("timezone", "UTC"),
        "send_time": config.get("send_time", "09:00"),
        "plugins": plugin_names,
        "message": message,
        "driver": {
            "type": driver_config.get("type", "whatsapp-playwright"),
            "status": driver_status,
            "recipient": recipient_name,
            "detail": driver_result.get("detail"),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run NotifyHub worker workflow")
    parser.add_argument("--config", default=str(ROOT / "config" / "config.yml"))
    parser.add_argument("--plugin", action="append", default=None)
    parser.add_argument("--recipient", default=None)
    parser.add_argument("--message", default=None)
    parser.add_argument("--schedule", action="store_true", help="Run only if current time matches send_time")
    parser.add_argument("--live", action="store_true", help="Attempt a real WhatsApp send instead of dry run")
    parser.add_argument("--driver", default="whatsapp-playwright", choices=["whatsapp-playwright", "whatsapp-desktop"], help="Choose the WhatsApp driver")
    parser.add_argument("--birthdays", default=None, help="Path to a CSV file containing birthday rows")
    args = parser.parse_args()

    config = load_config(args.config)
    send_time = str(config.get("send_time", "09:00"))
    timezone = str(config.get("timezone", "UTC"))
    if args.schedule and not should_run_now(send_time, timezone):
        print({"status": "skipped", "reason": "outside_send_time"})
        return

    if args.message:
        config["message"] = args.message
    if args.recipient:
        config["recipient"] = args.recipient

    if args.birthdays:
        summary = run_birthdays_workflow(
            config,
            birthday_path=args.birthdays,
            driver_config={"type": args.driver, "dry_run": not args.live},
        )
    else:
        summary = run_workflow(
            config,
            plugins=args.plugin,
            driver_config={"type": args.driver, "dry_run": not args.live},
            recipient=args.recipient,
        )
    print(summary)


if __name__ == "__main__":
    main()
