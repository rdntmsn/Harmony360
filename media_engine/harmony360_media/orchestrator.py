from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from .core.harmony360_core import Harmony360
from .models import EpisodePackage
from .agents import (
    AudioAgent,
    CaptionAgent,
    ClaimGateAgent,
    EvidenceAgent,
    MediaLedger,
    MetadataAgent,
    NarrationAgent,
    PublicationGate,
    ResearchAgent,
    ScriptAgent,
    StoryboardAgent,
    VisualAgent,
    YouTubeAdapter,
)


class MediaOrchestrator(Harmony360):
    """Harmony360-native orchestration runtime for governed media generation."""

    def __init__(self, memory_dir: str | Path = './har360_output'):
        super().__init__(memory_dir=memory_dir)
        self.research = ResearchAgent(memory_dir=memory_dir)
        self.evidence = EvidenceAgent(memory_dir=memory_dir)
        self.script = ScriptAgent(memory_dir=memory_dir)
        self.claim_gate = ClaimGateAgent(memory_dir=memory_dir)
        self.storyboard = StoryboardAgent(memory_dir=memory_dir)
        self.visual = VisualAgent(memory_dir=memory_dir)
        self.narration = NarrationAgent(memory_dir=memory_dir)
        self.audio = AudioAgent(memory_dir=memory_dir)
        self.caption = CaptionAgent(memory_dir=memory_dir)
        self.metadata_agent = MetadataAgent(memory_dir=memory_dir)
        self.publication_gate = PublicationGate(memory_dir=memory_dir)
        self.youtube = YouTubeAdapter(memory_dir=memory_dir)
        self.ledger = MediaLedger(memory_dir=memory_dir)

    def create_episode(
        self,
        *,
        episode_id: str,
        series: str,
        topic: str,
        sources: Iterable[Dict[str, Any]],
        claims: Iterable[Dict[str, Any]],
        script: str,
        scenes: Iterable[Dict[str, Any]],
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> EpisodePackage:
        episode = EpisodePackage(episode_id=episode_id, series=series, topic=topic)
        self.research.resolve_sources(episode, sources)
        self.evidence.classify_claims(episode, claims)
        self.script.draft_script(episode, script)
        gate = self.claim_gate.validate_claims(episode)
        if not gate['approved']:
            return episode
        self.storyboard.build_storyboard(episode, scenes)
        self.metadata_agent.generate_metadata(
            episode,
            title=title or topic,
            description=description or f'{series} — {topic}',
        )
        episode.refresh_hashes()
        return episode
