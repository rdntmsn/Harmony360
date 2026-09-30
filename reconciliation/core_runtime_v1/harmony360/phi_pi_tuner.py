from __future__ import annotations

import hashlib
import json
import math
import random
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader

from .constants import PHI, PI
from .core import Harmony360
from .ledger import HAR360LedgerManager
from .snapshot import Harmony360Snapshot
from .trainer import ByteCausalDataset, TinyCausalLanguageModel


@dataclass(frozen=True)
class TuningCandidate:
    name: str
    value: float
    family: str = "control"


DEFAULT_CANDIDATES = (
    TuningCandidate("baseline", 1.0, "baseline"),
    TuningCandidate("phi", float(PHI), "harmony360"),
    TuningCandidate("sqrt2", math.sqrt(2.0), "control"),
    TuningCandidate("one_point_five", 1.5, "control"),
    TuningCandidate("e_over_2", math.e / 2.0, "control"),
    TuningCandidate("pi_over_2", float(PI) / 2.0, "control"),
)


@dataclass
class AblationConfig:
    sequence_length: int = 12
    embedding_dim: int = 12
    hidden_dim: int = 24
    batch_size: int = 16
    epochs: int = 2
    learning_rate: float = 1e-2
    seeds: tuple[int, ...] = (13, 36, 69)
    device: str = "cpu"
    validation_fraction: float = 0.2

    def validate(self) -> None:
        if self.sequence_length < 2:
            raise ValueError("sequence_length must be >= 2")
        if self.embedding_dim < 2 or self.hidden_dim < 2:
            raise ValueError("model dimensions must be >= 2")
        if self.batch_size < 1 or self.epochs < 1:
            raise ValueError("batch_size and epochs must be >= 1")
        if self.learning_rate <= 0:
            raise ValueError("learning_rate must be positive")
        if not self.seeds:
            raise ValueError("at least one seed is required")
        if not 0.1 <= self.validation_fraction <= 0.4:
            raise ValueError("validation_fraction must be between 0.1 and 0.4")


