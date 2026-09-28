# Harmony360 Market Dynamics Laboratory (HMDL) v0.1

Historical-data research foundation. This branch is **EXPERIMENTAL** and does not modify or claim to integrate a verified Harmony360Core implementation. It is a domain adapter with explicit receipts and a human governance boundary.

## Colab

Open `notebooks/HMDL_v0_1_Foundation.ipynb` in Colab and run the cells in order. The notebook includes its own source code and writes to `/content/drive/MyDrive/HAR360_MASTER/hmdl/runs` when Drive is mounted; otherwise it writes to `/content/hmdl/runs`. Set `CSV_PATH` to a file with `Date` and `Close` or `Adj Close` to avoid a market download. With no CSV it requests SPY daily prices through yfinance. Uploading a CSV does not establish its provenance.

## Python

```bash
python -m pip install -r hmdl/requirements.txt
python hmdl/hmdl.py --csv path/to/daily_prices.csv --output ./runs
# or omit --csv to fetch SPY for research
```

Output contains raw and normalized CSV, DuckDB observations/features/evidence tables, baseline metrics, and a `.har360.json` record with SHA-256 receipts and lineage. `verify(run_directory)` checks the record and artifact hashes. The raw receipt verifies bytes; it does not verify whether the data provider was correct.

The baseline comparison includes buy-and-hold, 50/200 moving averages, 20-session momentum and 20-session mean reversion. Signals use only information through close t and the resulting position applies to t+1. Two basis points per position change are charged by default. The first 200 sessions warm up the features; this run does not perform an out-of-sample claim. No signal, order or broker interface exists.

## Lineage and scope

Parent research run: `20260820T012723Z`, [Governed Market Platform report](https://drive.google.com/file/d/1jWLJRzP53709v-K2P7-6hScX43j-WQ9n/view). That run compared SPY moving-average baselines and experimental FFT/wavelet features, but did not establish predictive validation. This foundation records it as a parent reference, without claiming byte-level derivation from its dataset or using its results as a benchmark for this new sample.

The Core v1.0 specification remains under review, and the later v1.1 integration spike reported a failed technical gate. This module does not call either draft Core interface. An eventual integration requires source receipts, interface verification, human review and explicit promotion.

Next experiment HMDL-001: specify and test multiscale coherence against conventional volatility and momentum controls using walk-forward partitions and feature ablation. That work is not in v0.1.

## Limits

Yahoo data is for research and may be revised; corporate action and point-in-time integrity are not independently certified. A local CSV may be from any source. Daily close execution, transaction costs and the zero-risk-free-rate Sharpe are simplified. Results confer no predictive edge, canonical status or trading authorization.
