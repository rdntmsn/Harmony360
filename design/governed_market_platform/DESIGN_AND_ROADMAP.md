# Harmony360 Governed Market Platform

## Governing conclusion

Harmony360 already contains a meaningful financial research architecture in QES, FractalSeer, Guardian, TLN369, MarketState and PortfolioState materials. The conventional trading roadmap supplies missing data, validation and execution infrastructure. These bodies of work should be integrated through explicit interfaces—not blended into an opaque trading bot.

## Proposed topology

```text
Market feeds
  -> immutable raw events and evidence receipts
  -> normalized bars/features
  -> baseline strategy lane + Harmony experimental lane
  -> signal adjudication
  -> deterministic Guardian risk gate
  -> order-intent ledger
  -> paper broker adapter
  -> acknowledgements/fills/reconciliation
  -> decision, evidence and lineage records
```

## Required domain boundaries

### SignalAssessment

Analytical output only: instrument, horizon, direction, probability/confidence, feature versions, source timestamps, model identity, experimental classification and evidence references.

### OrderIntent

A deterministic portfolio proposal created only after signal adjudication: target exposure, quantity/notional ceiling, limit/stop rules, expiry, risk checks and idempotency key.

### BrokerOrder

The broker-specific request and lifecycle: submitted, acknowledged, partially filled, filled, cancelled, rejected or reconciliation-required.

No analytical model may create or submit BrokerOrder directly.

## Two strategy lanes

### Operational baselines

- Buy-and-hold
- Moving-average momentum
- Mean reversion
- Volatility targeting
- Conventional indicator references

### Harmony experimental lane

- Actual continuous-wavelet features
- FFT spectral features
- Micro/meso/macro 3-6-9 horizons
- TLN phase classification
- Market coherence
- Fractal/resonance candidates

Every Harmony feature must be individually ablated and compared with baselines. Narrative plausibility is not evidence of edge.

## Initial stack

- Python domain package with framework-independent logic
- FastAPI at the service boundary
- PostgreSQL as production authority
- SQLite permitted for local-development parity
- Immutable Parquet market-data partitions
- DuckDB as a derived research/query sidecar only
- vectorbt for rapid research
- event-driven execution simulator for fills and order lifecycles
- Alpaca paper adapter first
- IBKR or other brokers only through later replaceable adapters

## Guardian controls

- per-order and per-position notional caps
- symbol, sector, gross, net and leverage exposure limits
- daily loss and portfolio drawdown halts
- stale-data and disconnected-feed rejection
- spread, liquidity and price-deviation limits
- deterministic client order IDs and duplicate rejection
- rate and burst limits
- market-hours and corporate-action awareness
- partial-fill, cancel/replace and restart reconciliation
- separate paper/live credentials
- independent kill switch and cancel-on-disconnect policy

## Evidence and research controls

- point-in-time datasets
- corporate-action adjustments with recorded methodology
- survivorship-bias controls
- strict train/validation/test separation
- walk-forward and out-of-sample evaluation
- transaction costs, spread, slippage and partial fills
- multiple market regimes
- parameter-search disclosure
- baseline comparisons and ablation studies
- reproducible seeds, environment locks and dataset hashes

## Build phases

### Phase 0 — estate recovery

Recover the exact FractalSeerDivision, GuardianDivision, TLN369, Harmony360, MarketState and PortfolioState implementations from Drive and GitHub. Hash inputs and classify each artifact. Output a source map and executable tests. Do not scan the full Drive recursively during normal runs.

### Phase 1 — deterministic research core

Implement one instrument (SPY), daily bars, immutable ingestion, baseline strategies, cost-aware backtests and reproducible reports.

Exit gate: repeatable results, no look-ahead leakage, dataset receipts and baseline metrics.

### Phase 2 — Harmony feature evaluation

Add wavelet, FFT, triadic horizons, TLN phase and coherence as isolated feature modules.

Exit gate: walk-forward improvement over baselines across multiple regimes, successful ablations and no unsupported claims.

### Phase 3 — paper execution

Add signal adjudication, Guardian gates, order-intent ledger, Alpaca paper adapter, streaming updates and reconciliation.

Exit gate: no duplicate orders across retries/restarts and complete audit reconstruction.

### Phase 4 — resilience

Test stale feeds, disconnects, timeouts, partial fills, broker rejections, process restarts, clock drift and database recovery.

Exit gate: bounded failure, effective kill switch and deterministic recovery.

### Phase 5 — governed promotion

Only after a sustained paper record and human review may a tiny, bounded live pilot be proposed. Live operation is not authorized by this design package.

## Immediate sprint

1. Extract the named QES/FractalSeer code blocks from the v10-v13 estate.
2. Create typed contracts for SignalAssessment, OrderIntent and BrokerOrder.
3. Build SPY daily-bar ingestion with hash receipts.
4. Implement buy-and-hold and moving-average baselines.
5. Replace placeholder Fourier/wavelet functions with real tested implementations.
6. Produce one walk-forward report with costs and ablations.
7. Stop before broker integration until the research report passes review.

## Current maturity

- Financial architecture: promising
- Recoverable implementation: meaningful
- Predictive edge: not demonstrated
- Paper-execution readiness: requires engineering
- Live-capital readiness: not established

