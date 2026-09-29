from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .core import Harmony360


class HAR360LedgerManager(Harmony360):
    """Append-only Harmony360 ledger index with hash chaining.

    This implements the historical load/export intent as a real ledger:
    each entry binds to the previous entry hash and can be verified later.
    """

    FORMAT = "HAR360_LEDGER"
    VERSION = "1.0"

    def __init__(self, ledger_path: str | Path):
        super().__init__()
        self.ledger_path = Path(ledger_path)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.ledger_path.exists():
            self.ledger_path.write_text("", encoding="utf-8")

    @staticmethod
    def _canonical(entry: dict[str, Any]) -> bytes:
        return json.dumps(entry, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

    @classmethod
    def _entry_hash(cls, entry_without_hash: dict[str, Any]) -> str:
        return hashlib.sha256(cls._canonical(entry_without_hash)).hexdigest()

    def load_ledger_index(self) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        for line in self.ledger_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                entries.append(json.loads(line))
        return entries

    def append_entry(
        self,
        *,
        event_type: str,
        artifact_id: str,
        artifact_sha256: str,
        status: str,
        lineage: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        entries = self.load_ledger_index()
        previous_hash = entries[-1]["entry_sha256"] if entries else None
        body = {
            "format": self.FORMAT,
            "version": self.VERSION,
            "sequence": len(entries) + 1,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "artifact_id": artifact_id,
            "artifact_sha256": artifact_sha256,
            "status": status,
            "lineage": lineage,
            "metadata": metadata or {},
            "previous_entry_sha256": previous_hash,
        }
        entry = dict(body)
        entry["entry_sha256"] = self._entry_hash(body)
        with self.ledger_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, sort_keys=True) + "\n")
        return entry

    def verify_chain(self) -> dict[str, Any]:
        entries = self.load_ledger_index()
        previous_hash = None
        for expected_sequence, entry in enumerate(entries, start=1):
            if entry.get("sequence") != expected_sequence:
                return {"valid": False, "reason": "sequence_mismatch", "sequence": expected_sequence}
            if entry.get("previous_entry_sha256") != previous_hash:
                return {"valid": False, "reason": "previous_hash_mismatch", "sequence": expected_sequence}
            recorded = entry.get("entry_sha256")
            body = dict(entry)
            body.pop("entry_sha256", None)
            actual = self._entry_hash(body)
            if actual != recorded:
                return {"valid": False, "reason": "entry_hash_mismatch", "sequence": expected_sequence}
            previous_hash = recorded
        return {"valid": True, "entries": len(entries), "head_sha256": previous_hash}

    def export_ledger_snapshot(self, destination: str | Path) -> Path:
        verification = self.verify_chain()
        if not verification["valid"]:
            raise ValueError(f"Ledger verification failed: {verification}")
        payload = {
            "format": self.FORMAT,
            "version": self.VERSION,
            "exported_utc": datetime.now(timezone.utc).isoformat(),
            "verification": verification,
            "entries": self.load_ledger_index(),
        }
        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return path