class PhiPiTuner(Harmony360):
    """Governed constant tuner and controlled training-ablation harness.

    Historical lineage: PhiPiTuner.optimize_parameters / export_best_fit_results.
    Reconciliation boundary: phi/pi are candidates, not privileged conclusions.
    The tuner compares Harmony360 constants against explicit controls under the
    same model, corpus, seeds, and training budget.
    """

    FORMAT = "HARMONY360_PHI_PI_TUNER"
    VERSION = "1.0"

    def __init__(
        self,
        base_dir: str | Path,
        *,
        candidates: Sequence[TuningCandidate] = DEFAULT_CANDIDATES,
    ):
        super().__init__()
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.candidates = tuple(candidates)
        self.last_result: dict[str, Any] | None = None

    @staticmethod
    def _seed(seed: int) -> None:
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)

    @staticmethod
    def _mean_loss(
        model: nn.Module,
        loader: DataLoader,
        loss_fn: nn.Module,
        device: torch.device,
    ) -> float:
        model.eval()
        losses: list[float] = []
        with torch.no_grad():
            for x, y in loader:
                x, y = x.to(device), y.to(device)
                logits = model(x)
                loss = loss_fn(logits.reshape(-1, logits.shape[-1]), y.reshape(-1))
                losses.append(float(loss.item()))
        return float(np.mean(losses)) if losses else math.nan

    def optimize_parameters(
        self,
        simulation_id: str,
        objective,
        *,
        candidates: Sequence[TuningCandidate] | None = None,
        maximize: bool = False,
    ) -> dict[str, Any]:
        """Evaluate every declared candidate with a caller-supplied objective."""
        pool = tuple(candidates or self.candidates)
        if not pool:
            raise ValueError("candidate list cannot be empty")

        records = []
        for candidate in pool:
            score = float(objective(candidate))
            if not math.isfinite(score):
                raise ValueError(f"non-finite score for {candidate.name}")
            records.append({**asdict(candidate), "score": score})

        ranked = sorted(records, key=lambda r: r["score"], reverse=maximize)
        result = {
            "format": self.FORMAT,
            "version": self.VERSION,
            "simulation_id": simulation_id,
            "objective_direction": "maximize" if maximize else "minimize",
            "results": records,
            "ranking": ranked,
            "best": ranked[0],
            "scope_of_conclusion": (
                "Ranks declared candidates only for the supplied objective and tested conditions. "
                "A phi/pi candidate is not privileged and may lose to controls."
            ),
        }
        self.last_result = result
        return result

    def run_language_model_ablation(
        self,
        corpus_text: str,
        *,
        simulation_id: str = "phi_pi_lm_ablation_v1",
        mode: str = "lr_decay",
        config: AblationConfig | None = None,
        candidates: Sequence[TuningCandidate] | None = None,
    ) -> dict[str, Any]:
        """Compare constants in a controlled verification-scale LM experiment.

        Modes:
        - lr_decay: after each epoch, lr <- base_lr / candidate.value**epoch.
        - init_scale: multiply the common seeded initial parameter state by the
          candidate value before training.

        Every candidate uses identical architecture, corpus split, seeds, epochs,
        optimizer family, and batch budget.
        """
        config = config or AblationConfig()
        config.validate()
        if mode not in {"lr_decay", "init_scale"}:
            raise ValueError("mode must be 'lr_decay' or 'init_scale'")

        corpus = corpus_text.encode("utf-8")
        min_bytes = (config.sequence_length + 2) * 2
        if len(corpus) < min_bytes:
            raise ValueError(f"corpus too small; need at least {min_bytes} bytes")

        split = int(len(corpus) * (1.0 - config.validation_fraction))
        split = max(config.sequence_length + 2, split)
        split = min(split, len(corpus) - config.sequence_length - 2)
        train_bytes = corpus[:split]
        val_bytes = corpus[split:]

        train_ds = ByteCausalDataset(train_bytes, config.sequence_length)
        val_ds = ByteCausalDataset(val_bytes, config.sequence_length)
        pool = tuple(candidates or self.candidates)
        loss_fn = nn.CrossEntropyLoss()
        device = torch.device(config.device)
        records: list[dict[str, Any]] = []

        for seed in config.seeds:
            self._seed(seed)
            reference = TinyCausalLanguageModel(
                embedding_dim=config.embedding_dim,
                hidden_dim=config.hidden_dim,
            )
            reference_state = {
                key: value.detach().clone()
                for key, value in reference.state_dict().items()
            }

            for candidate in pool:
                self._seed(seed)
                model = TinyCausalLanguageModel(
                    embedding_dim=config.embedding_dim,
                    hidden_dim=config.hidden_dim,
                ).to(device)
                model.load_state_dict(reference_state)

                if mode == "init_scale":
                    with torch.no_grad():
                        for parameter in model.parameters():
                            parameter.mul_(candidate.value)

                train_gen = torch.Generator().manual_seed(seed)
                train_loader = DataLoader(
                    train_ds,
                    batch_size=config.batch_size,
                    shuffle=True,
                    generator=train_gen,
                )
                val_loader = DataLoader(
                    val_ds,
                    batch_size=config.batch_size,
                    shuffle=False,
                )
                optimizer = torch.optim.AdamW(model.parameters(), lr=config.learning_rate)

                initial_val_loss = self._mean_loss(model, val_loader, loss_fn, device)
                epoch_train_losses: list[float] = []

                for epoch in range(config.epochs):
                    if mode == "lr_decay":
                        lr = config.learning_rate / (candidate.value ** epoch)
                        for group in optimizer.param_groups:
                            group["lr"] = lr

                    model.train()
                    batch_losses: list[float] = []
                    for x, y in train_loader:
                        x, y = x.to(device), y.to(device)
                        optimizer.zero_grad(set_to_none=True)
                        logits = model(x)
                        loss = loss_fn(
                            logits.reshape(-1, logits.shape[-1]),
                            y.reshape(-1),
                        )
                        loss.backward()
                        optimizer.step()
                        batch_losses.append(float(loss.item()))
                    epoch_train_losses.append(float(np.mean(batch_losses)))

                final_val_loss = self._mean_loss(model, val_loader, loss_fn, device)
                records.append(
                    {
                        "candidate": candidate.name,
                        "candidate_value": candidate.value,
                        "candidate_family": candidate.family,
                        "seed": seed,
                        "mode": mode,
                        "initial_validation_loss": initial_val_loss,
                        "final_validation_loss": final_val_loss,
                        "epoch_train_losses": epoch_train_losses,
                    }
                )

        aggregate = []
        for candidate in pool:
            rows = [r for r in records if r["candidate"] == candidate.name]
            vals = np.asarray([r["final_validation_loss"] for r in rows], dtype=float)
            aggregate.append(
                {
                    **asdict(candidate),
                    "runs": len(rows),
                    "mean_final_validation_loss": float(vals.mean()),
                    "std_final_validation_loss": float(vals.std(ddof=0)),
                }
            )

        ranking = sorted(aggregate, key=lambda r: r["mean_final_validation_loss"])
        phi_row = next((r for r in aggregate if r["name"] == "phi"), None)
        baseline_row = next((r for r in aggregate if r["name"] == "baseline"), None)

        result = {
            "format": "HARMONY360_TRAINING_ABLATION",
            "version": "1.0",
            "simulation_id": simulation_id,
            "mode": mode,
            "config": asdict(config),
            "candidate_count": len(pool),
            "run_count": len(records),
            "records": records,
            "aggregate": aggregate,
            "ranking": ranking,
            "best_observed_candidate": ranking[0],
            "phi_vs_baseline": (
                None
                if phi_row is None or baseline_row is None
                else {
                    "phi_mean_validation_loss": phi_row["mean_final_validation_loss"],
                    "baseline_mean_validation_loss": baseline_row["mean_final_validation_loss"],
                    "difference_phi_minus_baseline": (
                        phi_row["mean_final_validation_loss"]
                        - baseline_row["mean_final_validation_loss"]
                    ),
                }
            ),
            "scope_of_conclusion": (
                "Controlled verification-scale comparison of declared constants under identical "
                "architecture, data split, seeds, optimizer family, and training budget. It does "
                "not establish universal superiority of any constant or Harmony360 mechanism."
            ),
        }

        out_path = self.base_dir / f"{simulation_id}_{mode}.har360.json"
        out_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
        result["result_path"] = str(out_path)

        snapper = Harmony360Snapshot()
        snapshot = snapper.save_state(
            result,
            label="phi_pi_ablation",
            source="PhiPiTuner.run_language_model_ablation",
            lineage="historical PhiPiTuner -> governed controlled ablation v1",
            metadata={"claim_type": "experimental/model_training_ablation"},
        )
        snapshot_path = self.base_dir / f"{simulation_id}_{mode}_snapshot.har360.json"
        snapper.export_snapshot(snapshot, snapshot_path)

        artifact_sha256 = hashlib.sha256(out_path.read_bytes()).hexdigest()
        ledger = HAR360LedgerManager(self.base_dir / "PHI_PI_TUNER_LEDGER.jsonl")
        ledger.append_entry(
            event_type="PHI_PI_ABLATION_COMPLETED",
            artifact_id=out_path.name,
            artifact_sha256=artifact_sha256,
            status="PASS",
            lineage="historical PhiPiTuner -> governed controlled ablation v1",
            metadata={
                "mode": mode,
                "run_count": len(records),
                "best_observed_candidate": ranking[0]["name"],
            },
        )

        self.last_result = result
        return result

    def export_best_fit_results(self, path: str | Path | None = None) -> Path:
        if self.last_result is None:
            raise ValueError("No tuning result is available to export.")
        target = Path(path) if path else self.base_dir / "PHI_PI_TUNER_BEST_FIT.har360.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.last_result, indent=2, sort_keys=True), encoding="utf-8")
        return target
