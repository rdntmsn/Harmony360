import torch

from harmony360 import (
    ConventionalMLP,
    FractalBranchMLP,
    FractalReproductionConfig,
    FractalStructureReproduction,
    trainable_parameters,
)


def test_parameter_counts_match_exactly():
    assert trainable_parameters(ConventionalMLP()) == 118282
    assert trainable_parameters(FractalBranchMLP()) == 118282


def test_fractal_reproduction_uses_measurement_contract(tmp_path):
    torch.manual_seed(7)
    train_x = torch.randn(128, 1, 28, 28)
    train_y = torch.randint(0, 10, (128,))
    test_x = torch.randn(64, 1, 28, 28)
    test_y = torch.randint(0, 10, (64,))

    runner = FractalStructureReproduction(tmp_path)
    result = runner.run(
        train_x,
        train_y,
        test_x,
        test_y,
        config=FractalReproductionConfig(
            batch_size=32,
            epochs=1,
            learning_rate=1e-3,
            seeds=(13,),
        ),
        simulation_id="unit_fractal",
    )

    assert result["parameter_match"]["exact_match"] is True
    assert result["parameter_match"]["control"] == 118282
    assert result["parameter_match"]["fractal_treatment"] == 118282
    assert len(result["experiments"]) == 1

    arms = result["experiments"][0]["arms"]
    assert arms[0]["intervention_flags"]["harmony360_measurement"] is True
    assert arms[0]["intervention_flags"]["fractal_structure_intervention"] is False
    assert arms[1]["intervention_flags"]["harmony360_measurement"] is True
    assert arms[1]["intervention_flags"]["fractal_structure_intervention"] is True

    for arm in arms:
        assert "test_loss" in arm["harmony360_measurement"]
        assert "test_accuracy" in arm["harmony360_measurement"]
        observables = arm["harmony360_measurement"]["test_accuracy"]["harmony360_observables"]
        assert "phi_pi_modulation" in observables
        assert "r_369" in observables
        assert "fractal_harmonic_projection" in observables

    assert (tmp_path / "FRACTAL_STRUCTURE_LEDGER.jsonl").exists()
    assert (tmp_path / "unit_fractal.har360.json").exists()


def test_historical_scope_is_explicit(tmp_path):
    torch.manual_seed(3)
    train_x = torch.randn(64, 1, 28, 28)
    train_y = torch.randint(0, 10, (64,))
    test_x = torch.randn(32, 1, 28, 28)
    test_y = torch.randint(0, 10, (32,))

    result = FractalStructureReproduction(tmp_path).run(
        train_x,
        train_y,
        test_x,
        test_y,
        config=FractalReproductionConfig(batch_size=32, epochs=1, seeds=(13,)),
    )

    lineage = result["historical_lineage"]
    assert lineage["historical_baseline_parameters"] == 118282
    assert lineage["historical_fractal_parameters"] == 151562
    assert lineage["historical_confound"] == "parameter_count_mismatch"
    assert "Exact historical topology was not located" in lineage["reconstruction_note"]
