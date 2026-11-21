"""Call the installed, existing core. Do not copy or redefine its mathematics."""
from __future__ import annotations

import math
import tempfile
from pathlib import Path

from .jsonutil import atomic_write, canonical, digest, strict_loads


class CoreBridge:
    def __init__(self):
        try:
            from harmony360 import Harmony360, load_har360, save_har360
        except ImportError:
            raise RuntimeError("Install the existing reconciliation/core_runtime_v1 package first") from None
        self.core = Harmony360()
        self.load_har360, self.save_har360 = load_har360, save_har360

    def analyze(self, values: list[float]) -> dict:
        if not values or not all(isinstance(x, (float, int)) and not isinstance(x, bool) and math.isfinite(x) for x in values):
            raise ValueError("Expected a nonempty list of finite numeric values")
        return {"core_manifest": self.core.core_manifest(),
                "core_calls": ["coherence_score", "harmonic_entropy", "resonance_scaling_exponential"],
                "dispersion_coherence": self.core.coherence_score(values),
                "harmonic_entropy_bits": self.core.harmonic_entropy(values),
                "resonance_calibration": [float(self.core.resonance_scaling_exponential(n)) for n in (0, 1, 2)],
                "interpretation": "Numerical diagnostics only; neither factual accuracy nor permission to act."}

    def seal(self, payload: dict, path: Path) -> str:
        canonical(payload)  # Existing codec accepts more permissive JSON; the adapter tightens its own input.
        path = Path(path)
        with tempfile.TemporaryDirectory() as tmp:
            temporary = Path(tmp) / "receipt.har360"
            self.save_har360(payload, temporary, metadata={"adapter_schema": "harmony360.orchestration.v0.1"})
            raw = temporary.read_bytes()
            strict_loads(raw)
            if self.load_har360(temporary) != payload:
                raise ValueError("Core codec round-trip mismatch")
            atomic_write(path, raw)
        return digest(raw)

    def reconstruct(self, path: Path, *, expected_sha256: str) -> dict:
        raw = Path(path).read_bytes()
        if digest(raw) != expected_sha256:
            raise ValueError("Carrier hash mismatch before decoding")
        strict_loads(raw)
        # Decode the exact verified bytes; do not re-open a mutable caller path.
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "verified.har360"
            p.write_bytes(raw)
            return self.load_har360(p)

