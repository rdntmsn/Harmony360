from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def save_har360(payload: Any, path: str | Path, metadata: dict | None = None) -> Path:
    """Serialize a governed Harmony360 envelope. This is serialization, not encryption."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload_bytes = canonical_json_bytes(payload)
    envelope = {
        "format": "HAR360",
        "version": "1.0",
        "metadata": metadata or {},
        "payload_sha256": sha256_hex(payload_bytes),
        "payload": payload,
    }
    path.write_text(json.dumps(envelope, indent=2, sort_keys=True), encoding="utf-8")
    return path


def load_har360(path: str | Path) -> Any:
    envelope = json.loads(Path(path).read_text(encoding="utf-8"))
    if envelope.get("format") != "HAR360":
        raise ValueError("Not a HAR360 envelope")
    payload = envelope["payload"]
    expected = envelope["payload_sha256"]
    actual = sha256_hex(canonical_json_bytes(payload))
    if actual != expected:
        raise ValueError("HAR360 payload integrity mismatch")
    return payload
