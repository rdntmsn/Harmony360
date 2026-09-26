from harmony360_media.core.harmony360_core import Harmony360
from harmony360_media.orchestrator import MediaOrchestrator
from harmony360_media.agents import (
    ResearchAgent, EvidenceAgent, ScriptAgent, ClaimGateAgent, StoryboardAgent,
    VisualAgent, NarrationAgent, AudioAgent, CaptionAgent, RenderAgent,
    MetadataAgent, PublicationGate, YouTubeAdapter, MediaLedger,
)

MEDIA_CLASSES = [
    MediaOrchestrator, ResearchAgent, EvidenceAgent, ScriptAgent, ClaimGateAgent,
    StoryboardAgent, VisualAgent, NarrationAgent, AudioAgent, CaptionAgent,
    RenderAgent, MetadataAgent, PublicationGate, YouTubeAdapter, MediaLedger,
]


def test_every_media_class_inherits_harmony360_core():
    for cls in MEDIA_CLASSES:
        assert issubclass(cls, Harmony360), cls.__name__
