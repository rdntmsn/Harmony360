from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Sequence

import numpy as np

from .core import Harmony360


@dataclass(frozen=True)
class MeasurementSemantics:
    """Meaning attached to the numeric series being measured.

    `coordinate_units` and `value_units` are descriptive. Harmony360 transforms
    are mathematical unless the caller explicitly supplies a physical mapping.
    """

    label: str
    value_units: str = "dimensionless"
    coordinate_units: str = "index"
    interpretation: str = "observed numeric series"


class Harmony360MeasurementContract(Harmony360):
    """Canonical Harmony360 mathematical measurement layer.

    Standing rule:
      * Every governed Harmony360 experiment measures every arm through this
        canonical core layer, including neutral/control arms.
      * Harmony360 interventions remain independently switchable. Measurement
        does not imply intervention.
      * Domain-standard metrics remain primary evidence for domain performance;
        Harmony360-native observables are recorded in parallel.

    The contract prevents inheritance-only experiments where `Harmony360` is in
    the class tree but none of the core mathematics enters the evidence record.
    """

    FORMAT = "HARMONY360_EXPERIMENTAL_MEASUREMENT"
    VERSION = "1.0"

    def measure_series(
        self,
        values: Sequence[float],
        *,
        semantics: MeasurementSemantics,
        coordinates: Sequence[float] | None = None,
    ) -> dict[str, Any]:
        arr = np.asarray(values, dtype=float)
        if arr.ndim != 1 or arr.size == 0:
            raise ValueError("values must be a non-empty 1-D numeric sequence")
        if not np.isfinite(arr).all():
            raise ValueError("values must be finite")

        if coordinates is None:
            coords = np.arange(arr.size, dtype=float)
        else:
            coords = np.asarray(coordinates, dtype=float)
            if coords.shape != arr.shape:
                raise ValueError("coordinates must align one-to-one with values")
            if not np.isfinite(coords).all():
                raise ValueError("coordinates must be finite")

        # The raw observed value is the argument to the scalar core transforms.
        # This is dimensionless mathematical measurement unless caller semantics
        # explicitly establish a physical mapping.
        phi_pi = np.asarray([self.phi_pi_modulation(v) for v in arr], dtype=float)
        r369 = np.asarray([self.R_369(v) for v in arr], dtype=float)
        resonance = np.asarray([self.resonance_scaling(v) for v in arr], dtype=float)

        projections = np.asarray(
            [self.fractal_harmonic_projection(float(v), float(c)) for v, c in zip(arr, coords)],
            dtype=float,
        )

        return {
            "format": self.FORMAT,
            "version": self.VERSION,
            "semantics": asdict(semantics),
            "core_constants": {
                "phi": float(self.phi),
                "pi": float(self.pi),
                "alpha": float(self.alpha),
                "eta": float(self.eta),
                "chi": float(self.chi),
            },
            "domain_summary": {
                "count": int(arr.size),
                "mean": float(arr.mean()),
                "std": float(arr.std(ddof=0)),
                "min": float(arr.min()),
                "max": float(arr.max()),
                "first": float(arr[0]),
                "last": float(arr[-1]),
            },
            "harmony360_observables": {
                "coherence_score": float(self.coherence_score(arr)),
                "harmonic_entropy": float(self.harmonic_entropy(arr)),
                "phi_pi_modulation": phi_pi.tolist(),
                "phi_pi_modulation_mean": float(phi_pi.mean()),
                "phi_pi_modulation_std": float(phi_pi.std(ddof=0)),
                "r_369": r369.tolist(),
                "r_369_mean": float(r369.mean()),
                "resonance_scaling": resonance.tolist(),
                "resonance_scaling_mean": float(resonance.mean()),
                "fractal_harmonic_projection": projections.tolist(),
            },
            "claim_boundary": (
                "Harmony360 observables are mathematical measurements of the supplied series. "
                "They do not acquire physical meaning unless the experiment defines and validates "
                "the mapping from the measured quantity to a physical observable."
            ),
        }

    def build_arm_record(
        self,
        *,
        arm_name: str,
        domain_metrics: dict[str, Any],
        measured_series: dict[str, dict[str, Any]],
        intervention_flags: dict[str, bool],
    ) -> dict[str, Any]:
        if not arm_name:
            raise ValueError("arm_name is required")
        if not measured_series:
            raise ValueError("at least one Harmony360 measured series is required")
        if not intervention_flags:
            raise ValueError("intervention_flags are required, including for controls")

        return {
            "arm_name": arm_name,
            "domain_metrics": domain_metrics,
            "harmony360_measurement": measured_series,
            "intervention_flags": {str(k): bool(v) for k, v in intervention_flags.items()},
        }

    def validate_experiment_record(self, experiment: dict[str, Any]) -> bool:
        arms = experiment.get("arms")
        if not isinstance(arms, list) or len(arms) < 2:
            return False
        for arm in arms:
            if not isinstance(arm, dict):
                return False
            if not arm.get("arm_name"):
                return False
            if not isinstance(arm.get("domain_metrics"), dict):
                return False
            measured = arm.get("harmony360_measurement")
            if not isinstance(measured, dict) or not measured:
                return False
            for measurement in measured.values():
                if not isinstance(measurement, dict):
                    return False
                if measurement.get("format") != self.FORMAT:
                    return False
                if "harmony360_observables" not in measurement:
                    return False
            flags = arm.get("intervention_flags")
            if not isinstance(flags, dict) or not flags:
                return False
        return True

    def compare_arms(
        self,
        control: dict[str, Any],
        treatment: dict[str, Any],
        *,
        domain_metric: str,
        measured_series_key: str,
    ) -> dict[str, Any]:
        c_domain = float(control["domain_metrics"][domain_metric])
        t_domain = float(treatment["domain_metrics"][domain_metric])

        c_h = control["harmony360_measurement"][measured_series_key]["harmony360_observables"]
        t_h = treatment["harmony360_measurement"][measured_series_key]["harmony360_observables"]

        return {
            "control_arm": control["arm_name"],
            "treatment_arm": treatment["arm_name"],
            "domain_metric": domain_metric,
            "domain_delta_treatment_minus_control": t_domain - c_domain,
            "harmony360_delta": {
                "coherence_score": float(t_h["coherence_score"] - c_h["coherence_score"]),
                "harmonic_entropy": float(t_h["harmonic_entropy"] - c_h["harmonic_entropy"]),
                "phi_pi_modulation_mean": float(
                    t_h["phi_pi_modulation_mean"] - c_h["phi_pi_modulation_mean"]
                ),
                "r_369_mean": float(t_h["r_369_mean"] - c_h["r_369_mean"]),
                "resonance_scaling_mean": float(
                    t_h["resonance_scaling_mean"] - c_h["resonance_scaling_mean"]
                ),
            },
            "interpretation_boundary": (
                "The domain delta measures task performance. Harmony360 deltas measure changes "
                "in canonical mathematical observables. Correlation or causation between them "
                "requires repeated controlled experiments."
            ),
        }
