from __future__ import annotations

import json
import os
import urllib.request
from typing import Any


class WhatsAppCloudDriver:
    def __init__(self, api_token: str | None = None, phone_number_id: str | None = None) -> None:
        self.api_token = api_token or os.getenv("WHATSAPP_CLOUD_API_TOKEN")
        self.phone_number_id = phone_number_id or os.getenv("WHATSAPP_CLOUD_PHONE_NUMBER_ID")
        self.api_version = os.getenv("WHATSAPP_CLOUD_API_VERSION", "v17.0")

    def send_message(self, recipient: str, message: str, dry_run: bool = True) -> dict[str, Any]:
        if dry_run:
            return {"status": "simulated", "recipient": recipient, "message": message}

        if not self.api_token or not self.phone_number_id:
            return {
                "status": "error",
                "recipient": recipient,
                "message": message,
                "detail": "Missing WHATSAPP_CLOUD_API_TOKEN or WHATSAPP_CLOUD_PHONE_NUMBER_ID.",
            }

        url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": message},
        }

        request_data = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

        try:
            request = urllib.request.Request(url, data=request_data, headers=headers, method="POST")
            with urllib.request.urlopen(request, timeout=30) as response:
                response_data = response.read().decode("utf-8")
            return {
                "status": "sent",
                "recipient": recipient,
                "message": message,
                "detail": response_data,
            }
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8") if exc.fp else ""
            return {
                "status": "error",
                "recipient": recipient,
                "message": message,
                "detail": f"HTTP {exc.code}: {body}",
            }
        except Exception as exc:
            return {
                "status": "error",
                "recipient": recipient,
                "message": message,
                "detail": str(exc),
            }
