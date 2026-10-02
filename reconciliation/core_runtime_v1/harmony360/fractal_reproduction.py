from __future__ import annotations

import hashlib
import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from .ledger import HAR360LedgerManager
from .measurement import Harmony360MeasurementContract, MeasurementSemantics
from .snapshot import Harmony360Snapshot


class ConventionalMLP(nn.Module):
    """Parameter-matched conventional MNIST MLP: 784 -> 128 -> 128 -> 10."""

    def __init__(self) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(784, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, 10),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x.reshape(x.shape[0], -1))


class FractalBranchMLP(nn.Module):
    """Parameter-matched branching topology for the recovered fractal-structure question.

    784 -> 128 trunk -> two parallel 128 -> 64 branches -> concat(128) -> 10.

    This is a governed reconstruction of the structural hypothesis, not a claim
    that the exact historical 2026 topology was recovered.
    """

    def __init__(self) -> None:
        super().__init__()
        self.trunk = nn.Linear(784, 128)
        self.branch_a = nn.Linear(128, 64)
        self.branch_b = nn.Linear(128, 64)
        self.head = nn.Linear(128, 10)
        self.activation = nn.ReLU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x.reshape(x.shape[0], -1)
        trunk = self.activation(self.trunk(x))
        a = self.activation(self.branch_a(trunk))
        b = self.activation(self.branch_b(trunk))
        return self.head(torch.cat([a, b], dim=-1))


