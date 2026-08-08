from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AssetRecord:
    asset_id: str
    path: str
    name: str
    size_bytes: int
    sha256: str
    mime_type: str | None = None
    duplicate_of: str | None = None


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    asset_id: str
    locator: str
    content_sha256: str
    extraction_method: str
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LineageRecord:
    parent_id: str
    child_id: str
    relationship: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RuntimeResult:
    project_id: str
    project_root: Path
    assets: list[AssetRecord]
    evidence: list[EvidenceRecord]
    lineage: list[LineageRecord]
    blueprint: dict[str, Any]
    output_dir: Path
