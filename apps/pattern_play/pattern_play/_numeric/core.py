from __future__ import annotations

import math
from dataclasses import dataclass, asdict
from typing import Sequence, Any

import numpy as np

from .constants import (
    PHI, PI, ALPHA, ALPHA_LEGACY,
    PLANCK_LENGTH, HBAR, C,
)


@dataclass(frozen=True)
class Harmony360CoreIdentity:
    name: str = "Harmony360"
    runtime_version: str = "1.0.0"
    reconciliation_lineage: str = "recovered-v10-v13 -> canonical-runtime-spine-v1"


class Harmony360:
    """Canonical Harmony360 runtime spine.

    Scope:
      - constants and mathematical primitives
      - deterministic Harmony360 transforms
      - stable inheritance surface for capability modules
      - explicit separation between definitions and scientific claims

    This class does not grant empirical truth to a formula merely because
    the formula is implemented.
    """

    identity = Harmony360CoreIdentity()

    def __init__(self):
        self.phi = PHI
        self.pi = PI
        self.alpha = ALPHA
        self.alpha_legacy = ALPHA_LEGACY
        self.hbar = HBAR
        self.c = C
        self.lp = PLANCK_LENGTH

    def resonance_scaling_exponential(self, n, A=1.0, B=1.0, C_=1.0):
        return A * (self.phi ** n) + B * (self.pi ** n) + C_ * ((self.phi * self.pi) ** (n / 2))

    def resonance_scaling_wave(self, theta, A=1.0, B=1.0, C_=1.0):
        return A * np.sin(3 * theta) + B * np.cos(6 * theta) + C_ * np.sin(9 * theta)

    def resonance_scaling(self, theta, A=1.0, B=1.0, C=1.0):
        return self.resonance_scaling_wave(theta, A=A, B=B, C_=C)

    def R_369(self, t):
        return np.sin(3 * t) + np.cos(6 * t) + np.sin(9 * t)

    def phi_pi_modulation(self, f):
        if not np.isfinite(f):
            return 0.0
        return np.sin(2 * self.pi * f / self.phi)

    def fractal_harmonic_wavefield(self, x, y):
        return 0.5 * (
            (1 + self.phi) * np.sin(3 * x * (1 + self.phi) / 2)
            + np.cos(6 * y * self.pi / 2)
        )

    def fractal_harmonic_mapping(self, x, y):
        return self.fractal_harmonic_wavefield(x, y)

    def fractal_harmonic_projection(self, x, y):
        return (
            self.phi * x + self.pi * y,
            self.phi * y - self.pi * x,
        )

    def golden_spiral(self, angle):
        return np.exp(self.phi * angle)

    @property
    def eta(self) -> float:
        """Harmony360 η definition: φπ + α.

        This is a Harmony360-defined mathematical quantity, not by itself
        an established physical constant.
        """
        return self.phi * self.pi + self.alpha

    @property
    def chi(self) -> float:
        """Harmony360 χ definition: ln(φ)/π."""
        return math.log(self.phi) / self.pi

    def eh360(self, frequency_hz: float) -> float:
        """Harmony360 EH360 definition: ħ f (φπ + α)."""
        if not np.isfinite(frequency_hz):
            raise ValueError("frequency_hz must be finite")
        return self.hbar * float(frequency_hz) * self.eta

    def coherence_score(self, values: Sequence[float]) -> float:
        arr = np.asarray(values, dtype=float)
        if arr.size == 0 or not np.isfinite(arr).all() or np.all(arr == 0):
            return 0.0
        mean = float(np.mean(arr))
        if abs(mean) < 1e-12:
            return 0.0
        score = 1.0 - float(np.std(arr)) / (abs(mean) + 1e-12)
        return float(np.clip(score, 0.0, 1.0))

    def harmonic_entropy(self, values: Sequence[float]) -> float:
        arr = np.asarray(values, dtype=float)
        arr = arr[np.isfinite(arr)]
        if arr.size == 0:
            return 0.0
        weights = np.abs(arr)
        total = float(weights.sum())
        if total <= 0:
            return 0.0
        p = weights / total
        return float(-np.sum(p * np.log2(p + 1e-15)))

    def core_manifest(self) -> dict[str, Any]:
        return {
            "identity": asdict(self.identity),
            "constants": {
                "phi": self.phi,
                "pi": self.pi,
                "alpha": self.alpha,
                "alpha_legacy": self.alpha_legacy,
                "planck_length_m": self.lp,
                "hbar_j_s": self.hbar,
                "c_m_s": self.c,
            },
            "harmony360_definitions": {
                "eta": self.eta,
                "chi": self.chi,
                "eh360": "hbar * f * eta",
            },
            "claim_boundary": (
                "Implemented mathematical definitions are not automatically "
                "empirical scientific claims."
            ),
        }