def trainable_parameters(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


@dataclass
class FractalReproductionConfig:
    batch_size: int = 128
    epochs: int = 3
    learning_rate: float = 1e-3
    seeds: tuple[int, ...] = (13, 36, 69)
    device: str = "cpu"

    def validate(self) -> None:
        if self.batch_size < 1 or self.epochs < 1:
            raise ValueError("batch_size and epochs must be >= 1")
        if self.learning_rate <= 0:
            raise ValueError("learning_rate must be positive")
        if not self.seeds:
            raise ValueError("at least one seed is required")


class FractalStructureReproduction(Harmony360MeasurementContract):
    """Controlled reproduction harness for the recovered fractal-structure claim."""

    VERSION = "1.0"

    def __init__(self, base_dir: str | Path):
        super().__init__()
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _seed(seed: int) -> None:
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)

    @staticmethod
    def _evaluate(model: nn.Module, loader: DataLoader, device: torch.device) -> tuple[float, float]:
        loss_fn = nn.CrossEntropyLoss()
        model.eval()
        total_loss = 0.0
        total_correct = 0
        total = 0
        with torch.no_grad():
            for x, y in loader:
                x, y = x.to(device), y.to(device)
                logits = model(x)
                loss = loss_fn(logits, y)
                total_loss += float(loss.item()) * len(y)
                total_correct += int((logits.argmax(dim=1) == y).sum().item())
                total += len(y)
        return total_loss / total, total_correct / total

    def _run_arm(
        self,
        model: nn.Module,
        train_loader: DataLoader,
        test_loader: DataLoader,
        *,
        epochs: int,
        learning_rate: float,
        device: torch.device,
    ) -> dict[str, Any]:
        model = model.to(device)
        optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
        loss_fn = nn.CrossEntropyLoss()
        history = []

        for epoch in range(1, epochs + 1):
            model.train()
            train_loss_total = 0.0
            seen = 0
            for x, y in train_loader:
                x, y = x.to(device), y.to(device)
                optimizer.zero_grad(set_to_none=True)
                logits = model(x)
                loss = loss_fn(logits, y)
                loss.backward()
                optimizer.step()
                train_loss_total += float(loss.item()) * len(y)
                seen += len(y)

            test_loss, test_accuracy = self._evaluate(model, test_loader, device)
            history.append(
                {
                    "epoch": epoch,
                    "train_loss": train_loss_total / seen,
                    "test_loss": test_loss,
                    "test_accuracy": test_accuracy,
                }
            )

        return {
            "parameters": trainable_parameters(model),
            "history": history,
            "final_train_loss": history[-1]["train_loss"],
            "final_test_loss": history[-1]["test_loss"],
            "final_test_accuracy": history[-1]["test_accuracy"],
        }

    def run(
        self,
        train_x: torch.Tensor,
        train_y: torch.Tensor,
        test_x: torch.Tensor,
        test_y: torch.Tensor,
        *,
        config: FractalReproductionConfig | None = None,
        simulation_id: str = "fractal_structure_reproduction_v1",
    ) -> dict[str, Any]:
        config = config or FractalReproductionConfig()
        config.validate()

        control_params = trainable_parameters(ConventionalMLP())
        fractal_params = trainable_parameters(FractalBranchMLP())
        if control_params != fractal_params:
            raise AssertionError("control and fractal treatment must have exactly equal trainable parameters")

        device = torch.device(config.device)
        records: list[dict[str, Any]] = []
        experiments: list[dict[str, Any]] = []
        comparisons: list[dict[str, Any]] = []

        for seed in config.seeds:
            self._seed(seed)
            generator = torch.Generator().manual_seed(seed)
            train_loader = DataLoader(
                TensorDataset(train_x, train_y),
                batch_size=config.batch_size,
                shuffle=True,
                generator=generator,
            )
            test_loader = DataLoader(
                TensorDataset(test_x, test_y),
                batch_size=config.batch_size,
                shuffle=False,
            )

            self._seed(seed)
            control_result = self._run_arm(
                ConventionalMLP(), train_loader, test_loader,
                epochs=config.epochs, learning_rate=config.learning_rate, device=device,
            )

            # Recreate the loader with the same seed so batch order is identical.
            generator = torch.Generator().manual_seed(seed)
            train_loader = DataLoader(
                TensorDataset(train_x, train_y),
                batch_size=config.batch_size,
                shuffle=True,
                generator=generator,
            )

            self._seed(seed)
            fractal_result = self._run_arm(
                FractalBranchMLP(), train_loader, test_loader,
                epochs=config.epochs, learning_rate=config.learning_rate, device=device,
            )

            def arm_record(name: str, result: dict[str, Any], fractal_on: bool) -> dict[str, Any]:
                losses = [row["test_loss"] for row in result["history"]]
                accuracies = [row["test_accuracy"] for row in result["history"]]
                return self.build_arm_record(
                    arm_name=name,
                    domain_metrics={
                        "parameters": result["parameters"],
                        "final_test_loss": result["final_test_loss"],
                        "final_test_accuracy": result["final_test_accuracy"],
                    },
                    measured_series={
                        "test_loss": self.measure_series(
                            losses,
                            semantics=MeasurementSemantics(
                                label="test_loss",
                                value_units="cross_entropy",
                                coordinate_units="epoch",
                                interpretation="MNIST test cross-entropy trajectory",
                            ),
                            coordinates=list(range(1, len(losses) + 1)),
                        ),
                        "test_accuracy": self.measure_series(
                            accuracies,
                            semantics=MeasurementSemantics(
                                label="test_accuracy",
                                value_units="fraction_correct",
                                coordinate_units="epoch",
                                interpretation="MNIST test-accuracy trajectory",
                            ),
                            coordinates=list(range(1, len(accuracies) + 1)),
                        ),
                    },
                    intervention_flags={
                        "harmony360_measurement": True,
                        "fractal_structure_intervention": fractal_on,
                        "phi_pi_modulation_intervention": False,
                        "recl_intervention": False,
                    },
                )

            control_arm = arm_record("parameter_matched_control", control_result, False)
            fractal_arm = arm_record("fractal_branch_treatment", fractal_result, True)
            experiment = {
                "format": "HARMONY360_EXPERIMENT_RECORD",
                "version": "1.0",
                "seed": seed,
                "arms": [control_arm, fractal_arm],
            }
            if not self.validate_experiment_record(experiment):
                raise AssertionError("measurement contract validation failed")

            comparison = self.compare_arms(
                control_arm,
                fractal_arm,
                domain_metric="final_test_accuracy",
                measured_series_key="test_accuracy",
            )
            experiments.append(experiment)
            comparisons.append(comparison)
            records.extend([
                {"seed": seed, "variant": "parameter_matched_control", **control_result},
                {"seed": seed, "variant": "fractal_branch_treatment", **fractal_result},
            ])

        def aggregate(variant: str) -> dict[str, Any]:
            rows = [r for r in records if r["variant"] == variant]
            acc = np.asarray([r["final_test_accuracy"] for r in rows], dtype=float)
            loss = np.asarray([r["final_test_loss"] for r in rows], dtype=float)
            return {
                "variant": variant,
                "runs": len(rows),
                "parameters": rows[0]["parameters"],
                "mean_final_test_accuracy": float(acc.mean()),
                "std_final_test_accuracy": float(acc.std(ddof=0)),
                "mean_final_test_loss": float(loss.mean()),
                "std_final_test_loss": float(loss.std(ddof=0)),
            }

        control_agg = aggregate("parameter_matched_control")
        fractal_agg = aggregate("fractal_branch_treatment")

        result = {
            "format": "HARMONY360_FRACTAL_STRUCTURE_REPRODUCTION",
            "version": self.VERSION,
            "simulation_id": simulation_id,
            "historical_lineage": {
                "source": "HAR360AI-FNN recovery spike 2026-08-16",
                "historical_baseline_parameters": 118282,
                "historical_fractal_parameters": 151562,
                "historical_confound": "parameter_count_mismatch",
                "reconstruction_note": (
                    "Exact historical topology was not located in the recovered spike artifacts. "
                    "This v1 tests the surviving fractal/branching structural question with exact "
                    "parameter matching rather than claiming byte-for-byte historical reproduction."
                ),
            },
            "null_hypothesis": (
                "Under matched parameter count, data, seeds, optimizer, epochs, and batch order, "
                "the fractal branching topology does not improve held-out classification accuracy "
                "relative to the conventional MLP."
            ),
            "config": asdict(config),
            "parameter_match": {
                "control": control_params,
                "fractal_treatment": fractal_params,
                "exact_match": control_params == fractal_params,
            },
            "records": records,
            "aggregate": [control_agg, fractal_agg],
            "accuracy_delta_fractal_minus_control": (
                fractal_agg["mean_final_test_accuracy"] - control_agg["mean_final_test_accuracy"]
            ),
            "experiments": experiments,
            "comparisons": comparisons,
            "scope_of_conclusion": (
                "Tests one parameter-matched branching reconstruction of the historical fractal-structure "
                "question. Both arms are measured through the canonical Harmony360 measurement contract. "
                "A positive result supports this tested topology under these conditions; it does not establish "
                "that fractal structure is universally superior or that this is the exact historical implementation."
            ),
        }

        out_path = self.base_dir / f"{simulation_id}.har360.json"
        out_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
        result["result_path"] = str(out_path)

        snapper = Harmony360Snapshot()
        snapshot = snapper.save_state(
            result,
            label="fractal_structure_reproduction",
            source="FractalStructureReproduction.run",
            lineage="historical FNN fractal structure -> parameter-matched governed reproduction v1",
            metadata={"claim_type": "experimental/model_architecture_ablation"},
        )
        snapshot_path = self.base_dir / f"{simulation_id}_snapshot.har360.json"
        snapper.export_snapshot(snapshot, snapshot_path)

        artifact_sha256 = hashlib.sha256(out_path.read_bytes()).hexdigest()
        ledger = HAR360LedgerManager(self.base_dir / "FRACTAL_STRUCTURE_LEDGER.jsonl")
        ledger.append_entry(
            event_type="FRACTAL_STRUCTURE_REPRODUCTION_COMPLETED",
            artifact_id=out_path.name,
            artifact_sha256=artifact_sha256,
            status="PASS",
            lineage="historical FNN fractal structure -> parameter-matched governed reproduction v1",
            metadata={
                "run_count": len(records),
                "parameter_match": True,
                "accuracy_delta_fractal_minus_control": result["accuracy_delta_fractal_minus_control"],
            },
        )
        return result
