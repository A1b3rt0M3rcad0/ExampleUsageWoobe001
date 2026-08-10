from __future__ import annotations

import hmac

from fastapi import Header, HTTPException, Request, status

from .config import Settings


SESSION_KEY = "user"


def authenticate_demo_user(email: str, password: str, settings: Settings) -> bool:
    return hmac.compare_digest(email.strip().lower(), settings.demo_email.lower()) and hmac.compare_digest(
        password, settings.demo_password
    )


def require_user(request: Request, settings: Settings) -> dict[str, str]:
    principal = request.session.get(SESSION_KEY)
    if not isinstance(principal, dict) or principal.get("user_id") != settings.demo_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return principal


def require_tool_key(
    settings: Settings,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> None:
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token or not hmac.compare_digest(token, settings.woobe_tool_api_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid tool credential")
