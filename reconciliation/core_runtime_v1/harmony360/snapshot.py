from __future__ import annotations

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .core import Harmony360
from .serialization import canonical_json_bytes


class Harmony360Snapshot(Harmony360):
    """Versioned, integrity-checked Harmony360 state snapshots.

    Reconciles the historical v13 save/load/export/import snapshot semantics
    with deterministic hashing and explicit provenance fields.
    """

    FORMAT = "HARMONY360_SNAPSHOT"
    VERSION = "1.0"

    def save_state(
        self,
        module_state: dict[str, Any],
        label: str = "snapshot",
        *,
        source: str | None = None,
        lineage: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        state_hash = hashlib.sha256(canonical_json_bytes(module_state)).hexdigest()
        return {
            "format": self.FORMAT,
            "version": self.VERSION,
            "label": label,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "source": source,
            "lineage": lineage,
            "constants": {
                "phi": self.phi,
                "pi": self.pi,
                "alpha": self.alpha,
                "alpha_legacy": self.alpha_legacy,
                "planck_length_m": self.lp,
            },
            "metadata": metadata or {},
            "state_sha256": state_hash,
            "state": module_state,
        }

    # Historical naming compatibility.
    def save_snapshot(self, module_state: dict[str, Any], label: str = "snapshot") -> dict[str, Any]:
        return self.save_state(module_state, label=label)

    def validate_snapshot(self, snapshot_obj: dict[str, Any]) -> bool:
        if snapshot_obj.get("format") != self.FORMAT:
            return False
        if snapshot_obj.get("version") != self.VERSION:
            return False
        if "state" not in snapshot_obj or "state_sha256" not in snapshot_obj:
            return False
        actual = hashlib.sha256(canonical_json_bytes(snapshot_obj["state"])).hexdigest()
        return actual == snapshot_obj["state_sha256"]

    def load_state(self, snapshot_obj: dict[str, Any]) -> dict[str, Any]:
        if not self.validate_snapshot(snapshot_obj):
            raise ValueError("Invalid or tampered Harmony360 snapshot")
        return snapshot_obj["state"]

    def export_snapshot(self, snapshot: dict[str, Any], filename: str | Path) -> Path:
        if not self.validate_snapshot(snapshot):
            raise ValueError("Refusing to export invalid Harmony360 snapshot")
        path = Path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(snapshot, indent=2, sort_keys=True), encoding="utf-8")
        return path

    def import_snapshot(self, filename: str | Path) -> dict[str, Any]:
        snapshot = json.loads(Path(filename).read_text(encoding="utf-8"))
        if not self.validate_snapshot(snapshot):
            raise ValueError("Invalid or tampered Harmony360 snapshot")
        return snapshot

    def load_snapshot(self, snapshot_path: str | Path) -> dict[str, Any]:
        return self.load_state(self.import_snapshot(snapshot_path))

    def debug_snapshot_metadata(self, snapshot: dict[str, Any]) -> str:
        valid = self.validate_snapshot(snapshot)
        label = snapshot.get("label", "unknown")
        timestamp = snapshot.get("timestamp_utc", "unknown")
        keys = list(snapshot.get("state", {}).keys()) if isinstance(snapshot.get("state"), dict) else []
        return f"[Snapshot: {label}] @ {timestamp} | valid={valid} | keys={keys}"
