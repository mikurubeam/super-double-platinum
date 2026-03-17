"""Google Sheets helpers for the dance competition tracker.

This module assumes the user has stored a Service Account JSON in the system
keyring under the key name "service_account_json".

The service account must have edit access to the target spreadsheet.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

import gspread
from google.oauth2.service_account import Credentials

from secrets_manager import get_secret

# The key name used when storing the service account JSON in the keyring.
_SERVICE_ACCOUNT_SECRET_KEY = "service_account_json"

# The spreadsheet ID to operate on.
# Set via environment variable for convenience. Example:
#   export DANCE_SPREADSHEET_ID=1ABC...xyz
_SPREADSHEET_ID_ENV = "DANCE_SPREADSHEET_ID"

# Default worksheet names.
SHEET_RESULTS = "Results"
SHEET_ACCOUNTS = "Accounts"


class SheetError(Exception):
    pass


def _load_credentials() -> Credentials:
    raw = get_secret(_SERVICE_ACCOUNT_SECRET_KEY)
    if not raw:
        raise SheetError(
            "No service account JSON found in keyring. "
            "Run `python -m app setup` and provide the JSON contents."
        )

    try:
        info = json.loads(raw)
    except json.JSONDecodeError as e:
        raise SheetError("Stored service account JSON is not valid JSON") from e

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    return Credentials.from_service_account_info(info, scopes=scopes)


def _get_spreadsheet_id() -> str:
    sid = os.environ.get(_SPREADSHEET_ID_ENV)
    if not sid:
        raise SheetError(
            "Environment variable DANCE_SPREADSHEET_ID is not set. "
            "Set it to the spreadsheet ID (the long string in the sheet URL)."
        )
    return sid


def _client() -> gspread.Client:
    creds = _load_credentials()
    return gspread.authorize(creds)


def _open_spreadsheet() -> gspread.Spreadsheet:
    client = _client()
    sid = _get_spreadsheet_id()
    return client.open_by_key(sid)


def _ensure_sheet(spreadsheet: gspread.Spreadsheet, title: str, header: List[str]) -> gspread.Worksheet:
    """Ensure a sheet exists and has a header row."""
    try:
        ws = spreadsheet.worksheet(title)
    except gspread.exceptions.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=title, rows=1000, cols=len(header))
        ws.append_row(header)
        return ws

    # If the sheet exists but has no header, write it.
    first_row = ws.row_values(1)
    if not first_row:
        ws.append_row(header)
    return ws


def ensure_structure() -> None:
    """Create the required worksheets if they don't exist."""
    ss = _open_spreadsheet()
    _ensure_sheet(ss, SHEET_RESULTS, ["timestamp", "from", "message", "parsed"])
    _ensure_sheet(ss, SHEET_ACCOUNTS, ["username", "password_hash", "created_at"])


def append_result(payload: Dict[str, Any]) -> None:
    """Append a row to the Results sheet."""
    ss = _open_spreadsheet()
    ws = _ensure_sheet(ss, SHEET_RESULTS, ["timestamp", "from", "message", "parsed"])
    ws.append_row([payload.get("timestamp"), payload.get("from"), payload.get("message"), json.dumps(payload.get("parsed", {}))])


def list_results() -> List[Dict[str, Any]]:
    """Return all results as list of dicts."""
    ss = _open_spreadsheet()
    ws = _ensure_sheet(ss, SHEET_RESULTS, ["timestamp", "from", "message", "parsed"])
    records = ws.get_all_records()
    return records


def list_accounts() -> List[Dict[str, Any]]:
    ss = _open_spreadsheet()
    ws = _ensure_sheet(ss, SHEET_ACCOUNTS, ["username", "password_hash", "created_at"])
    return ws.get_all_records()


def add_account(username: str, password_hash: str, created_at: str) -> None:
    ss = _open_spreadsheet()
    ws = _ensure_sheet(ss, SHEET_ACCOUNTS, ["username", "password_hash", "created_at"])
    ws.append_row([username, password_hash, created_at])
