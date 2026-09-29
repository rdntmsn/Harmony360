import json
from pathlib import Path

import pytest

from harmony360.snapshot import Harmony360Snapshot
from harmony360.ledger import HAR360LedgerManager
from harmony360.sync import h360_sync


def test_snapshot_round_trip_and_tamper_detection(tmp_path):
    snapper = Harmony360Snapshot()
    snapshot = snapper.save_state({"x": 360}, label="unit")
    p = snapper.export_snapshot(snapshot, tmp_path / "unit.har360.json")
    assert snapper.load_snapshot(p) == {"x": 360}

    tampered = json.loads(p.read_text())
    tampered["state"]["x"] = 361
    p.write_text(json.dumps(tampered))
    with pytest.raises(ValueError):
        snapper.import_snapshot(p)


def test_ledger_chain_and_tamper_detection(tmp_path):
    path = tmp_path / "ledger.jsonl"
    ledger = HAR360LedgerManager(path)
    a = ledger.append_entry(
        event_type="TEST", artifact_id="a", artifact_sha256="a" * 64, status="PASS"
    )
    b = ledger.append_entry(
        event_type="TEST", artifact_id="b", artifact_sha256="b" * 64, status="PASS"
    )
    check = ledger.verify_chain()
    assert check["valid"] is True
    assert check["entries"] == 2
    assert b["previous_entry_sha256"] == a["entry_sha256"]

    rows = path.read_text().splitlines()
    first = json.loads(rows[0])
    first["status"] = "ALTERED"
    rows[0] = json.dumps(first)
    path.write_text("\n".join(rows) + "\n")
    assert ledger.verify_chain()["valid"] is False


def test_ledger_export_requires_valid_chain(tmp_path):
    ledger = HAR360LedgerManager(tmp_path / "ledger.jsonl")
    ledger.append_entry(
        event_type="TEST", artifact_id="a", artifact_sha256="c" * 64, status="PASS"
    )
    out = ledger.export_ledger_snapshot(tmp_path / "ledger_snapshot.har360.json")
    data = json.loads(out.read_text())
    assert data["verification"]["valid"] is True


def test_h360_sync_writes_snapshot_and_ledger(tmp_path):
    snapshot_dir = tmp_path / "snapshots"
    ledger_path = tmp_path / "ledger.jsonl"

    @h360_sync(
        snapshot_dir,
        ledger_path,
        snapshot_type="unit_test",
        notes="test operation",
        lineage="snapshot-ledger-reconciliation-v1",
    )
    def add(a, b):
        return a + b

    assert add(100, 260) == 360
    snapshots = list(snapshot_dir.glob("*.har360.json"))
    assert len(snapshots) == 1
    ledger = HAR360LedgerManager(ledger_path)
    assert ledger.verify_chain()["valid"] is True
    entries = ledger.load_ledger_index()
    assert len(entries) == 1
    assert entries[0]["artifact_id"] == snapshots[0].name
