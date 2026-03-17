"""Manage secret values using the system keyring.

This module is used to keep long-lived confidential values (like a Google
service account JSON) out of source control, while still making them available
at runtime.

Usage:
  from secrets_manager import set_secret, get_secret
  set_secret("dance_competition_sa", json_text)
  json_text = get_secret("dance_competition_sa")

The keyring backend is chosen by the system (e.g. Secret Service on Linux, Key
Vault on macOS)."""

from __future__ import annotations

import keyring
from typing import Optional

SERVICE_NAME = "dance_competition"


def set_secret(name: str, value: str) -> None:
    """Store a secret value in the system keyring."""
    keyring.set_password(SERVICE_NAME, name, value)


def get_secret(name: str) -> Optional[str]:
    """Retrieve a secret value from the system keyring."""
    return keyring.get_password(SERVICE_NAME, name)


def delete_secret(name: str) -> None:
    """Delete a secret from the keyring."""
    keyring.delete_password(SERVICE_NAME, name)
