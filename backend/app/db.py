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

            # This repository is a deterministic proof-of-value environment. Operational
            # telemetry is intentionally synthetic and refreshed on every API startup so
            # the demo always has recent, internally consistent evidence to investigate.
            db.execute(
                "DELETE FROM logs WHERE account_id = ?",
                (self.settings.demo_account_id,),
            )
            db.execute(
                "DELETE FROM problems WHERE account_id = ?",
                (self.settings.demo_account_id,),
            )
            self._seed_logs(db)
            self._seed_problems(db)

    def _seed_logs(self, db: sqlite3.Connection) -> None:
        now = utcnow()
        fixtures = [
            (-4, "ERROR", "database", "pool.exhausted", "PostgreSQL connection pool exhausted; requests are waiting for a free connection", "req_db_901", {"active_connections": 50, "pool_size": 50, "waiting_requests": 37, "wait_ms_p95": 1840}),
            (-6, "ERROR", "api-gateway", "request.failed", "POST /v1/orders returned 503 because the orders service could not acquire a database connection", "req_api_900", {"status_code": 503, "route": "/v1/orders", "upstream": "orders-api", "latency_ms": 2134}),
            (-8, "WARN", "database", "pool.saturation", "Database connection pool utilization has remained above 92% for five minutes", "req_db_899", {"utilization_percent": 96, "pool_size": 50}),
            (-11, "ERROR", "auth-api", "credential.rejected", "API credential rejected because it is revoked", "req_auth_812", {"credential_id": "key_prod_04", "reason": "revoked", "client": "legacy-importer"}),
            (-13, "WARN", "notifications-worker", "queue.lag", "Notification queue lag exceeded the operational threshold", "req_notif_450", {"queue": "notifications.email", "pending": 1834, "oldest_message_seconds": 286}),
            (-15, "ERROR", "webhook-worker", "delivery.failed", "Webhook delivery failed after 3 retries", "req_hook_774", {"endpoint": "https://client.example/webhooks", "status_code": 503, "attempts": 3, "customer": "org_meridian"}),
            (-18, "WARN", "api-gateway", "rate_limit.near", "Request rate is above 94% of the minute limit", "req_api_887", {"current_rpm": 472, "limit_rpm": 500}),
            (-21, "ERROR", "payments-api", "upstream.timeout", "Payment authorization provider timed out", "req_pay_661", {"provider": "demo-pay", "operation": "authorize", "timeout_ms": 5000, "amount": 128.40}),
            (-24, "ERROR", "notifications-worker", "provider.rejected", "Email provider rejected a delivery batch with HTTP 429", "req_notif_441", {"provider": "mail-demo", "status_code": 429, "batch_size": 100}),
            (-27, "ERROR", "orders-api", "database.unavailable", "Order creation failed while waiting for a database connection", "req_ord_551", {"operation": "create_order", "db_wait_ms": 2012}),
            (-31, "WARN", "cache", "hit_rate.degraded", "Redis cache hit rate dropped below the expected baseline", "req_cache_332", {"hit_rate_percent": 61.2, "baseline_percent": 91.0, "evictions_last_hour": 482}),
            (-34, "ERROR", "webhook-worker", "delivery.failed", "Webhook endpoint returned HTTP 503", "req_hook_760", {"endpoint": "https://client.example/webhooks", "status_code": 503, "attempt": 1, "customer": "org_meridian"}),
            (-38, "WARN", "billing-api", "invoice.retry", "Invoice generation scheduled for retry after a transient database lock", "req_bill_219", {"invoice_id": "inv_demo_1842", "retry_in_seconds": 60}),
            (-43, "ERROR", "payments-api", "upstream.timeout", "Payment provider timed out during capture", "req_pay_649", {"provider": "demo-pay", "operation": "capture", "timeout_ms": 5000, "amount": 89.90}),
            (-49, "INFO", "api-gateway", "request.completed", "GET /v1/projects completed with 200", "req_api_841", {"latency_ms": 84, "status_code": 200}),
            (-56, "WARN", "billing-api", "usage.threshold", "Monthly API usage crossed 80% of plan quota", "req_bill_201", {"usage": 8120, "limit": 10000}),
            (-63, "ERROR", "auth-api", "credential.rejected", "Legacy importer attempted to use revoked production credential", "req_auth_790", {"credential_id": "key_prod_04", "reason": "revoked", "client": "legacy-importer"}),
            (-72, "ERROR", "webhook-worker", "delivery.failed", "Webhook delivery exhausted retries after repeated HTTP 503 responses", "req_hook_731", {"endpoint": "https://client.example/webhooks", "status_code": 503, "attempts": 3, "customer": "org_meridian"}),
            (-86, "INFO", "reporting-api", "report.created", "Weekly operational report created", "req_rep_191", {"report_id": "rpt_previous"}),
            (-101, "WARN", "cache", "memory.pressure", "Redis memory usage exceeded 85%", "req_cache_301", {"memory_percent": 87.4, "evicted_keys": 193}),
            (-124, "ERROR", "payments-api", "upstream.timeout", "Payment provider timed out", "req_pay_601", {"provider": "demo-pay", "operation": "authorize", "timeout_ms": 5000}),
            (-151, "INFO", "auth-api", "credential.rotated", "Production API credential rotated", "req_auth_711", {"credential_id": "key_prod_05", "replaced": "key_prod_04"}),
            (-176, "WARN", "notifications-worker", "queue.lag", "Notification queue began accumulating faster than workers could process it", "req_notif_390", {"queue": "notifications.email", "pending": 904, "workers": 4}),
            (-220, "INFO", "database", "pool.normal", "Database pool utilization returned to normal after an earlier traffic spike", "req_db_702", {"utilization_percent": 58, "pool_size": 50}),
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
                "Database connection pool saturation is causing API failures",
                "database",
                -42,
                -4,
                73,
                "The database pool is saturated during the current traffic window, causing orders-api and api-gateway requests to wait for connections and eventually fail.",
                [
                    "connection pool reached 50/50 active connections",
                    "37 requests were waiting for a connection in the latest sample",
                    "POST /v1/orders returned 503 while db wait p95 exceeded 1.8s",
                ],
            ),
            (
                "open",
                "high",
                "Revoked production credential still configured in legacy importer",
                "auth-api",
                -67,
                -11,
                18,
                "The legacy importer is still sending requests with a credential revoked during the latest production key rotation.",
                [
                    "18 rejected requests in the current incident window",
                    "credential_id=key_prod_04 is revoked",
                    "replacement credential key_prod_05 is active",
                    "failed requests identify client=legacy-importer",
                ],
            ),
            (
                "monitoring",
                "medium",
                "Customer webhook endpoint is intermittently unavailable",
                "webhook-worker",
                -118,
                -15,
                11,
                "A customer webhook endpoint is intermittently returning HTTP 503 and causing retry exhaustion.",
                [
                    "11 failed delivery attempts were observed",
                    "failures are concentrated on org_meridian",
                    "all terminal failures returned HTTP 503",
                ],
            ),
            (
                "open",
                "medium",
                "Payment provider latency is causing authorization and capture timeouts",
                "payments-api",
                -132,
                -21,
                7,
                "The external payment provider has exceeded the five-second timeout on both authorization and capture operations.",
                [
                    "7 upstream timeouts in the incident window",
                    "authorize and capture operations are both affected",
                    "timeouts originate from provider=demo-pay",
                ],
            ),
            (
                "open",
                "medium",
                "Notification queue backlog is delaying outbound email",
                "notifications-worker",
                -181,
                -13,
                29,
                "Email notifications are accumulating because queue ingress is exceeding worker throughput and the provider has also returned HTTP 429 responses.",
                [
                    "1,834 messages pending in notifications.email",
                    "oldest queued message is more than four minutes old",
                    "mail provider returned HTTP 429 for a recent batch",
                ],
            ),
            (
                "monitoring",
                "medium",
                "Cache efficiency degradation is increasing backend load",
                "cache",
                -105,
                -31,
                14,
                "Redis hit rate dropped well below baseline while memory pressure and evictions increased, pushing more reads toward backend services and the database.",
                [
                    "cache hit rate dropped to 61.2% from a 91% baseline",
                    "482 evictions were observed in the last hour",
                    "Redis memory usage previously crossed 87%",
                ],
            ),
            (
                "monitoring",
                "low",
                "API request rate is approaching the configured plan limit",
                "api-gateway",
                -64,
                -18,
                6,
                "Traffic is repeatedly crossing the warning threshold and is close to the configured 500 requests-per-minute limit.",
                [
                    "latest observed rate is 472 requests per minute",
                    "configured limit is 500 requests per minute",
                    "no rate-limit rejection is present in the latest mock evidence",
                ],
            ),
            (
                "resolved",
                "low",
                "Transient invoice generation lock",
                "billing-api",
                -93,
                -38,
                2,
                "A transient database lock delayed invoice generation, but retry scheduling recovered the operation without manual intervention.",
                [
                    "invoice inv_demo_1842 was scheduled for retry",
                    "no subsequent terminal invoice failure was observed",
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
