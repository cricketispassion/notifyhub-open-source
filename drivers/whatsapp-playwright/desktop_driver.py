from __future__ import annotations

import time
from pathlib import Path
from typing import Any

try:
    import psutil
except ImportError:  # pragma: no cover - optional dependency
    psutil = None

try:
    import pyautogui
except ImportError:  # pragma: no cover - optional dependency
    pyautogui = None

try:
    import pygetwindow as gw
except ImportError:  # pragma: no cover - optional dependency
    gw = None

try:
    from pywinauto import Application
except ImportError:  # pragma: no cover - optional dependency
    Application = None


def get_search_shortcut() -> str:
    return "ctrl+f"


def _matches_recipient(window_title: str, recipient: str) -> bool:
    normalized_title = window_title.strip().lower()
    normalized_recipient = recipient.strip().lower()
    return normalized_recipient in normalized_title or normalized_title in normalized_recipient


class WhatsAppDesktopDriver:
    def __init__(self, timeout: int = 30000) -> None:
        self.timeout = timeout

    def _find_window(self):
        if gw is None:
            return None

        for window in gw.getWindowsWithTitle('WhatsApp'):
            if window.title.lower().startswith('whatsapp'):
                return window

        for window in gw.getAllWindows():
            if window.title and 'whatsapp' in window.title.lower():
                return window

        if psutil is not None and Application is not None:
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                info = proc.info
                name = (info.get('name') or '').lower()
                exe = (info.get('exe') or '').lower()
                if 'whatsapp' in name or 'whatsapp' in exe:
                    try:
                        app = Application().connect(process=info['pid'])
                        windows = app.windows()
                        if windows:
                            return windows[0]
                    except Exception:
                        continue

        return None

    def send_message(self, recipient: str, message: str, dry_run: bool = True) -> dict[str, Any]:
        if dry_run:
            return {"status": "simulated", "recipient": recipient, "message": message}

        if pyautogui is None or gw is None or Application is None or psutil is None:
            return {"status": "error", "recipient": recipient, "message": message, "detail": "Desktop automation dependencies are not installed."}

        window = self._find_window()
        if window is None:
            return {"status": "error", "recipient": recipient, "message": message, "detail": "WhatsApp desktop app is not running."}

        try:
            if hasattr(window, '_hWnd'):
                app = Application().connect(handle=window._hWnd)
                app_top = app.windows()[0] if app.windows() else app.top_window()
            else:
                app_top = window

            if hasattr(app_top, 'set_focus'):
                app_top.set_focus()
            elif hasattr(window, 'activate'):
                window.activate()
            else:
                window.restore()
        except Exception as exc:
            return {"status": "error", "recipient": recipient, "message": message, "detail": f"Could not focus WhatsApp window: {exc}"}

        time.sleep(1)
        pyautogui.hotkey(*get_search_shortcut().split('+'))
        time.sleep(1)
        pyautogui.typewrite(recipient, interval=0.05)
        time.sleep(2)
        pyautogui.press('enter')
        time.sleep(2)

        if gw is not None:
            app_windows = [w for w in gw.getAllWindows() if _matches_recipient(w.title, recipient)]
            if not app_windows:
                return {
                    "status": "error",
                    "recipient": recipient,
                    "message": message,
                    "detail": "Could not confirm the chat window for recipient.",
                }

        pyautogui.typewrite(message, interval=0.05)
        time.sleep(1)
        pyautogui.press('enter')
        return {"status": "sent", "recipient": recipient, "message": message}
