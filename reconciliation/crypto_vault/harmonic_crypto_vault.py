from __future__ import annotations

import os
import json
import base64
import hashlib
import secrets
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Callable

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

try:
    from harmony360_core import Harmony360
except Exception:
    class Harmony360:
        """Compatibility shim for standalone execution.

        The reconciliation module is intended to inherit the canonical
        Harmony360 core when that package path is available.
        """
        def __init__(self):
            self.phi = (1 + 5 ** 0.5) / 2
            self.pi = 3.141592653589793
            self.alpha = 1 / 137


class Harmony360KeyRegistry:
    """Development key registry. Production should delegate key bytes to KMS/secret storage."""

    def __init__(self):
        self._keys: dict[str, bytes] = {}
        self._status: dict[str, str] = {}

    def create_key(self, key_id: str | None = None) -> str:
        key_id = key_id or f"h360-key-{secrets.token_hex(8)}"
        if key_id in self._keys:
            raise ValueError(f"Duplicate key_id: {key_id}")
        self._keys[key_id] = AESGCM.generate_key(bit_length=256)
        self._status[key_id] = "ACTIVE"
        return key_id

    def resolve(self, key_id: str) -> bytes:
        if self._status.get(key_id) != "ACTIVE":
            raise KeyError(f"Key is unavailable or inactive: {key_id}")
        return self._keys[key_id]

    def revoke(self, key_id: str) -> None:
        if key_id not in self._keys:
            raise KeyError(key_id)
        self._status[key_id] = "REVOKED"

    def status(self, key_id: str) -> str | None:
        return self._status.get(key_id)


class HarmonicCryptoVault(Harmony360):
    """Authenticated encrypted .har360 storage.

    Security primitive: AES-256-GCM.
    Harmony360 responsibilities: identity, lineage, policy hooks,
    evidence metadata, and reconstruction metadata.

    φ/π transforms and historical QRC360 transforms are not used as
    cryptographic security primitives.
    """

    FORMAT = "HARMONY360_CRYPTO_VAULT"
    VERSION = "1.0"
    ALGORITHM = "AES-256-GCM"
    NONCE_BYTES = 12
    KEY_BYTES = 32

    def __init__(self, vault_dir: str | Path, key_resolver: Callable[[str], bytes]):
        super().__init__()
        self.vault_dir = Path(vault_dir)
        self.vault_dir.mkdir(parents=True, exist_ok=True)
        self.key_resolver = key_resolver

    @staticmethod
    def _canonical_json(value: Any) -> bytes:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

    @staticmethod
    def _sha256(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def validate_resonance_key(self, key_id: str) -> bool:
        try:
            key = self.key_resolver(key_id)
        except Exception:
            return False
        return isinstance(key, bytes) and len(key) == self.KEY_BYTES

    def store_encrypted_har360(
        self,
        data_blob: Any,
        key_id: str,
        artifact_id: str,
        metadata: dict | None = None,
    ) -> Path:
        if not self.validate_resonance_key(key_id):
            raise ValueError("Invalid Harmony360 vault key.")

        key = self.key_resolver(key_id)
        plaintext = self._canonical_json(data_blob)
        nonce = os.urandom(self.NONCE_BYTES)

        header = {
            "format": self.FORMAT,
            "version": self.VERSION,
            "algorithm": self.ALGORITHM,
            "artifact_id": artifact_id,
            "key_id": key_id,
            "plaintext_sha256": self._sha256(plaintext),
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {},
        }

        aad = self._canonical_json(header)
        ciphertext = AESGCM(key).encrypt(nonce, plaintext, aad)

        envelope = {
            "header": header,
            "nonce_b64": base64.b64encode(nonce).decode("ascii"),
            "ciphertext_b64": base64.b64encode(ciphertext).decode("ascii"),
            "ciphertext_sha256": self._sha256(ciphertext),
        }

        destination = self.vault_dir / f"{artifact_id}.encrypted.har360"
        destination.write_text(json.dumps(envelope, indent=2, sort_keys=True), encoding="utf-8")
        return destination

    def load_encrypted_har360(self, path: str | Path, key_id: str) -> Any:
        envelope = json.loads(Path(path).read_text(encoding="utf-8"))
        header = envelope["header"]

        if header["format"] != self.FORMAT:
            raise ValueError("Not a Harmony360 CryptoVault artifact.")
        if header["version"] != self.VERSION:
            raise ValueError("Unsupported vault version.")
        if header["algorithm"] != self.ALGORITHM:
            raise ValueError("Unexpected encryption algorithm.")
        if header["key_id"] != key_id:
            raise ValueError("Key identifier mismatch.")
        if not self.validate_resonance_key(key_id):
            raise ValueError("Invalid Harmony360 vault key.")

        nonce = base64.b64decode(envelope["nonce_b64"])
        ciphertext = base64.b64decode(envelope["ciphertext_b64"])

        if self._sha256(ciphertext) != envelope["ciphertext_sha256"]:
            raise ValueError("Ciphertext hash mismatch.")

        try:
            plaintext = AESGCM(self.key_resolver(key_id)).decrypt(
                nonce, ciphertext, self._canonical_json(header)
            )
        except InvalidTag as exc:
            raise ValueError("Authentication failed.") from exc

        if self._sha256(plaintext) != header["plaintext_sha256"]:
            raise ValueError("Decrypted payload hash mismatch.")

        return json.loads(plaintext.decode("utf-8"))
