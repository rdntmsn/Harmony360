import json
from pathlib import Path

from harmony360.trainer import (
    Harmony360Trainer,
    Harmony360HybridTrainer,
    Harmony360TrainingConfig,
    load_trained_language_model,
)


def tiny_config():
    return Harmony360TrainingConfig(
        sequence_length=8,
        embedding_dim=8,
        hidden_dim=16,
        batch_size=8,
        epochs=2,
        learning_rate=0.02,
        seed=360,
    )


def test_real_language_model_training_changes_parameters_and_checkpoints(tmp_path):
    trainer = Harmony360Trainer(tmp_path / "run")
    trainer.add_text(
        ("Harmony360 trains parameters through loss gradients and optimizer updates. " * 8),
        source="unit",
    )
    summary = trainer.train_model(config=tiny_config())

    assert summary["status"] == "PASS"
    assert summary["metrics"]["parameter_delta_l2"] > 0
    assert Path(summary["checkpoint_path"]).exists()
    assert len(summary["checkpoint_sha256"]) == 64
    assert (tmp_path / "run" / "TRAINING_LEDGER.jsonl").exists()
    assert (tmp_path / "run" / "snapshots" / "latest_training_run.har360.json").exists()

    model, checkpoint = load_trained_language_model(summary["checkpoint_path"])
    assert checkpoint["model_type"] == "TinyCausalLanguageModel"


def test_hybrid_ingests_har360_and_trains_language_model(tmp_path):
    har = tmp_path / "sample.har360.json"
    har.write_text(json.dumps({
        "format": "HAR360",
        "payload": {
            "content": "Harmony360 governed training corpus. " * 8,
            "metadata": {"note": "reconciliation"}
        }
    }))

    trainer = Harmony360HybridTrainer(tmp_path / "hybrid")
    entry = trainer.ingest_har360(har)
    assert "governed training corpus" in entry["content"]

    result = trainer.train_language_model(config=tiny_config())
    assert result["status"] == "PASS"
    assert result["metrics"]["parameter_delta_l2"] > 0


def test_resonance_predictor_is_real_regression(tmp_path):
    trainer = Harmony360HybridTrainer(tmp_path / "hybrid")
    result = trainer.train_resonance_predictor(
        [[0.0], [1.0], [2.0], [3.0]],
        [0.0, 2.0, 4.0, 6.0],
        epochs=120,
        learning_rate=0.03,
    )
    assert result["final_loss"] < result["initial_loss"]


def test_classifier_is_real_parameter_training(tmp_path):
    trainer = Harmony360HybridTrainer(tmp_path / "hybrid")
    result = trainer.train_classifier(
        [[0.0], [0.1], [1.0], [1.1]],
        [0, 0, 1, 1],
        epochs=100,
        learning_rate=0.03,
    )
    assert result["final_loss"] < result["initial_loss"]
    assert result["training_accuracy"] >= 0.75
