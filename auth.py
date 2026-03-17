"""Simple account management for the dance competition tracker.

Accounts are stored in the Google Sheet and passwords are hashed with bcrypt.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import bcrypt

from sheets import add_account, list_accounts


def hash_password(plain: str) -> str:
    """Hash a password for storage."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a password against a stored hash."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def create_account(username: str, password: str) -> None:
    """Create a new account in the spreadsheet."""
    now = datetime.utcnow().isoformat() + "Z"
    password_hash = hash_password(password)
    add_account(username=username, password_hash=password_hash, created_at=now)


def authenticate(username: str, password: str) -> bool:
    """Check username/password againt the stored accounts."""
    accounts = list_accounts()
    for row in accounts:
        if row.get("username") == username:
            return verify_password(password, row.get("password_hash", ""))
    return False
