from __future__ import annotations

import hashlib
import hmac
import secrets
from typing import Any

from config import get_settings


def authenticate_user(username: str, password: str) -> bool:
    settings = get_settings()
    if not username or not password:
        return False
    expected = settings.secret_key
    digest = hmac.compare_digest(
        hashlib.sha256(f"{username}:{password}".encode("utf-8")).hexdigest(),
        hashlib.sha256(f"{username}:{expected}".encode("utf-8")).hexdigest(),
    )
    return digest


def create_token(username: str) -> str:
    return secrets.token_urlsafe(24) + f":{username}"


def verify_token(token: str) -> bool:
    return bool(token and token.count(":") == 1)
