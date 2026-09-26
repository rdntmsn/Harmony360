from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import hashlib
import json


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def sha256_json(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


@dataclass
class SourceArtifact:
    source_id: str
    title: str
    source_type: str
    uri: Optional[str] = None
    content_hash: Optional[str] = None
    classification: str = 'DISCOVERED'
    notes: Optional[str] = None


@dataclass
class ClaimRecord:
    claim_id: str
    statement: str
    claim_class: str
    status: str = 'UNREVIEWED'
    evidence_ids: List[str] = field(default_factory=list)
    uncertainty: Optional[str] = None


@dataclass
class SceneRecord:
    scene_id: str
    order: int
    narration: str
    visual_prompt: str
    duration_seconds: float
    visual_type: str = 'generated_visualization'
    evidence_visual: bool = False
    asset_path: Optional[str] = None


@dataclass
class ReviewRecord:
    reviewer: str
    decision: str
    reviewed_at: str = field(default_factory=utc_now)
    notes: str = ''


@dataclass
class PublicationReceipt:
    provider: str
    external_id: Optional[str] = None
    url: Optional[str] = None
    privacy_state: str = 'private'
    published_at: Optional[str] = None
    status: str = 'NOT_UPLOADED'


@dataclass
class EpisodePackage:
    episode_id: str
    series: str
    topic: str
    created_at: str = field(default_factory=utc_now)
    lifecycle: str = 'UNDER_REVIEW'
    workflow_state: str = 'DISCOVERED'
    sources: List[SourceArtifact] = field(default_factory=list)
    claims: List[ClaimRecord] = field(default_factory=list)
    script: str = ''
    scenes: List[SceneRecord] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    review: Optional[ReviewRecord] = None
    publication: Optional[PublicationReceipt] = None
    hashes: Dict[str, str] = field(default_factory=dict)
    lineage: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def refresh_hashes(self) -> Dict[str, str]:
        self.hashes['package'] = sha256_json({
            'episode_id': self.episode_id,
            'series': self.series,
            'topic': self.topic,
            'sources': [asdict(s) for s in self.sources],
            'claims': [asdict(c) for c in self.claims],
            'script': self.script,
            'scenes': [asdict(s) for s in self.scenes],
            'metadata': self.metadata,
            'workflow_state': self.workflow_state,
            'lifecycle': self.lifecycle,
        })
        if self.script:
            self.hashes['script'] = hashlib.sha256(self.script.encode('utf-8')).hexdigest()
        return self.hashes
