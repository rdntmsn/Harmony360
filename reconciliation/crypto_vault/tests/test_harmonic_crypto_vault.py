import base64
import json

import pytest

from harmonic_crypto_vault import HarmonicCryptoVault, Harmony360KeyRegistry


def test_round_trip_and_nonce_uniqueness(tmp_path):
    registry = Harmony360KeyRegistry()
    key_id = registry.create_key("key-a")
    vault = HarmonicCryptoVault(tmp_path, registry.resolve)
    payload = {"hello": "Harmony360", "n": 360}

    p1 = vault.store_encrypted_har360(payload, key_id, "a")
    p2 = vault.store_encrypted_har360(payload, key_id, "b")

    assert vault.load_encrypted_har360(p1, key_id) == payload
    e1 = json.loads(p1.read_text())
    e2 = json.loads(p2.read_text())
    assert e1["nonce_b64"] != e2["nonce_b64"]
    assert e1["ciphertext_b64"] != e2["ciphertext_b64"]


def test_wrong_key_rejected(tmp_path):
    registry = Harmony360KeyRegistry()
    key_a = registry.create_key("key-a")
    key_b = registry.create_key("key-b")
    vault = HarmonicCryptoVault(tmp_path, registry.resolve)
    p = vault.store_encrypted_har360({"x": 1}, key_a, "a")

    with pytest.raises(ValueError):
        vault.load_encrypted_har360(p, key_b)


def test_ciphertext_tamper_rejected(tmp_path):
    registry = Harmony360KeyRegistry()
    key_id = registry.create_key("key-a")
    vault = HarmonicCryptoVault(tmp_path, registry.resolve)
    p = vault.store_encrypted_har360({"x": 1}, key_id, "a")

    env = json.loads(p.read_text())
    raw = bytearray(base64.b64decode(env["ciphertext_b64"]))
    raw[0] ^= 1
    env["ciphertext_b64"] = base64.b64encode(bytes(raw)).decode("ascii")
    p.write_text(json.dumps(env))

    with pytest.raises(ValueError):
        vault.load_encrypted_har360(p, key_id)


def test_authenticated_metadata_tamper_rejected(tmp_path):
    registry = Harmony360KeyRegistry()
    key_id = registry.create_key("key-a")
    vault = HarmonicCryptoVault(tmp_path, registry.resolve)
    p = vault.store_encrypted_har360({"x": 1}, key_id, "a", {"lineage": "original"})

    env = json.loads(p.read_text())
    env["header"]["metadata"]["lineage"] = "tampered"
    p.write_text(json.dumps(env))

    with pytest.raises(ValueError):
        vault.load_encrypted_har360(p, key_id)


def test_revoked_key_invalid(tmp_path):
    registry = Harmony360KeyRegistry()
    key_id = registry.create_key("key-a")
    vault = HarmonicCryptoVault(tmp_path, registry.resolve)
    assert vault.validate_resonance_key(key_id)
    registry.revoke(key_id)
    assert not vault.validate_resonance_key(key_id)
