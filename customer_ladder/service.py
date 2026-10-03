from __future__ import annotations

from .models import Blueprint, CustomerIntake
from .qualification import qualify


def build_blueprint(intake: CustomerIntake) -> Blueprint:
    """Convert a lightweight intake into an inspectable Signal-to-System Blueprint."""
    tier, rationale = qualify(intake)

    manifested = (
        f"{intake.asset_count} known assets across "
        f"{len(intake.source_locations)} source location(s)."
    )
    reference = f"A reconciled, usable system supporting: {intake.goal}"

    divergences = list(intake.conflicts)
    if not intake.source_locations:
        divergences.append("Source material has not yet been located or bounded.")
    if not intake.recurring_themes:
        divergences.append("Recurring signals have not yet been identified.")

    connections = [
        f"Theme: {theme}" for theme in intake.recurring_themes
    ] + [f"Opportunity: {item}" for item in intake.opportunities]

    recl_actions = []
    if divergences:
        recl_actions.append("Reconcile the highest-impact divergence against source evidence.")
    recl_actions.append("Promote supported signals into the working blueprint.")
    recl_actions.append("Archive or quarantine unsupported/duplicate material rather than silently deleting it.")

    return Blueprint(
        manifested_state=manifested,
        reference_state=reference,
        divergences=divergences,
        connections=connections,
        recl_actions=recl_actions,
        opportunities=intake.opportunities,
        recommended_tier=tier,
        rationale=rationale,
    )
