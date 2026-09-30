from pathlib import Path

from harmony360 import AblationConfig, PhiPiTuner, TuningCandidate


def test_generic_tuner_does_not_privilege_phi(tmp_path):
    tuner = PhiPiTuner(tmp_path)
    candidates = (
        TuningCandidate("phi", 1.61803398875, "harmony360"),
        TuningCandidate("control", 1.5, "control"),
    )
    result = tuner.optimize_parameters(
        "unit",
        lambda c: abs(c.value - 1.5),
        candidates=candidates,
    )
    assert result["best"]["name"] == "control"


def test_language_model_ablation_is_controlled_and_persisted(tmp_path):
    tuner = PhiPiTuner(tmp_path)
    corpus = (
        "Harmony360 controlled ablation separates historical questions from assumptions. "
        "The same corpus architecture seeds optimizer and budget are used for each candidate. "
    ) * 10
    config = AblationConfig(
        sequence_length=8,
        embedding_dim=8,
        hidden_dim=12,
        batch_size=16,
        epochs=1,
        learning_rate=0.01,
        seeds=(13,),
        device="cpu",
    )
    candidates = (
        TuningCandidate("baseline", 1.0, "baseline"),
        TuningCandidate("phi", 1.61803398875, "harmony360"),
    )
    result = tuner.run_language_model_ablation(
        corpus,
        simulation_id="unit_ablation",
        mode="lr_decay",
        config=config,
        candidates=candidates,
    )
    assert result["run_count"] == 2
    assert {r["candidate"] for r in result["records"]} == {"baseline", "phi"}
    assert len(result["ranking"]) == 2
    assert Path(result["result_path"]).exists()
    assert (tmp_path / "PHI_PI_TUNER_LEDGER.jsonl").exists()
    assert result["measurement_contract"]["format"] == "HARMONY360_EXPERIMENT_RECORD"
    assert len(result["measurement_contract"]["arms"]) == 2

    for record in result["records"]:
        assert record["intervention_flags"]["harmony360_measurement"] is True
        measured = record["harmony360_measurement"]
        assert "validation_loss" in measured
        assert "epoch_train_loss" in measured
        assert "learning_rate" in measured
        obs = measured["validation_loss"]["harmony360_observables"]
        assert "phi_pi_modulation" in obs
        assert "r_369" in obs
        assert "resonance_scaling" in obs
        assert "fractal_harmonic_projection" in obs

    baseline = next(r for r in result["records"] if r["candidate"] == "baseline")
    assert baseline["intervention_flags"]["phi_constant_intervention"] is False
    assert baseline["intervention_flags"]["harmony360_measurement"] is True


def test_initialization_ablation_runs(tmp_path):
    tuner = PhiPiTuner(tmp_path)
    corpus = "phi initialization control experiment " * 40
    config = AblationConfig(
        sequence_length=8,
        embedding_dim=8,
        hidden_dim=12,
        batch_size=16,
        epochs=1,
        seeds=(36,),
    )
    candidates = (
        TuningCandidate("baseline", 1.0, "baseline"),
        TuningCandidate("phi", 1.61803398875, "harmony360"),
        TuningCandidate("sqrt2", 2 ** 0.5, "control"),
    )
    result = tuner.run_language_model_ablation(
        corpus,
        simulation_id="unit_init",
        mode="init_scale",
        config=config,
        candidates=candidates,
    )
    assert result["run_count"] == 3
    assert result["phi_vs_baseline"] is not None
    assert all(r["intervention_flags"]["harmony360_measurement"] for r in result["records"])


def test_export_best_fit_results(tmp_path):
    tuner = PhiPiTuner(tmp_path)
    tuner.optimize_parameters("export", lambda c: c.value)
    path = tuner.export_best_fit_results()
    assert path.exists()
    assert path.name == "PHI_PI_TUNER_BEST_FIT.har360.json"
