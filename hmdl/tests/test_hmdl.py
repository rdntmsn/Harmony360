import json
from pathlib import Path

import numpy as np
import pandas as pd

from hmdl import features, run, verify


def fixture(path: Path):
    dates = pd.bdate_range("2020-01-01", periods=300)
    close = 100 + np.arange(300) * 0.1
    pd.DataFrame({"Date": dates, "Close": close}).to_csv(path, index=False)


def test_signal_uses_prior_close(tmp_path):
    csv = tmp_path / "prices.csv"
    fixture(csv)
    frame = features(pd.DataFrame({"date": pd.bdate_range("2020-01-01", periods=300, tz="UTC"),
                                   "close": 100 + np.arange(300) * 0.1}))
    assert frame.ma_position.iloc[199] == 0
    assert frame.ma_position.iloc[200] == 1
    assert frame.momentum_position.iloc[20] == 0
    assert frame.momentum_position.iloc[21] == 1


def test_run_receipts_and_tamper_detection(tmp_path):
    csv = tmp_path / "prices.csv"
    fixture(csv)
    root = run(csv, tmp_path / "runs")
    record = json.loads((root / "RUN_SUMMARY.har360.json").read_text())
    assert record["execution_authorized"] is False
    assert record["observations"] == 300
    assert verify(root)
    (root / "raw.csv").write_bytes(b"changed")
    assert not verify(root)
