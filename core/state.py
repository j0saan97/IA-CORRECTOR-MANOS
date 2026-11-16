"""SQLite (state.db) con las capturas ya procesadas, para no repetir."""
import sqlite3
from datetime import datetime
from pathlib import Path

from config import settings


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.STATE_DB)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS processed (
               path TEXT PRIMARY KEY,
               hand_no TEXT,
               status TEXT,
               message TEXT,
               processed_at TEXT)"""
    )
    return conn


def is_processed(path: Path) -> bool:
    with _conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM processed WHERE path = ? AND status = 'ok'", (str(path),)
        ).fetchone()
    return row is not None


def mark(path: Path, hand_no: str | None, status: str, message: str = "") -> None:
    with _conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO processed VALUES (?, ?, ?, ?, ?)",
            (str(path), hand_no, status, message, datetime.now().isoformat(timespec="seconds")),
        )
