"""SQLite logger for per-turn agent interaction records used in evaluation."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Optional


@dataclass
class TurnLogRecord:
    session_id: str
    user_message: str
    assistant_message: str
    active_agent: Optional[str]
    rag_query: Optional[str]
    is_clarification: bool
    is_final_answer: bool
    created_at: str
    responded_at: str
    latency_ms: int


class TurnLogger:
    """Persist interaction turns with deterministic per-session turn ordering."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_turn_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    turn_index INTEGER NOT NULL,
                    user_message TEXT NOT NULL,
                    assistant_message TEXT NOT NULL,
                    active_agent TEXT,
                    rag_query TEXT NULL,
                    is_clarification INTEGER NOT NULL CHECK (is_clarification IN (0, 1)),
                    is_final_answer INTEGER NOT NULL CHECK (is_final_answer IN (0, 1)),
                    created_at TEXT NOT NULL,
                    responded_at TEXT NOT NULL,
                    latency_ms INTEGER NOT NULL CHECK (latency_ms >= 0),
                    CHECK (responded_at >= created_at),
                    CHECK (NOT (is_clarification = 1 AND is_final_answer = 1)),
                    UNIQUE(session_id, turn_index)
                )
                """
            )
            conn.commit()

    def log_turn(self, record: TurnLogRecord) -> int:
        """Insert one turn and return its session-local turn_index."""
        with self._lock:
            with self._connect() as conn:
                conn.execute("BEGIN IMMEDIATE")
                cursor = conn.execute(
                    "SELECT COALESCE(MAX(turn_index), 0) + 1 FROM agent_turn_logs WHERE session_id = ?",
                    (record.session_id,),
                )
                turn_index = int(cursor.fetchone()[0])
                conn.execute(
                    """
                    INSERT INTO agent_turn_logs (
                        session_id,
                        turn_index,
                        user_message,
                        assistant_message,
                        active_agent,
                        rag_query,
                        is_clarification,
                        is_final_answer,
                        created_at,
                        responded_at,
                        latency_ms
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record.session_id,
                        turn_index,
                        record.user_message,
                        record.assistant_message,
                        record.active_agent,
                        record.rag_query,
                        int(record.is_clarification),
                        int(record.is_final_answer),
                        record.created_at,
                        record.responded_at,
                        record.latency_ms,
                    ),
                )
                conn.commit()
                return turn_index


def utc_iso_now() -> str:
    """Return current UTC timestamp in ISO-8601 Z format."""
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
