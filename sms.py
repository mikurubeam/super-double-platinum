"""SMS handling for the dance competition tracker.

This module provides helpers to parse incoming SMS messages and store them in the
Google Sheet via sheets.append_result().

If your Google phone provider can send webhooks, point it at the /webhook/sms
endpoint in app.py. Otherwise, you can run the polling helper which uses the
unofficial google-voice client to fetch new messages from a Google Voice number.
"""

from __future__ import annotations

import re
import time
from datetime import datetime
from typing import Dict, List, Optional

import requests

from sheets import append_result


def parse_sms_message(text: str) -> Dict[str, str]:
    """Parse a key/value style SMS body into a dict.

    Expected formats (case-insensitive keys):
      "dancer: Alice; place: 1; event: Solo"
      "dancer=Alice,place=1,event=Solo"

    Any other text will still be returned under the key "raw".
    """
    if not text:
        return {"raw": ""}

    text = text.strip()
    # Split on semicolons or commas.
    parts = re.split(r"[;,]\\s*", text)
    data: Dict[str, str] = {}
    for part in parts:
        if not part:
            continue
        if ":" in part:
            k, v = part.split(":", 1)
        elif "=" in part:
            k, v = part.split("=", 1)
        else:
            continue
        data[k.strip().lower()] = v.strip()

    if not data:
        return {"raw": text}

    return data


def handle_incoming_sms(from_number: str, message: str) -> None:
    """Handle an incoming SMS and record it."""
    parsed = parse_sms_message(message)
    payload = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "from": from_number,
        "message": message,
        "parsed": parsed,
    }
    append_result(payload)


def _poll_google_voice_every(interval_s: int = 30):
    """Poll Google Voice for new messages.

    This uses the unofficial google-voice library (https://pypi.org/project/google-voice/).
    You must configure the login via environment variables (or .netrc) as described
    in its documentation.

    Notes:
    - Polling is RATE LIMITED; keep interval reasonably high (>= 30s).
    - This is intended as a fallback when webhooks are not available.
    """
    try:
        import googlevoice
        from googlevoice import Voice
    except ImportError as e:
        raise RuntimeError(
            "google-voice library not installed. Install it with `pip install google-voice`."
        ) from e

    voice = Voice()
    # Login using environment variables or .netrc file as per google-voice docs.
    voice.login()

    last_ts: Optional[int] = None

    while True:
        sms = voice.sms
        sms.refresh()
        for msg in sms.messages:
            ts = int(msg.timestamp)
            if last_ts is None or ts > last_ts:
                handle_incoming_sms(msg.number, msg.message)
                last_ts = ts
        time.sleep(interval_s)


def webhook_test(url: str, from_number: str, message: str) -> None:
    """Send a test webhook POST to a webhook URL.

    This is just a helper so you can confirm your webhook receiver works.
    """
    data = {"from": from_number, "message": message}
    requests.post(url, json=data)
