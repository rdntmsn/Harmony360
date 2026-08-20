# Harmony360 Governed Market Platform — Design Spike

Status: implementation candidate; paper trading only.

This package turns the recovered Harmony360QES and FractalSeer concepts into a testable market-research and paper-execution architecture. It does not claim verified predictive edge, canonical authority, or live-capital readiness.

## Fast review

1. Read `COPY_PASTE_REVIEW.md`.
2. Review `DESIGN_AND_ROADMAP.md`.
3. Use `COLAB_MOBILE_PROTOCOL.md` when generating the implementation notebook.
4. Promote Harmony-derived features only after the stated evidence gates pass.

## Non-negotiable boundaries

- A model creates a `SignalAssessment`; it never calls a broker.
- Guardian converts or rejects proposed signals before an `OrderIntent` exists.
- Only a broker adapter creates a `BrokerOrder`.
- Paper mode is the default and live mode requires explicit human promotion.
- Baseline strategies and Harmony-derived experimental features remain separately measurable.
- Every stage emits concise status, elapsed time, counts, warnings, and a resumable checkpoint.

## Package contents

- `DESIGN_AND_ROADMAP.md` — architecture, build phases, risks, and promotion gates
- `COLAB_MOBILE_PROTOCOL.md` — phone-first notebook and progress-reporting contract
- `COPY_PASTE_REVIEW.md` — compact immediate-review version
- `SOURCE_CLASSIFICATION.json` — governed classification of the reviewed sources
- `HARMONY360_MARKET_PLATFORM.har360.json` — package manifest
- `Harmony360_Governed_Market_Platform_v0_2.ipynb` — runnable recovery, baseline, spectral-feature, walk-forward, and governed-export Colab
