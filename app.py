"""Dance competition tracker application.

Run locally and store data in Google Sheets.

Usage:
  python -m app setup            # store service account JSON in keyring
  python -m app run              # start local Flask server
  python -m app poll-sms         # poll Google Voice for new SMS
  python -m app create-account   # create a user account (stored in sheet)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict

from flask import Flask, jsonify, request
from flask_cors import CORS

import auth
from sheets import ensure_structure, list_results
from secrets_manager import set_secret
from sms import handle_incoming_sms


app = Flask(
    __name__,
    static_folder="frontend",
    static_url_path="",
)
CORS(app)


@app.route("/api/results", methods=["GET"])
def api_results() -> Any:
    """Return all captured results."""
    # In a real app you'd add pagination and authentication.
    results = list_results()
    return jsonify(results)


@app.route("/api/create-account", methods=["POST"])
def api_create_account() -> Any:
    """Create a local account. Stores username/password hash in the sheet."""
    body = request.get_json(silent=True) or {}
    username = body.get("username")
    password = body.get("password")
    if not username or not password:
        return jsonify({"ok": False, "error": "username and password required"}), 400

    auth.create_account(username=username, password=password)
    return jsonify({"ok": True})


@app.route("/api/auth", methods=["POST"])
def api_auth() -> Any:
    body = request.get_json(silent=True) or {}
    username = body.get("username")
    password = body.get("password")
    if not username or not password:
        return jsonify({"ok": False, "error": "username and password required"}), 400

    ok = auth.authenticate(username=username, password=password)
    return jsonify({"ok": ok})


@app.route("/webhook/sms", methods=["POST"])
def webhook_sms() -> Any:
    """Receive an incoming SMS via webhook.

    Expected JSON payload:
      {"from": "+12345556789", "message": "dancer: Alice; place: 1"}
    """
    body = request.get_json(silent=True) or {}
    from_number = body.get("from") or body.get("from_number")
    message = body.get("message") or body.get("text")
    if not from_number or not message:
        return jsonify({"ok": False, "error": "missing from or message"}), 400

    handle_incoming_sms(from_number, message)
    return jsonify({"ok": True})


@app.route("/", defaults={"path": "index.html"})
@app.route("/<path:path>")
def serve_frontend(path: str) -> Any:
    """Serve the frontend static site."""
    return app.send_static_file(path)


def _setup() -> None:
    """Interactive setup helper."""
    print("*** Dance Competition Tracker setup ***")
    print("1) Create or open a Google Cloud Service Account with Sheets access.")
    print("2) Download the JSON key file.")
    print("")

    key_path = input("Enter path to service account JSON file: ").strip()
    if not key_path or not os.path.exists(key_path):
        print("Invalid path")
        sys.exit(1)

    with open(key_path, "r", encoding="utf-8") as f:
        raw = f.read().strip()

    # Persist to keyring.
    set_secret("service_account_json", raw)

    print("")
    print("Stored credentials in the system keyring.")
    print("Now set the DANCE_SPREADSHEET_ID environment variable to the target spreadsheet ID.")
    print("Example: export DANCE_SPREADSHEET_ID=1aBcDeFg...")
    print("")
    print("Once you set the environment variable, run: python -m app init")


def _init() -> None:
    """Initialize the spreadsheet (creates required worksheets)."""
    ensure_structure()
    print("Spreadsheet setup complete.")


def _create_account_cli() -> None:
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    auth.create_account(username=username, password=password)
    print("Account created.")


def _run_server(host: str, port: int) -> None:
    print(f"Starting local server: http://{host}:{port}")
    app.run(host=host, port=port)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m app",
        description="Dance competition tracker (local Flask server + Google Sheets backend)",
    )
    parser.add_argument("command", choices=["setup", "init", "run", "poll-sms", "create-account"], help="command to run")
    parser.add_argument("--host", default="127.0.0.1", help="host for run")
    parser.add_argument("--port", type=int, default=5000, help="port for run")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    if args.command == "setup":
        _setup()
    elif args.command == "init":
        _init()
    elif args.command == "run":
        _run_server(host=args.host, port=args.port)
    elif args.command == "poll-sms":
        from sms import _poll_google_voice_every

        _poll_google_voice_every()
    elif args.command == "create-account":
        _create_account_cli()
    else:
        raise RuntimeError("unknown command")


if __name__ == "__main__":
    main()
