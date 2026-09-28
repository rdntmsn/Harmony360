"""Harmony360 Market Dynamics Laboratory v0.1: historical research only.

This is a domain adapter. It neither imports nor modifies Harmony360Core and
does not claim a canonical Core integration.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pandas as pd

VERSION = "0.1.0"
PARENT_RUN = "20260820T012723Z"
SOURCE_REPORT = "https://drive.google.com/file/d/1jWLJRzP53709v-K2P7-6hScX43j-WQ9n/view"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_bytes(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def load_csv(path: str | Path) -> tuple[pd.DataFrame, bytes]:
    raw = Path(path).read_bytes()
    frame = pd.read_csv(path)
    return normalize(frame), raw


def download_spy(start="2010-01-01", end=None) -> tuple[pd.DataFrame, bytes]:
    """Fetch research-grade Yahoo data; network and provider availability vary."""
    import yfinance as yf

    end = end or datetime.now(timezone.utc).date().isoformat()
    data = yf.download("SPY", start=start, end=end, auto_adjust=True,
                       progress=False, multi_level_index=False)
    if data.empty:
        raise ValueError("No SPY data returned; supply a dated CSV instead")
    data = data.reset_index()
    raw = data.to_csv(index=False, float_format="%.12g").encode()
    return normalize(data), raw


def normalize(data: pd.DataFrame) -> pd.DataFrame:
    cols = {str(c).strip().lower(): c for c in data.columns}
    date_key = cols.get("date") or cols.get("datetime")
    price_key = cols.get("adj close") or cols.get("close")
    if date_key is None or price_key is None:
        raise ValueError("CSV needs Date and Close (or Adj Close) columns")
    result = pd.DataFrame({"date": pd.to_datetime(data[date_key], utc=True, errors="raise"),
                           "close": pd.to_numeric(data[price_key], errors="raise")})
    if result.date.isna().any() or result.close.isna().any() or not (result.close > 0).all():
        raise ValueError("Dates and strictly positive prices are required")
    result = result.sort_values("date").reset_index(drop=True)
    if result.date.duplicated().any() or len(result) < 252:
        raise ValueError("Require 252+ distinct, dated observations")
    return result


def features(data: pd.DataFrame) -> pd.DataFrame:
    frame = data.copy()
    frame["return"] = frame.close.pct_change()
    frame["sma50"] = frame.close.rolling(50, min_periods=50).mean()
    frame["sma200"] = frame.close.rolling(200, min_periods=200).mean()
    frame["momentum20"] = frame.close.pct_change(20)
    frame["volatility20"] = frame["return"].rolling(20).std()
    # End-of-day information only. All positions are shifted to the next session.
    frame["ma_position"] = (frame.sma50 > frame.sma200).where(frame.sma200.notna()).astype(float).shift(1).fillna(0)
    frame["momentum_position"] = (frame.momentum20 > 0).where(frame.momentum20.notna()).astype(float).shift(1).fillna(0)
    frame["mean_reversion_position"] = (frame.momentum20 < 0).where(frame.momentum20.notna()).astype(float).shift(1).fillna(0)
    frame["buy_hold_position"] = 1.0
    return frame


def score(frame: pd.DataFrame, position: str, cost_bps: float = 2.0) -> dict:
    if cost_bps < 0:
        raise ValueError("cost_bps must be nonnegative")
    x = frame.iloc[200:].copy()
    if x.empty or x["return"].isna().any():
        raise ValueError("Insufficient scored observations")
    pos = x[position].astype(float)
    # First position incurs entry cost; changes incur turnover cost.
    turnover = pos.diff().abs().fillna(pos.abs())
    net = pos * x["return"] - turnover * cost_bps / 10000
    equity = (1 + net).cumprod()
    n = len(net)
    final = float(equity.iloc[-1])
    volatility = float(net.std(ddof=1) * math.sqrt(252))
    return {"sessions": n, "cost_bps": cost_bps,
            "cagr": float(final ** (252 / n) - 1) if final > 0 else None,
            "volatility": volatility,
            "sharpe_zero_rf": float(net.mean() * 252 / volatility) if volatility > 0 else None,
            "max_drawdown": float((equity / equity.cummax() - 1).min()),
            "final_multiple": final, "turnover": float(turnover.sum())}


def run(csv_path: str | Path | None = None, output_root: str | Path = "runs",
        cost_bps: float = 2.0, parent_run: str = PARENT_RUN) -> Path:
    """Create an immutable per-run directory and hash-verifiable research record."""
    if csv_path is None:
        data, raw = download_spy()
        source = {"provider": "yfinance/Yahoo", "symbol": "SPY", "point_in_time_verified": False}
    else:
        data, raw = load_csv(csv_path)
        source = {"provider": "user_csv", "input_filename": Path(csv_path).name,
                  "point_in_time_verified": False}
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    root = Path(output_root) / run_id
    root.mkdir(parents=True, exist_ok=False)
    (root / "raw.csv").write_bytes(raw)
    normalized_bytes = data.to_csv(index=False, float_format="%.12g").encode()
    (root / "normalized.csv").write_bytes(normalized_bytes)
    frame = features(data)
    con = duckdb.connect(str(root / "research.duckdb"))
    try:
        con.register("observations_frame", data)
        con.execute("CREATE TABLE observations AS SELECT * FROM observations_frame")
        con.register("features_frame", frame)
        con.execute("CREATE TABLE features AS SELECT * FROM features_frame")
        con.execute("CREATE TABLE evidence (run_id VARCHAR, raw_sha256 VARCHAR, normalized_sha256 VARCHAR, source_json VARCHAR)")
        con.execute("INSERT INTO evidence VALUES (?, ?, ?, ?)",
                    [run_id, sha256(raw), sha256(normalized_bytes), json.dumps(source, sort_keys=True)])
    finally:
        con.close()
    names = {"buy_hold": "buy_hold_position", "ma_50_200": "ma_position",
             "momentum_20": "momentum_position", "mean_reversion_20": "mean_reversion_position"}
    results = {name: score(frame, column, cost_bps) for name, column in names.items()}
    (root / "baseline_results.json").write_text(json.dumps(results, indent=2, allow_nan=False) + "\n")
    record = {
        "schema": "hmdl.foundation.v0.1", "run_id": run_id, "version": VERSION,
        "parent_run_id": parent_run, "parent_report": SOURCE_REPORT,
        "classification": "EXPERIMENTAL", "lifecycle_decision": "RETAIN_FOR_RESEARCH",
        "canonical_authority_granted": False, "execution_authorized": False,
        "symbol": "SPY" if csv_path is None else None, "source": source,
        "observation_start": data.date.iloc[0].isoformat(),
        "observation_end": data.date.iloc[-1].isoformat(), "observations": len(data),
        "raw_sha256": sha256(raw), "normalized_sha256": sha256(normalized_bytes),
        "method": {"sessions_per_year": 252, "cost_bps": cost_bps,
                   "signal_execution": "signal at close t; position at session t+1",
                   "score_warmup_sessions": 200, "dividend_adjustment": "source dependent"},
        "baselines": results,
        "finding": "BASELINES_COMPUTED_NO_PREDICTIVE_CLAIM",
        "limitations": ["Single historical sample; no walk-forward validation",
                        "Data not independently verified as point-in-time",
                        "No slippage, spread, tax, financing, or broker model",
                        "No Harmony360-derived feature or Core compatibility claim"],
        "artifact_sha256": {"raw.csv": sha256(raw),
                            "normalized.csv": sha256(normalized_bytes),
                            "baseline_results.json": sha256((root / "baseline_results.json").read_bytes()),
                            "research.duckdb": sha256((root / "research.duckdb").read_bytes())},
    }
    record["record_sha256"] = sha256(canonical_bytes(record))
    (root / "RUN_SUMMARY.har360.json").write_text(json.dumps(record, indent=2, allow_nan=False) + "\n")
    return root


def verify(root: str | Path) -> bool:
    root = Path(root)
    record = json.loads((root / "RUN_SUMMARY.har360.json").read_text())
    declared_hash = record.pop("record_sha256")
    if sha256(canonical_bytes(record)) != declared_hash:
        return False
    return all(sha256((root / name).read_bytes()) == digest
               for name, digest in record["artifact_sha256"].items())


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--csv", type=Path, help="Date and Close CSV; omit to download SPY")
    p.add_argument("--output", type=Path, default=Path("runs"))
    args = p.parse_args()
    destination = run(args.csv, args.output)
    print(json.dumps({"run_directory": str(destination), "verification_pass": verify(destination)}))
