from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator
from uuid import uuid4

from .config import Settings


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Database:
    def __init__(self, settings: Settings) -> None:
        self.path = Path(settings.database_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.settings = settings

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    account_id TEXT NOT NULL,
                    surface_public_id TEXT NOT NULL,
                    woobe_session_id TEXT NOT NULL UNIQUE,
                    target_release_id TEXT,
                    created_at TEXT NOT NULL,
                    last_accessed_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS logs (
                    id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    service TEXT NOT NULL,
                    event TEXT NOT NULL,
                    message TEXT NOT NULL,
                    request_id TEXT,
                    metadata_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS problems (
                    id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    title TEXT NOT NULL,
                    service TEXT NOT NULL,
                    detected_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL,
                    occurrences INTEGER NOT NULL,
                    summary TEXT NOT NULL,
                    evidence_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS reports (
                    id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    period_label TEXT NOT NULL,
                    executive_summary TEXT NOT NULL,
                    findings_json TEXT NOT NULL,
                    recommendations_json TEXT NOT NULL,
                    generated_by TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

            existing = db.execute(
                "SELECT COUNT(*) AS count FROM logs WHERE account_id = ?",
                (self.settings.demo_account_id,),
            ).fetchone()["count"]
            if existing == 0:
                self._seed_logs(db)

            existing = db.execute(
                "SELECT COUNT(*) AS count FROM problems WHERE account_id = ?",
                (self.settings.demo_account_id,),
            ).fetchone()["count"]
            if existing == 0:
                self._seed_problems(db)

    def _seed_logs(self, db: sqlite3.Connection) -> None:
        now = utcnow()
        fixtures = [
            (-7, "INFO", "api-gateway", "request.completed", "GET /v1/projects completed with 200", "req_7f1", {"latency_ms": 84, "status_code": 200}),
            (-18, "WARN", "billing-api", "usage.threshold", "Monthly API usage crossed 80% of plan quota", "req_7e9", {"usage": 8120, "limit": 10000}),
            (-28, "ERROR", "webhook-worker", "delivery.failed", "Webhook delivery failed after 3 retries", "req_7d2", {"endpoint": "https://client.example/webhooks", "status_code": 503, "attempts": 3}),
            (-34, "ERROR", "auth-api", "credential.rejected", "API credential rejected because it is revoked", "req_7ca", {"credential_id": "key_prod_04", "reason": "revoked"}),
            (-43, "WARN", "api-gateway", "rate_limit.near", "Request rate is above 90% of the minute limit", "req_7b1", {"current_rpm": 456, "limit_rpm": 500}),
            (-58, "INFO", "reporting-api", "report.created", "Weekly operational report created", "req_79a", {"report_id": "rpt_previous"}),
            (-73, "ERROR", "payments-api", "upstream.timeout", "Payment provider timed out", "req_765", {"provider": "demo-pay", "timeout_ms": 5000}),
            (-120, "INFO", "auth-api", "credential.rotated", "Production API credential rotated", "req_711", {"credential_id": "key_prod_05"}),
        ]
        for minutes, severity, service, event, message, request_id, metadata in fixtures:
            db.execute(
                """
                INSERT INTO logs(id, account_id, occurred_at, severity, service, event, message, request_id, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"log_{uuid4().hex[:12]}",
                    self.settings.demo_account_id,
                    (now + timedelta(minutes=minutes)).isoformat(),
                    severity,
                    service,
                    event,
                    message,
                    request_id,
                    json.dumps(metadata),
                ),
            )

    def _seed_problems(self, db: sqlite3.Connection) -> None:
        now = utcnow()
        fixtures = [
            (
                "open",
                "high",
                "Revoked production credential still configured in one integration",
                "auth-api",
                -36,
                -34,
                9,
                "Requests from one integration are using a credential that was revoked during rotation.",
                [
                    "9 rejected requests in the last hour",
                    "credential_id=key_prod_04 is revoked",
                    "replacement credential key_prod_05 is active",
                ],
            ),
            (
                "monitoring",
                "medium",
                "Webhook endpoint intermittently unavailable",
                "webhook-worker",
                -95,
                -28,
                4,
                "The customer webhook endpoint returned 503 intermittently and caused retry exhaustion.",
                [
                    "4 failed deliveries",
                    "all failures returned HTTP 503",
                    "last successful delivery occurred 22 minutes ago",
                ],
            ),
            (
                "resolved",
                "low",
                "Temporary payment provider latency",
                "payments-api",
                -180,
                -73,
                3,
                "A short latency spike caused upstream timeouts. The provider recovered without intervention.",
                [
                    "3 timeouts",
                    "provider latency returned to baseline",
                ],
            ),
        ]
        for status, severity, title, service, detected_delta, last_delta, occurrences, summary, evidence in fixtures:
            db.execute(
                """
                INSERT INTO problems(id, account_id, status, severity, title, service, detected_at, last_seen_at, occurrences, summary, evidence_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"prb_{uuid4().hex[:10]}",
                    self.settings.demo_account_id,
                    status,
                    severity,
                    title,
                    service,
                    (now + timedelta(minutes=detected_delta)).isoformat(),
                    (now + timedelta(minutes=last_delta)).isoformat(),
                    occurrences,
                    summary,
                    json.dumps(evidence),
                ),
            )
