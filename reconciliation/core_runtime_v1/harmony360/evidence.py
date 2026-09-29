from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class EvidenceRecord:
    capability: str
    status: str
    scope_of_conclusion: str
    lineage: str
    details: dict[str, Any]
    run_id: str | None = None

    def finalize(self) -> dict[str, Any]:
        run_id = self.run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        body = {
            "run_id": run_id,
            "capability": self.capability,
            "status": self.status,
            "scope_of_conclusion": self.scope_of_conclusion,
            "lineage": self.lineage,
            "details": self.details,
        }
        canonical = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
        body["record_sha256"] = hashlib.sha256(canonical).hexdigest()
        return body

    def write(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.finalize(), indent=2, sort_keys=True), encoding="utf-8")
        return path
