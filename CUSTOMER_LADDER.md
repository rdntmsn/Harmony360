# Harmony360 Customer Ladder v0.1

This is the first executable bridge between Harmony360 content, the $27 DIY product, and the existing service ladder.

```text
Recognition content
  -> $27 Signal-to-System Starter Kit
  -> $199 Starter Blueprint
  -> $499 Growth Blueprint
  -> Custom Enterprise
```

## What the code does now

1. Captures the facts the DIY customer discovers: goal, source locations, asset count, themes, conflicts, opportunities, team and governance needs.
2. Produces a small Signal-to-System Blueprint using the Harmony360 pattern:

```text
Manifested state
  -> Reference state
  -> Divergences
  -> Connections
  -> RECL actions
  -> Opportunity map
```

3. Recommends the next product tier with deterministic, inspectable rules.
4. Exposes the flow as a small FastAPI service.

## Run locally

```bash
pip install fastapi uvicorn pydantic pytest
uvicorn customer_ladder.api:app --reload
```

Then POST to `/blueprint`:

```json
{
  "goal": "Turn my scattered research into a product",
  "source_locations": ["Google Drive", "Chat exports"],
  "asset_count": 85,
  "recurring_themes": ["knowledge recovery", "decision lineage"],
  "conflicts": ["two competing product definitions"],
  "opportunities": ["DIY kit"]
}
```

## Product architecture

The $27 kit is not merely a PDF. It is the human-facing intake and first-pass reasoning layer for this runtime. A later web form can submit the completed workbook to this API, generate a saved blueprint, and route qualified customers into the appropriate service.

The $199 layer should next add actual archive intake, hashing, extraction, evidence records, duplicate detection, and governed blueprint generation. The $499 layer can add cross-source reconciliation, product/offer modeling, roadmap generation, and deeper opportunity analysis. Enterprise should connect those same primitives to persistent ingestion, teams, evidence/decision lineage, automation, and the broader Harmony360 governed runtime.

## Next engineering increment

- persist intake and blueprint records
- add evidence records and source references
- generate a portable `.har360` customer blueprint artifact
- connect checkout/intake IDs without storing payment data
- add archive upload as a separate governed boundary
- add explicit human approval before any tier recommendation becomes an operational sales action
