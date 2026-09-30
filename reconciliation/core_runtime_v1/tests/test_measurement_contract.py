import pytest

from harmony360 import Harmony360MeasurementContract, MeasurementSemantics


def test_measurement_contract_uses_core_math():
    m = Harmony360MeasurementContract()
    result = m.measure_series(
        [1.0, 0.8, 0.6],
        semantics=MeasurementSemantics(
            label="loss",
            value_units="cross_entropy",
            coordinate_units="epoch",
        ),
        coordinates=[0.0, 1.0, 2.0],
    )
    obs = result["harmony360_observables"]
    assert result["core_constants"]["phi"] == pytest.approx(m.phi)
    assert result["core_constants"]["pi"] == pytest.approx(m.pi)
    assert len(obs["phi_pi_modulation"]) == 3
    assert obs["phi_pi_modulation"][0] == pytest.approx(m.phi_pi_modulation(1.0))
    assert obs["r_369"][1] == pytest.approx(m.R_369(0.8))
    assert obs["resonance_scaling"][2] == pytest.approx(m.resonance_scaling(0.6))
    assert len(obs["fractal_harmonic_projection"]) == 3


def test_control_arm_is_measured_even_without_harmony_intervention():
    m = Harmony360MeasurementContract()
    measured = m.measure_series(
        [1.0, 0.9],
        semantics=MeasurementSemantics(label="validation_loss"),
    )
    arm = m.build_arm_record(
        arm_name="control",
        domain_metrics={"final_loss": 0.9},
        measured_series={"validation_loss": measured},
        intervention_flags={
            "harmony360_measurement": True,
            "phi_pi_modulation_intervention": False,
            "fractal_structure_intervention": False,
        },
    )
    assert arm["intervention_flags"]["harmony360_measurement"] is True
    assert arm["intervention_flags"]["phi_pi_modulation_intervention"] is False
    assert "phi_pi_modulation" in arm["harmony360_measurement"]["validation_loss"]["harmony360_observables"]


def test_inheritance_only_record_fails_contract():
    m = Harmony360MeasurementContract()
    invalid = {
        "arms": [
            {"arm_name": "control", "domain_metrics": {}, "intervention_flags": {"x": False}},
            {"arm_name": "treatment", "domain_metrics": {}, "intervention_flags": {"x": True}},
        ]
    }
    assert m.validate_experiment_record(invalid) is False


def test_complete_two_arm_record_passes_contract():
    m = Harmony360MeasurementContract()
    measured = m.measure_series(
        [1.0, 0.5],
        semantics=MeasurementSemantics(label="loss"),
    )
    control = m.build_arm_record(
        arm_name="control",
        domain_metrics={"final_loss": 0.5},
        measured_series={"loss": measured},
        intervention_flags={"harmony360_measurement": True, "treatment": False},
    )
    treatment = m.build_arm_record(
        arm_name="treatment",
        domain_metrics={"final_loss": 0.4},
        measured_series={"loss": measured},
        intervention_flags={"harmony360_measurement": True, "treatment": True},
    )
    assert m.validate_experiment_record({"arms": [control, treatment]}) is True


def test_compare_arms_keeps_domain_and_harmony360_deltas_separate():
    m = Harmony360MeasurementContract()
    c_measured = m.measure_series([1.0, 0.8], semantics=MeasurementSemantics(label="loss"))
    t_measured = m.measure_series([1.0, 0.6], semantics=MeasurementSemantics(label="loss"))
    control = m.build_arm_record(
        arm_name="control",
        domain_metrics={"final_loss": 0.8},
        measured_series={"loss": c_measured},
        intervention_flags={"harmony360_measurement": True, "treatment": False},
    )
    treatment = m.build_arm_record(
        arm_name="treatment",
        domain_metrics={"final_loss": 0.6},
        measured_series={"loss": t_measured},
        intervention_flags={"harmony360_measurement": True, "treatment": True},
    )
    comparison = m.compare_arms(
        control,
        treatment,
        domain_metric="final_loss",
        measured_series_key="loss",
    )
    assert comparison["domain_delta_treatment_minus_control"] == pytest.approx(-0.2)
    assert "phi_pi_modulation_mean" in comparison["harmony360_delta"]
