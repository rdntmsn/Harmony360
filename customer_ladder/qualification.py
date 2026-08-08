from __future__ import annotations

from .models import CustomerIntake, OfferTier


def qualify(intake: CustomerIntake) -> tuple[OfferTier, list[str]]:
    """Deterministic v0.1 routing. Keep pricing logic inspectable and testable."""
    reasons: list[str] = []

    if intake.team_size > 1 or intake.needs_automation or intake.needs_governance:
        reasons.append("Team, automation, or governance needs exceed a one-off blueprint.")
        return OfferTier.ENTERPRISE, reasons

    if intake.asset_count >= 250 or len(intake.opportunities) >= 2 or len(intake.conflicts) >= 4:
        reasons.append("The archive contains enough scale, conflict, or opportunity for productization.")
        return OfferTier.GROWTH, reasons

    if intake.asset_count >= 25 or intake.conflicts or intake.source_locations:
        reasons.append("A real source set exists and benefits from deeper Harmony360 archaeology.")
        return OfferTier.STARTER, reasons

    reasons.append("The scope is small enough for a self-directed first pass.")
    return OfferTier.DIY, reasons
