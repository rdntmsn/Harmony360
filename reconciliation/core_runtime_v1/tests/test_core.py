import math
import numpy as np

from harmony360 import Harmony360, ALPHA, ALPHA_LEGACY


def test_constants_and_lineage():
    h = Harmony360()
    assert math.isclose(h.phi, (1 + math.sqrt(5)) / 2)
    assert ALPHA != ALPHA_LEGACY
    assert h.identity.name == "Harmony360"


def test_eta_chi_definitions():
    h = Harmony360()
    assert math.isclose(h.eta, h.phi * h.pi + h.alpha)
    assert math.isclose(h.chi, math.log(h.phi) / h.pi)


def test_historical_aliases():
    h = Harmony360()
    theta = 0.25
    assert np.isclose(h.resonance_scaling(theta), h.resonance_scaling_wave(theta))
    assert np.isclose(h.fractal_harmonic_mapping(0.2, 0.4), h.fractal_harmonic_wavefield(0.2, 0.4))


def test_eh360_finite():
    h = Harmony360()
    assert h.eh360(432.0) > 0


def test_metrics_are_bounded_or_nonnegative():
    h = Harmony360()
    c = h.coherence_score([1, 1, 1, 1])
    e = h.harmonic_entropy([1, 2, 3, 4])
    assert 0 <= c <= 1
    assert e >= 0
