"""Harmony360 Media Engine v0.1.

Every executable Harmony360-owned media class inherits the retained Harmony360
core class. The package does not redefine or replace the core.
"""
from .core.harmony360_core import Harmony360
from .models import EpisodePackage, SourceArtifact, ClaimRecord, SceneRecord
from .orchestrator import MediaOrchestrator

__version__ = '0.1.0'
__all__ = ['Harmony360', 'EpisodePackage', 'SourceArtifact', 'ClaimRecord', 'SceneRecord', 'MediaOrchestrator']
