from __future__ import annotations

from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class OfferTier(str, Enum):
    DIY = "diy_27"
    STARTER = "starter_199"
    GROWTH = "growth_499"
    ENTERPRISE = "enterprise_custom"


class CustomerIntake(BaseModel):
    """What a prospect tells Harmony360 after the DIY signal scan."""

    goal: str = Field(min_length=3)
    source_locations: List[str] = Field(default_factory=list)
    asset_count: int = Field(default=0, ge=0)
    recurring_themes: List[str] = Field(default_factory=list)
    conflicts: List[str] = Field(default_factory=list)
    opportunities: List[str] = Field(default_factory=list)
    team_size: int = Field(default=1, ge=1)
    needs_automation: bool = False
    needs_governance: bool = False


class Blueprint(BaseModel):
    manifested_state: str
    reference_state: str
    divergences: List[str]
    connections: List[str]
    recl_actions: List[str]
    opportunities: List[str]
    recommended_tier: OfferTier
    rationale: List[str]
