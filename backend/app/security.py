from hmac import compare_digest
from typing import Any
from fastapi import HTTPException, Request, status
from .config import Settings

ADMIN_SESSION_KEY = "mercury_admin"

def authenticate_admin(email: str, password: str, settings: Settings) -> bool:
    return compare_digest(email.strip().lower(), settings.admin_email.lower()) and compare_digest(password, settings.admin_password)

def require_admin(request: Request, settings: Settings) -> dict[str, Any]:
    principal = request.session.get(ADMIN_SESSION_KEY)
    if not principal or principal.get("user_id") != settings.admin_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return principal

def require_bearer(expected: str, authorization: str | None) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Tool authorization")
    actual = authorization.removeprefix("Bearer ").strip()
    if not compare_digest(actual, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Tool authorization")
