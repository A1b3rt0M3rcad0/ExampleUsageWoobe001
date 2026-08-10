from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

import httpx

from .config import Settings


class WoobeIntegrationError(RuntimeError):
    pass


@dataclass(frozen=True)
class WoobeSession:
    session_id: str
    target_release_id: str | None


class WoobeChatSurfaceClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _assert_configured(self) -> None:
        if not self.settings.woobe_chat_surface_public_id:
            raise WoobeIntegrationError("WOOBE_CHAT_SURFACE_PUBLIC_ID is not configured")
        if not self.settings.woobe_chat_surface_access_key:
            raise WoobeIntegrationError("WOOBE_CHAT_SURFACE_ACCESS_KEY is not configured")

    async def create_session(self, *, external_reference: str, account_id: str, user_id: str) -> WoobeSession:
        self._assert_configured()
        url = (
            f"{self.settings.woobe_api_base_url.rstrip('/')}"
            f"/v1/chat-surfaces/{self.settings.woobe_chat_surface_public_id}/sessions"
        )
        headers = {
            "Authorization": f"Bearer {self.settings.woobe_chat_surface_access_key}",
            "Idempotency-Key": f"{account_id}:{user_id}:{external_reference}",
        }
        payload = {
            "external_reference": external_reference,
            "metadata": {
                "application": "ExampleUsageWoobe001",
                "account_reference": account_id,
                "user_reference": user_id,
            },
        }
        async with httpx.AsyncClient(timeout=self.settings.woobe_request_timeout_seconds) as client:
            response = await client.post(url, headers=headers, json=payload)
        if response.status_code >= 400:
            raise WoobeIntegrationError(f"Woobe session creation failed with HTTP {response.status_code}")
        body = response.json().get("data") or {}
        session_id = body.get("session_id")
        if not session_id:
            raise WoobeIntegrationError("Woobe did not return a session_id")
        return WoobeSession(
            session_id=str(session_id),
            target_release_id=str(body.get("target_release_id")) if body.get("target_release_id") else None,
        )

    async def issue_token(self, session_id: str) -> dict:
        self._assert_configured()
        url = (
            f"{self.settings.woobe_api_base_url.rstrip('/')}"
            f"/v1/chat-surfaces/{self.settings.woobe_chat_surface_public_id}/sessions/{session_id}/tokens"
        )
        headers = {"Authorization": f"Bearer {self.settings.woobe_chat_surface_access_key}"}
        payload = {"origin": self.settings.woobe_host_origin}
        async with httpx.AsyncClient(timeout=self.settings.woobe_request_timeout_seconds) as client:
            response = await client.post(url, headers=headers, json=payload)
        if response.status_code >= 400:
            raise WoobeIntegrationError(f"Woobe token issuance failed with HTTP {response.status_code}")
        data = response.json().get("data") or {}
        if not data.get("session_token"):
            raise WoobeIntegrationError("Woobe did not return a session_token")
        return data


def new_local_binding_id() -> str:
    return f"bind_{uuid4().hex[:16]}"
