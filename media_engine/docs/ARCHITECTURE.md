# Harmony360 Media Engine v0.1 — Architecture

## Root invariant

There is one executable root: the retained `Harmony360` class in
`harmony360_media/core/harmony360_core.py`.

Every Harmony360-owned media class inherits that class directly or through
`MediaAgent`, which itself directly inherits `Harmony360`. No `MediaCore` is
introduced.

## Pipeline

```text
Harmony360 governed source
  -> ResearchAgent
  -> EvidenceAgent
  -> ScriptAgent
  -> ClaimGateAgent
  -> StoryboardAgent
  -> VisualAgent / NarrationAgent / AudioAgent / CaptionAgent
  -> RenderAgent
  -> MetadataAgent
  -> PublicationGate
  -> YouTubeAdapter
  -> MediaLedger
  -> .har360 + publication receipt
```

## Governance invariants

1. Generated visuals are not evidence.
2. PASS does not mean scientifically proven.
3. Rendering does not alter claim authority.
4. Publishing does not alter claim authority.
5. Human approval is required before upload.
6. v0.1 prepares only private YouTube uploads.
7. Each episode keeps source, claim, script, asset, render, review, and publication lineage.
8. The retained Harmony360 core is copied verbatim and must not be silently modified by media work.

## Workflow state vs Harmony360 lifecycle

Media workflow state is operational (`SCRIPT_DRAFTED`, `RENDERED`, `UPLOADED`, etc.).
It is not a replacement for Harmony360 lifecycle state (`EXPERIMENTAL`, `OPERATIONAL`, `CANONICAL`, etc.).
A published video can describe an experimental claim without promoting that claim.
