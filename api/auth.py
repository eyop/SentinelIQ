from __future__ import annotations

import hashlib
import hmac
import secrets

from fastapi import Depends, Header, HTTPException, status

from config import get_settings


def authenticate_user(username: str, password: str) -> bool:
    """Validate a username/password pair.

    For the MVP, valid credentials match the configured secret key as the
    password. In a production deployment, replace this with a real
    credential store / password hashing.
    """
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
    """Issue a stateless demo token (token:username)."""
    return secrets.token_urlsafe(24) + f":{username}"


def verify_token(token: str) -> bool:
    """Validate a token issued by create_token."""
    return bool(token and token.count(":") == 1)


def _auth_disabled() -> bool:
    """Auth is bypassed in the local development environment."""
    return get_settings().env == "development"


async def require_auth(
    authorization: str | None = Header(default=None),
) -> None:
    """FastAPI dependency that enforces bearer-token auth.

    In development (`ENV=development`), authentication is bypassed so the
    platform is easy to demo locally. In production, requests must include
    a valid `Authorization: Bearer <token>` header.
    """
    if _auth_disabled():
        return

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.split(" ", 1)[1].strip()
    if not verify_token(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )