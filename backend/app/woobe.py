from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import httpx
from .config import Settings

class WoobeIntegrationError(RuntimeError):
    pass

@dataclass(frozen=True)
class SurfaceSession:
    session_id: str
    target_release_id: str | None

class WoobeChatSurfaceClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def create_session(self, *, public_id: str, access_key: str, external_reference: str, metadata: dict[str, Any]) -> SurfaceSession:
        url = f"{self.settings.woobe_api_base_url.rstrip('/')}/v1/chat-surfaces/{public_id}/sessions"
        async with httpx.AsyncClient(timeout=self.settings.woobe_request_timeout_seconds) as client:
            response = await client.post(url, headers={'Authorization':f'Bearer {access_key}','Idempotency-Key':external_reference}, json={'external_reference':external_reference,'metadata':metadata})
        if response.status_code >= 400:
            raise WoobeIntegrationError(f"Woobe session creation failed with HTTP {response.status_code}: {response.text[:400]}")
        payload = response.json(); session_id = payload.get('session_id')
        if not session_id: raise WoobeIntegrationError('Woobe session response did not include session_id')
        return SurfaceSession(session_id=session_id,target_release_id=payload.get('target_release_id'))

    async def issue_token(self, *, public_id: str, access_key: str, session_id: str) -> dict[str, Any]:
        url = f"{self.settings.woobe_api_base_url.rstrip('/')}/v1/chat-surfaces/{public_id}/sessions/{session_id}/tokens"
        async with httpx.AsyncClient(timeout=self.settings.woobe_request_timeout_seconds) as client:
            response = await client.post(url, headers={'Authorization':f'Bearer {access_key}'}, json={'origin':self.settings.woobe_host_origin})
        if response.status_code >= 400:
            raise WoobeIntegrationError(f"Woobe token issuance failed with HTTP {response.status_code}: {response.text[:400]}")
        payload = response.json()
        if not payload.get('session_token'): raise WoobeIntegrationError('Woobe token response did not include session_token')
        return payload
