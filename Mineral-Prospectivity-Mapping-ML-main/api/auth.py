"""Authentification JWT pour l'API CriticalMineralsCompass."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

JWT_SECRET = os.getenv("COMPASS_JWT_SECRET", "change-me-in-production")
JWT_ENABLED = os.getenv("COMPASS_JWT_ENABLED", "false").lower() in ("1", "true", "yes")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("COMPASS_JWT_EXPIRE_MINUTES", "480"))

API_USER = os.getenv("COMPASS_API_USER", "admin")
API_PASSWORD = os.getenv("COMPASS_API_PASSWORD", "compass-rdc")

_bearer = HTTPBearer(auto_error=False)


def authenticate_user(username: str, password: str) -> bool:
    return username == API_USER and password == API_PASSWORD


def create_access_token(username: str) -> tuple[str, int]:
    expires_minutes = JWT_EXPIRE_MINUTES
    expire = datetime.now(UTC) + timedelta(minutes=expires_minutes)
    payload = {"sub": username, "exp": expire, "iat": datetime.now(UTC)}
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token, expires_minutes * 60


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expiré") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide") from exc


def require_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    """Dépendance FastAPI — exige un JWT valide si l'auth est activée."""
    if not JWT_ENABLED:
        return "anonymous"

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentification requise",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials)
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide")
    return str(username)
