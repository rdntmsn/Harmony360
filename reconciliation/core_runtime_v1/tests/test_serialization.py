import json
import pytest

from harmony360 import save_har360, load_har360


def test_har360_round_trip(tmp_path):
    payload = {"hello": "Harmony360", "n": 360}
    p = save_har360(payload, tmp_path / "x.har360", {"kind": "test"})
    assert load_har360(p) == payload


def test_har360_tamper_detection(tmp_path):
    payload = {"x": 1}
    p = save_har360(payload, tmp_path / "x.har360")
    env = json.loads(p.read_text())
    env["payload"]["x"] = 2
    p.write_text(json.dumps(env))
    with pytest.raises(ValueError):
        load_har360(p)
