from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.middleware.sessions import SessionMiddleware

from .config import Settings, get_settings
from .db import Database
from .security import SESSION_KEY, authenticate_demo_user, require_tool_key, require_user
from .woobe import WoobeChatSurfaceClient, WoobeIntegrationError, new_local_binding_id


class LoginRequest(BaseModel):
    email: str
    password: str


class ReportCreateRequest(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    period_label: str = Field(min_length=1, max_length=80)
    executive_summary: str = Field(min_length=10, max_length=4000)
    findings: list[str] = Field(min_length=1, max_length=20)
    recommendations: list[str] = Field(default_factory=list, max_length=20)


settings = get_settings()
db = Database(settings)
db.initialize()

app = FastAPI(title="ExampleUsageWoobe001 API", version="0.1.0")
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.app_secret_key,
    session_cookie="example_usage_session",
    same_site="lax",
    https_only=settings.app_environment.lower() == "production",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_json(value: str) -> Any:
    return json.loads(value) if value else None


def account_payload() -> dict[str, Any]:
    return {
        "id": settings.demo_account_id,
        "name": "Northstar Labs",
        "plan": "Starter",
        "monthly_api_calls": 8120,
        "monthly_api_limit": 10000,
        "usage_percent": 81.2,
        "renewal_in_days": 3,
        "status": "active",
        "services": [
            {"name": "API Gateway", "status": "healthy"},
            {"name": "Authentication", "status": "degraded"},
            {"name": "Webhooks", "status": "degraded"},
            {"name": "Billing", "status": "healthy"},
        ],
        "api_credentials": [
            {"id": "key_prod_05", "name": "Production", "status": "active", "created_at": "2026-08-10T14:10:00Z"},
            {"id": "key_prod_04", "name": "Legacy production", "status": "revoked", "revoked_at": "2026-08-10T15:41:00Z"},
        ],
    }


def tool_guard(authorization: str | None = None) -> None:
    require_tool_key(settings, authorization)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/auth/login")
def login(payload: LoginRequest, request: Request) -> dict[str, Any]:
    if not authenticate_demo_user(payload.email, payload.password, settings):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    request.session[SESSION_KEY] = {
        "user_id": settings.demo_user_id,
        "account_id": settings.demo_account_id,
        "email": settings.demo_email,
        "name": "Morgan Lee",
    }
    return {"success": True}


@app.post("/api/auth/logout")
def logout(request: Request) -> dict[str, bool]:
    request.session.clear()
    return {"success": True}


@app.get("/api/me")
def me(request: Request) -> dict[str, Any]:
    principal = require_user(request, settings)
    return {
        **principal,
        "account": account_payload(),
    }


@app.get("/api/account")
def get_account(request: Request) -> dict[str, Any]:
    require_user(request, settings)
    return account_payload()


@app.get("/api/logs")
def get_logs(
    request: Request,
    severity: str | None = Query(default=None),
    service: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[dict[str, Any]]:
    require_user(request, settings)
    query = "SELECT * FROM logs WHERE account_id = ?"
    params: list[Any] = [settings.demo_account_id]
    if severity:
        query += " AND severity = ?"
        params.append(severity.upper())
    if service:
        query += " AND service = ?"
        params.append(service)
    query += " ORDER BY occurred_at DESC LIMIT ?"
    params.append(limit)
    with db.connect() as connection:
        rows = connection.execute(query, params).fetchall()
    return [
        {
            **dict(row),
            "metadata": parse_json(row["metadata_json"]),
        }
        for row in rows
    ]


@app.get("/api/problems")
def get_problems(
    request: Request,
    status_filter: str | None = Query(default=None, alias="status"),
) -> list[dict[str, Any]]:
    require_user(request, settings)
    query = "SELECT * FROM problems WHERE account_id = ?"
    params: list[Any] = [settings.demo_account_id]
    if status_filter:
        query += " AND status = ?"
        params.append(status_filter)
    query += " ORDER BY CASE severity WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END, last_seen_at DESC"
    with db.connect() as connection:
        rows = connection.execute(query, params).fetchall()
    return [
        {
            **dict(row),
            "evidence": parse_json(row["evidence_json"]),
        }
        for row in rows
    ]


@app.get("/api/reports")
def get_reports(request: Request) -> list[dict[str, Any]]:
    require_user(request, settings)
    with db.connect() as connection:
        rows = connection.execute(
            "SELECT * FROM reports WHERE account_id = ? ORDER BY created_at DESC",
            (settings.demo_account_id,),
        ).fetchall()
    return [
        {
            **dict(row),
            "findings": parse_json(row["findings_json"]),
            "recommendations": parse_json(row["recommendations_json"]),
        }
        for row in rows
    ]


@app.post("/api/chat/session")
async def create_or_get_chat_session(request: Request) -> dict[str, Any]:
    principal = require_user(request, settings)
    with db.connect() as connection:
        existing = connection.execute(
            """
            SELECT * FROM chat_sessions
            WHERE user_id = ? AND account_id = ? AND surface_public_id = ?
            ORDER BY created_at DESC LIMIT 1
            """,
            (principal["user_id"], principal["account_id"], settings.woobe_chat_surface_public_id),
        ).fetchone()
        if existing:
            connection.execute(
                "UPDATE chat_sessions SET last_accessed_at = ? WHERE id = ?",
                (now_iso(), existing["id"]),
            )
            return {
                "binding_id": existing["id"],
                "session_id": existing["woobe_session_id"],
                "target_release_id": existing["target_release_id"],
                "surface_id": settings.woobe_chat_surface_public_id,
            }

    client = WoobeChatSurfaceClient(settings)
    try:
        remote = await client.create_session(
            external_reference=f"{principal['account_id']}:{principal['user_id']}",
            account_id=principal["account_id"],
            user_id=principal["user_id"],
        )
    except WoobeIntegrationError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    binding_id = new_local_binding_id()
    with db.connect() as connection:
        connection.execute(
            """
            INSERT INTO chat_sessions(id, user_id, account_id, surface_public_id, woobe_session_id, target_release_id, created_at, last_accessed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                binding_id,
                principal["user_id"],
                principal["account_id"],
                settings.woobe_chat_surface_public_id,
                remote.session_id,
                remote.target_release_id,
                now_iso(),
                now_iso(),
            ),
        )
    return {
        "binding_id": binding_id,
        "session_id": remote.session_id,
        "target_release_id": remote.target_release_id,
        "surface_id": settings.woobe_chat_surface_public_id,
    }


@app.post("/api/chat/session/token")
async def issue_chat_token(request: Request) -> dict[str, Any]:
    principal = require_user(request, settings)
    with db.connect() as connection:
        binding = connection.execute(
            """
            SELECT * FROM chat_sessions
            WHERE user_id = ? AND account_id = ? AND surface_public_id = ?
            ORDER BY created_at DESC LIMIT 1
            """,
            (principal["user_id"], principal["account_id"], settings.woobe_chat_surface_public_id),
        ).fetchone()
    if not binding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not initialized")
    client = WoobeChatSurfaceClient(settings)
    try:
        token = await client.issue_token(binding["woobe_session_id"])
    except WoobeIntegrationError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    return {
        "surface_id": settings.woobe_chat_surface_public_id,
        "session_id": binding["woobe_session_id"],
        "target_release_id": binding["target_release_id"],
        **token,
    }


# Woobe HTTP Tool API. These endpoints are intentionally account-scoped to the single demo tenant.
# The current ChatSurface MVP does not provide delegated per-user Tool identity, so this API must not
# be presented as a production multi-tenant authorization model.

@app.get("/api/woobe-tools/account")
def tool_account(authorization: str | None = Header(default=None, alias="Authorization")) -> dict[str, Any]:
    tool_guard(authorization)
    return {"account": account_payload()}


@app.get("/api/woobe-tools/logs")
def tool_logs(
    authorization: str | None = Header(default=None, alias="Authorization"),
    severity: str | None = Query(default=None),
    service: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> dict[str, Any]:
    tool_guard(authorization)
    query = "SELECT * FROM logs WHERE account_id = ?"
    params: list[Any] = [settings.demo_account_id]
    if severity:
        query += " AND severity = ?"
        params.append(severity.upper())
    if service:
        query += " AND service = ?"
        params.append(service)
    query += " ORDER BY occurred_at DESC LIMIT ?"
    params.append(limit)
    with db.connect() as connection:
        rows = connection.execute(query, params).fetchall()
    return {
        "account_id": settings.demo_account_id,
        "count": len(rows),
        "logs": [
            {
                "id": row["id"],
                "occurred_at": row["occurred_at"],
                "severity": row["severity"],
                "service": row["service"],
                "event": row["event"],
                "message": row["message"],
                "request_id": row["request_id"],
                "metadata": parse_json(row["metadata_json"]),
            }
            for row in rows
        ],
    }


@app.get("/api/woobe-tools/problems")
def tool_problems(
    authorization: str | None = Header(default=None, alias="Authorization"),
    status_filter: str | None = Query(default=None, alias="status"),
) -> dict[str, Any]:
    tool_guard(authorization)
    query = "SELECT * FROM problems WHERE account_id = ?"
    params: list[Any] = [settings.demo_account_id]
    if status_filter:
        query += " AND status = ?"
        params.append(status_filter)
    query += " ORDER BY CASE severity WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END, last_seen_at DESC"
    with db.connect() as connection:
        rows = connection.execute(query, params).fetchall()
    return {
        "account_id": settings.demo_account_id,
        "count": len(rows),
        "problems": [
            {
                "id": row["id"],
                "status": row["status"],
                "severity": row["severity"],
                "title": row["title"],
                "service": row["service"],
                "detected_at": row["detected_at"],
                "last_seen_at": row["last_seen_at"],
                "occurrences": row["occurrences"],
                "summary": row["summary"],
                "evidence": parse_json(row["evidence_json"]),
            }
            for row in rows
        ],
    }


@app.post("/api/woobe-tools/reports", status_code=201)
def tool_create_report(
    payload: ReportCreateRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> dict[str, Any]:
    tool_guard(authorization)
    report_id = f"rpt_{uuid4().hex[:12]}"
    created_at = now_iso()
    with db.connect() as connection:
        connection.execute(
            """
            INSERT INTO reports(id, account_id, title, period_label, executive_summary, findings_json, recommendations_json, generated_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                report_id,
                settings.demo_account_id,
                payload.title,
                payload.period_label,
                payload.executive_summary,
                json.dumps(payload.findings),
                json.dumps(payload.recommendations),
                "woobe-assistant",
                created_at,
            ),
        )
    return {
        "report": {
            "id": report_id,
            "title": payload.title,
            "period_label": payload.period_label,
            "executive_summary": payload.executive_summary,
            "findings": payload.findings,
            "recommendations": payload.recommendations,
            "generated_by": "woobe-assistant",
            "created_at": created_at,
        }
    }
