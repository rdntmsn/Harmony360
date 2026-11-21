"""Transactional deduplication and an outbox; failed fetches cannot erase alerts."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from .changes import alert, normalize
from .jsonutil import canonical, digest, strict_loads, utcnow
from .sources import Snapshot


class BaselineRequired(RuntimeError):
    pass


class WatchStore:
    def __init__(self, path: str | Path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, timeout=30)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
          CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS seen(key TEXT PRIMARY KEY, fingerprint TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS outbox(
            id TEXT PRIMARY KEY, payload TEXT NOT NULL, created_at TEXT NOT NULL,
            delivered_at TEXT);
          CREATE TABLE IF NOT EXISTS checks(checked_at TEXT NOT NULL, change_count INTEGER NOT NULL);
        """)

    def close(self):
        self.db.close()

    def stage(self, snapshot: Snapshot, *, baseline: bool = False) -> list[dict]:
        changes = normalize(snapshot)  # Reject bad input before touching the state.
        try:
            self.db.execute("BEGIN IMMEDIATE")
            initialized = self.db.execute("SELECT value FROM metadata WHERE key='initialized'").fetchone()
            if baseline and initialized:
                raise BaselineRequired("Baseline already exists; resetting it could suppress undelivered changes")
            if not baseline and not initialized:
                raise BaselineRequired("Review current official advisories, then initialize with --baseline")
            for change in changes:
                previous = self.db.execute("SELECT fingerprint FROM seen WHERE key=?", (change.key,)).fetchone()
                if not baseline and (previous is None or previous[0] != change.fingerprint) and change.categories and not change.prerelease:
                    payload = alert(change)
                    payload["change_status"] = "NEW" if previous is None else "UPDATED"
                    alert_id = digest({"key": change.key, "fingerprint": change.fingerprint})
                    self.db.execute("INSERT OR IGNORE INTO outbox(id,payload,created_at) VALUES(?,?,?)",
                                    (alert_id, canonical(payload), utcnow()))
                self.db.execute("INSERT INTO seen VALUES(?,?) ON CONFLICT(key) DO UPDATE SET fingerprint=excluded.fingerprint",
                                (change.key, change.fingerprint))
            if baseline:
                self.db.execute("INSERT INTO metadata VALUES('initialized',?)", (snapshot.checked_at,))
            self.db.execute("INSERT INTO checks VALUES(?,?)", (snapshot.checked_at, len(changes)))
            self.db.commit()
        except BaseException:
            self.db.rollback()
            raise
        return self.pending()

    def pending(self) -> list[dict]:
        return [{"alert_id": row["id"], **strict_loads(row["payload"])} for row in self.db.execute(
            "SELECT id,payload FROM outbox WHERE delivered_at IS NULL ORDER BY created_at,id")]

    def acknowledge(self, ids: list[str]) -> None:
        with self.db:
            self.db.executemany("UPDATE outbox SET delivered_at=? WHERE id=? AND delivered_at IS NULL",
                                [(utcnow(), key) for key in ids])

