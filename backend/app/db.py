from __future__ import annotations
import json, sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator
from uuid import uuid4
from .config import Settings

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class Database:
    def __init__(self, settings: Settings) -> None:
        self.path = Path(settings.database_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

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
            db.executescript('''
            CREATE TABLE IF NOT EXISTS chat_sessions (
              id TEXT PRIMARY KEY, subject_key TEXT NOT NULL, surface_kind TEXT NOT NULL,
              surface_public_id TEXT NOT NULL, woobe_session_id TEXT NOT NULL UNIQUE,
              target_release_id TEXT, created_at TEXT NOT NULL, last_accessed_at TEXT NOT NULL,
              UNIQUE(subject_key, surface_kind, surface_public_id)
            );
            CREATE TABLE IF NOT EXISTS reports (
              id TEXT PRIMARY KEY, merchant_id TEXT NOT NULL, title TEXT NOT NULL,
              period_label TEXT NOT NULL, executive_summary TEXT NOT NULL,
              findings_json TEXT NOT NULL, recommendations_json TEXT NOT NULL,
              generated_by TEXT NOT NULL, created_at TEXT NOT NULL
            );
            ''')

    def get_chat_binding(self, subject_key: str, surface_kind: str, surface_public_id: str):
        with self.connect() as db:
            row = db.execute('SELECT * FROM chat_sessions WHERE subject_key=? AND surface_kind=? AND surface_public_id=? LIMIT 1', (subject_key, surface_kind, surface_public_id)).fetchone()
            if row:
                db.execute('UPDATE chat_sessions SET last_accessed_at=? WHERE id=?', (now_iso(), row['id']))
            return row

    def save_chat_binding(self, *, subject_key: str, surface_kind: str, surface_public_id: str, woobe_session_id: str, target_release_id: str | None) -> str:
        binding_id = f"bind_{uuid4().hex[:12]}"
        stamp = now_iso()
        with self.connect() as db:
            db.execute('INSERT INTO chat_sessions(id,subject_key,surface_kind,surface_public_id,woobe_session_id,target_release_id,created_at,last_accessed_at) VALUES (?,?,?,?,?,?,?,?)', (binding_id,subject_key,surface_kind,surface_public_id,woobe_session_id,target_release_id,stamp,stamp))
        return binding_id

    def create_report(self, *, merchant_id: str, title: str, period_label: str, executive_summary: str, findings: list[str], recommendations: list[str]) -> dict:
        report_id = f"rpt_{uuid4().hex[:12]}"
        stamp = now_iso()
        with self.connect() as db:
            db.execute('INSERT INTO reports(id,merchant_id,title,period_label,executive_summary,findings_json,recommendations_json,generated_by,created_at) VALUES (?,?,?,?,?,?,?,?,?)', (report_id,merchant_id,title,period_label,executive_summary,json.dumps(findings),json.dumps(recommendations),'mercury-merchant-assistant',stamp))
        return {'id':report_id,'title':title,'period_label':period_label,'executive_summary':executive_summary,'findings':findings,'recommendations':recommendations,'generated_by':'mercury-merchant-assistant','created_at':stamp}

    def list_reports(self, merchant_id: str) -> list[dict]:
        with self.connect() as db:
            rows = db.execute('SELECT * FROM reports WHERE merchant_id=? ORDER BY created_at DESC', (merchant_id,)).fetchall()
        return [{**dict(r),'findings':json.loads(r['findings_json']),'recommendations':json.loads(r['recommendations_json'])} for r in rows]
