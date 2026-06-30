from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any


class WhatsAppPlaywrightDriver:
    def __init__(self, headless: bool = True, timeout: int = 30000, login_wait_seconds: int = 30) -> None:
        self.headless = headless
        self.timeout = timeout
        self.login_wait_seconds = login_wait_seconds

    def send_message(self, recipient: str, message: str, dry_run: bool = True) -> dict[str, Any]:
        if dry_run:
            return {"status": "simulated", "recipient": recipient, "message": message}

        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise RuntimeError(
                "Playwright is not installed. Run 'python -m pip install playwright' and 'python -m playwright install chromium'."
            ) from exc

        user_data_dir = Path(__file__).resolve().parent / "profile"
        user_data_dir.mkdir(parents=True, exist_ok=True)

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch_persistent_context(
                str(user_data_dir),
                headless=self.headless,
                channel="chromium",
            )
            try:
                page = browser.new_page()
                page.goto("https://web.whatsapp.com", wait_until="domcontentloaded", timeout=self.timeout)
                page.wait_for_load_state("networkidle", timeout=self.timeout)

                deadline = time.time() + self.login_wait_seconds
                while time.time() < deadline:
                    if page.locator("input[placeholder='Search or start new chat']").count() > 0:
                        break
                    if page.locator("text=Link with phone number instead.").count() > 0:
                        try:
                            page.locator("text=Link with phone number instead.").click(timeout=2000)
                        except Exception:
                            pass
                    time.sleep(2)

                search_box = page.locator("input[placeholder='Search or start new chat']")
                search_box = search_box.first if search_box.count() > 0 else None
                if search_box is None:
                    return {
                        "status": "pending_login",
                        "recipient": recipient,
                        "message": message,
                        "detail": "WhatsApp Web is not ready yet. Complete the phone-number or QR login flow and retry.",
                    }

                try:
                    search_box.click()
                    search_box.fill(recipient)
                    page.keyboard.press("Enter")
                except Exception:  # pragma: no cover - browser runtime differences
                    pass

                composer = page.locator("div[contenteditable='true']").last
                if composer.count() == 0:
                    return {
                        "status": "error",
                        "recipient": recipient,
                        "message": message,
                        "detail": "Could not find the chat composer in WhatsApp Web.",
                    }

                composer.click()
                composer.fill(message)
                page.keyboard.press("Enter")
                return {
                    "status": "sent",
                    "recipient": recipient,
                    "message": message,
                    "url": page.url,
                }
            finally:
                browser.close()
