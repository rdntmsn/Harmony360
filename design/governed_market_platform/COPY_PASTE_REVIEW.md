# Immediate Review — Harmony360 Market Platform

Decision: build a governed market-research and paper-trading platform around Harmony360QES and FractalSeer, but do not let analytical models submit orders.

Architecture:

Market data -> immutable evidence -> normalized features -> baseline and Harmony experimental strategies -> adjudication -> Guardian risk gate -> order-intent ledger -> paper broker -> fills/reconciliation -> audit record.

First build:

- SPY only
- daily bars
- vectorized research plus an event-driven execution simulator
- PostgreSQL authority, SQLite local development, Parquet data and optional DuckDB queries
- Alpaca paper trading only after backtest validation

Harmony-derived features remain experimental:

- wavelets and FFT
- 3-6-9 horizons
- TLN phase
- coherence and fractal/resonance candidates

Promotion requires:

- real implementations rather than placeholders
- walk-forward out-of-sample testing
- transaction costs and slippage
- baseline comparison and ablation
- reproducibility and source hashes
- deterministic risk gates
- restart-safe idempotency and reconciliation
- sustained paper performance
- explicit human approval

Phone-first requirements:

- multiple short cells instead of one long cell
- progress every ten seconds
- counts, elapsed time, shortened current path and warnings
- quick/standard/full modes
- explicit Drive roots
- cached receipts and resumable checkpoints
- full-estate scanning disabled by default
- ZIP, Drive document, GitHub branch and end-of-run summary

Current verdict:

Harmony360 has a serious research/governance foundation, but verified predictive edge and live-capital readiness have not yet been demonstrated. Recover the real v10-v13 implementations, establish deterministic baselines, and make the Harmony features earn promotion experimentally.

#harmonygoats #bleat

