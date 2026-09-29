from __future__ import annotations

import functools
import hashlib
from pathlib import Path
from typing import Callable, Any

from .snapshot import Harmony360Snapshot
from .ledger import HAR360LedgerManager
from .serialization import canonical_json_bytes


def h360_sync(
    snapshot_dir: str | Path,
    ledger_path: str | Path,
    *,
    snapshot_type: str = "general",
    notes: str = "Harmony360 operation",
    lineage: str | None = None,
):
    """Persist a verified snapshot and append its hash to the HAR360 ledger.

    Reconciles the historical decorator behavior with explicit integrity,
    provenance, and an append-only ledger chain.
    """
    snapshot_dir = Path(snapshot_dir)
    ledger_path = Path(ledger_path)

    def decorator(func: Callable[..., Any]):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            snapper = Harmony360Snapshot()
            snapshot = snapper.save_state(
                {"result": result},
                label=func.__name__,
                source=func.__qualname__,
                lineage=lineage,
                metadata={"snapshot_type": snapshot_type, "notes": notes},
            )
            snapshot_dir.mkdir(parents=True, exist_ok=True)
            stamp = snapshot["timestamp_utc"].replace(":", "").replace("+00:00", "Z")
            path = snapshot_dir / f"{func.__name__}_{stamp}.har360.json"
            snapper.export_snapshot(snapshot, path)

            artifact_bytes = path.read_bytes()
            artifact_sha256 = hashlib.sha256(artifact_bytes).hexdigest()
            ledger = HAR360LedgerManager(ledger_path)
            ledger.append_entry(
                event_type="SNAPSHOT_WRITTEN",
                artifact_id=path.name,
                artifact_sha256=artifact_sha256,
                status="PASS",
                lineage=lineage,
                metadata={"snapshot_type": snapshot_type, "source": func.__qualname__},
            )
            return result

        return wrapper

    return decorator
