from __future__ import annotations

import hashlib
import json
import math
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

from .core import Harmony360
from .ledger import HAR360LedgerManager
from .snapshot import Harmony360Snapshot


@dataclass
class Harmony360TrainingConfig:
    sequence_length: int = 32
    embedding_dim: int = 32
    hidden_dim: int = 64
    batch_size: int = 16
    epochs: int = 3
    learning_rate: float = 3e-3
    weight_decay: float = 0.0
    seed: int = 360
    device: str = "cpu"

    def validate(self) -> None:
        if self.sequence_length < 2:
            raise ValueError("sequence_length must be >= 2")
        if self.embedding_dim < 2 or self.hidden_dim < 2:
            raise ValueError("model dimensions must be >= 2")
        if self.batch_size < 1 or self.epochs < 1:
            raise ValueError("batch_size and epochs must be >= 1")
        if self.learning_rate <= 0:
            raise ValueError("learning_rate must be positive")


class ByteCausalDataset(Dataset):
    """UTF-8 byte next-token dataset."""

    def __init__(self, corpus: bytes, sequence_length: int):
        if len(corpus) <= sequence_length:
            raise ValueError(
                f"Corpus has {len(corpus)} bytes; need more than sequence_length={sequence_length}."
            )
        self.tokens = torch.tensor(list(corpus), dtype=torch.long)
        self.sequence_length = sequence_length

    def __len__(self) -> int:
        return len(self.tokens) - self.sequence_length

    def __getitem__(self, idx: int):
        window = self.tokens[idx : idx + self.sequence_length + 1]
        return window[:-1], window[1:]


class TinyCausalLanguageModel(nn.Module):
    """Verification-scale causal byte language model; not an LLM claim."""

    def __init__(self, vocab_size: int = 256, embedding_dim: int = 32, hidden_dim: int = 64):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim)
        self.rnn = nn.GRU(embedding_dim, hidden_dim, batch_first=True)
        self.head = nn.Linear(hidden_dim, vocab_size)

    def forward(self, input_ids: torch.Tensor) -> torch.Tensor:
        x = self.embedding(input_ids)
        x, _ = self.rnn(x)
        return self.head(x)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _state_vector(model: nn.Module) -> torch.Tensor:
    return torch.cat([p.detach().cpu().reshape(-1) for p in model.parameters()])


class Harmony360Trainer(Harmony360):
    """Canonical Harmony360 model-training foundation.

    Reconciles the historical Trainer class into actual parameter optimization:
    corpus ingestion -> dataset -> model -> loss -> backprop -> optimizer update ->
    checkpoint -> snapshot/ledger evidence.

    Harmony360 governance wraps the training process. This v1 does not claim that
    phi/pi modifications improve learning; those require separate controlled tests.
    """

    def __init__(
        self,
        base_dir: str | Path,
        *,
        ledger_path: str | Path | None = None,
        snapshot_dir: str | Path | None = None,
    ):
        super().__init__()
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.docs: list[dict[str, str]] = []
        self.ledger_path = Path(ledger_path) if ledger_path else self.base_dir / "TRAINING_LEDGER.jsonl"
        self.snapshot_dir = Path(snapshot_dir) if snapshot_dir else self.base_dir / "snapshots"
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)

    def ingest_document(self, path: str | Path) -> dict[str, str]:
        path = Path(path)
        text = path.read_text(encoding="utf-8")
        entry = {
            "path": str(path),
            "content": text,
            "sha256": _sha256_bytes(text.encode("utf-8")),
        }
        self.docs.append(entry)
        return entry

    def ingest_batch(self, file_list: Iterable[str | Path]) -> list[dict[str, str]]:
        return [self.ingest_document(path) for path in file_list]

    def add_text(self, text: str, *, source: str = "memory") -> dict[str, str]:
        entry = {
            "path": source,
            "content": text,
            "sha256": _sha256_bytes(text.encode("utf-8")),
        }
        self.docs.append(entry)
        return entry

    def corpus_text(self) -> str:
        if not self.docs:
            raise ValueError("No documents have been ingested.")
        return "\n".join(d["content"] for d in self.docs)

    def corpus_bytes(self) -> bytes:
        return self.corpus_text().encode("utf-8")

    def _seed(self, seed: int) -> None:
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)

    @staticmethod
    def _mean_loss(model: nn.Module, dataloader: DataLoader, loss_fn: nn.Module, device: torch.device) -> float:
        model.eval()
        losses: list[float] = []
        with torch.no_grad():
            for x, y in dataloader:
                x, y = x.to(device), y.to(device)
                logits = model(x)
                loss = loss_fn(logits.reshape(-1, logits.shape[-1]), y.reshape(-1))
                losses.append(float(loss.item()))
        return float(np.mean(losses)) if losses else math.nan

    def train_model(
        self,
        *,
        config: Harmony360TrainingConfig | None = None,
        checkpoint_name: str = "harmony360_tiny_causal_lm.pt",
    ) -> dict[str, Any]:
        config = config or Harmony360TrainingConfig()
        config.validate()
        self._seed(config.seed)

        corpus = self.corpus_bytes()
        dataset = ByteCausalDataset(corpus, config.sequence_length)
        generator = torch.Generator().manual_seed(config.seed)
        loader = DataLoader(dataset, batch_size=config.batch_size, shuffle=True, generator=generator)

        device = torch.device(config.device)
        model = TinyCausalLanguageModel(
            embedding_dim=config.embedding_dim,
            hidden_dim=config.hidden_dim,
        ).to(device)

        loss_fn = nn.CrossEntropyLoss()
        optimizer = torch.optim.AdamW(
            model.parameters(),
            lr=config.learning_rate,
            weight_decay=config.weight_decay,
        )

        initial_vector = _state_vector(model).clone()
        initial_loss = self._mean_loss(model, loader, loss_fn, device)
        epoch_losses: list[float] = []

        model.train()
        for _epoch in range(config.epochs):
            batch_losses: list[float] = []
            for x, y in loader:
                x, y = x.to(device), y.to(device)
                optimizer.zero_grad(set_to_none=True)
                logits = model(x)
                loss = loss_fn(logits.reshape(-1, logits.shape[-1]), y.reshape(-1))
                loss.backward()
                optimizer.step()
                batch_losses.append(float(loss.item()))
            epoch_losses.append(float(np.mean(batch_losses)))

        final_loss = self._mean_loss(model, loader, loss_fn, device)
        final_vector = _state_vector(model)
        parameter_delta_l2 = float(torch.linalg.vector_norm(final_vector - initial_vector).item())

        checkpoint_path = self.base_dir / checkpoint_name
        checkpoint = {
            "format": "HARMONY360_TRAINING_CHECKPOINT",
            "version": "1.0",
            "model_type": "TinyCausalLanguageModel",
            "model_config": {
                "vocab_size": 256,
                "embedding_dim": config.embedding_dim,
                "hidden_dim": config.hidden_dim,
            },
            "training_config": asdict(config),
            "corpus_sha256": _sha256_bytes(corpus),
            "document_count": len(self.docs),
            "metrics": {
                "initial_loss": initial_loss,
                "epoch_losses": epoch_losses,
                "final_loss": final_loss,
                "parameter_delta_l2": parameter_delta_l2,
            },
            "state_dict": model.state_dict(),
        }
        torch.save(checkpoint, checkpoint_path)
        checkpoint_sha256 = _sha256_bytes(checkpoint_path.read_bytes())

        summary = {
            "capability": "Harmony360Trainer",
            "status": "PASS",
            "claim_type": "engineering/model_training",
            "model_type": "TinyCausalLanguageModel",
            "document_count": len(self.docs),
            "corpus_bytes": len(corpus),
            "corpus_sha256": _sha256_bytes(corpus),
            "training_config": asdict(config),
            "metrics": checkpoint["metrics"],
            "checkpoint_path": str(checkpoint_path),
            "checkpoint_sha256": checkpoint_sha256,
            "scope_of_conclusion": (
                "Confirms that a causal language model's parameters were optimized on the "
                "ingested corpus under the tested configuration. It does not establish "
                "generalization, large-language-model scale, or superiority of Harmony360 "
                "mathematical modifications."
            ),
        }

        snapper = Harmony360Snapshot()
        snapshot = snapper.save_state(
            summary,
            label="training_run",
            source="Harmony360Trainer.train_model",
            lineage="historical trainer -> canonical real training v1",
            metadata={"claim_type": "engineering/model_training"},
        )
        snapshot_path = self.snapshot_dir / "latest_training_run.har360.json"
        snapper.export_snapshot(snapshot, snapshot_path)

        ledger = HAR360LedgerManager(self.ledger_path)
        ledger.append_entry(
            event_type="MODEL_TRAINED",
            artifact_id=checkpoint_path.name,
            artifact_sha256=checkpoint_sha256,
            status="PASS",
            lineage="historical trainer -> canonical real training v1",
            metadata={
                "snapshot": str(snapshot_path),
                "corpus_sha256": summary["corpus_sha256"],
                "parameter_delta_l2": parameter_delta_l2,
                "initial_loss": initial_loss,
                "final_loss": final_loss,
            },
        )
        return summary

    def update_training(
        self,
        *,
        config: Harmony360TrainingConfig | None = None,
        checkpoint_name: str = "harmony360_tiny_causal_lm_updated.pt",
    ) -> dict[str, Any]:
        """Train a new governed checkpoint from the current corpus.

        v1 intentionally does not pretend to resume optimizer state from an old checkpoint.
        """
        return self.train_model(config=config, checkpoint_name=checkpoint_name)


class Harmony360HybridTrainer(Harmony360Trainer):
    """Trainer accepting canonical/historical .har360 JSON plus ordinary text."""

    @staticmethod
    def _extract_text(value: Any) -> list[str]:
        texts: list[str] = []
        if isinstance(value, str):
            if value.strip():
                texts.append(value)
        elif isinstance(value, dict):
            for key in ("content", "text", "message", "body", "payload", "state"):
                if key in value:
                    texts.extend(Harmony360HybridTrainer._extract_text(value[key]))
            for key, item in value.items():
                if key not in {"content", "text", "message", "body", "payload", "state"}:
                    texts.extend(Harmony360HybridTrainer._extract_text(item))
        elif isinstance(value, (list, tuple)):
            for item in value:
                texts.extend(Harmony360HybridTrainer._extract_text(item))
        return texts

    def ingest_har360(self, path: str | Path) -> dict[str, str]:
        path = Path(path)
        data = json.loads(path.read_text(encoding="utf-8"))
        chunks = self._extract_text(data)
        content = "\n".join(chunks).strip()
        if not content:
            raise ValueError(f"No textual training content found in {path}")
        entry = {
            "path": str(path),
            "content": content,
            "sha256": _sha256_bytes(content.encode("utf-8")),
        }
        self.docs.append(entry)
        return entry

    def train_language_model(
        self,
        export_path: str | Path | None = None,
        *,
        config: Harmony360TrainingConfig | None = None,
    ) -> dict[str, Any]:
        export_path = Path(export_path) if export_path else self.base_dir / "harmony360_hybrid_lm.pt"
        export_path.parent.mkdir(parents=True, exist_ok=True)
        summary = self.train_model(config=config, checkpoint_name=export_path.name)
        produced = self.base_dir / export_path.name
        if produced.resolve() != export_path.resolve():
            produced.replace(export_path)
            summary["checkpoint_path"] = str(export_path)
            summary["checkpoint_sha256"] = _sha256_bytes(export_path.read_bytes())
        summary["capability"] = "Harmony360HybridTrainer.train_language_model"
        return summary

    def train_resonance_predictor(
        self,
        features: Sequence[Sequence[float]],
        targets: Sequence[float],
        *,
        epochs: int = 100,
        learning_rate: float = 1e-2,
        seed: int = 360,
    ) -> dict[str, Any]:
        """Train a numeric regressor for caller-supplied targets.

        'Resonance' is a task label here, not an assertion of a physical quantity.
        """
        x = torch.tensor(np.asarray(features, dtype=np.float32))
        y = torch.tensor(np.asarray(targets, dtype=np.float32)).reshape(-1, 1)
        if x.ndim != 2 or len(x) != len(y) or len(x) < 2:
            raise ValueError("features must be 2-D and align with at least two targets")

        self._seed(seed)
        width = max(4, x.shape[1] * 2)
        model = nn.Sequential(nn.Linear(x.shape[1], width), nn.Tanh(), nn.Linear(width, 1))
        optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
        loss_fn = nn.MSELoss()
        with torch.no_grad():
            initial_loss = float(loss_fn(model(x), y).item())
        for _ in range(epochs):
            optimizer.zero_grad(set_to_none=True)
            loss = loss_fn(model(x), y)
            loss.backward()
            optimizer.step()
        with torch.no_grad():
            final_loss = float(loss_fn(model(x), y).item())
        return {
            "status": "PASS",
            "task": "regression",
            "initial_loss": initial_loss,
            "final_loss": final_loss,
            "samples": len(x),
            "scope_of_conclusion": "Verifies numeric regression mechanics for caller-supplied targets.",
        }

    def train_classifier(
        self,
        features: Sequence[Sequence[float]],
        labels: Sequence[int],
        *,
        epochs: int = 100,
        learning_rate: float = 1e-2,
        seed: int = 360,
    ) -> dict[str, Any]:
        x = torch.tensor(np.asarray(features, dtype=np.float32))
        y = torch.tensor(np.asarray(labels, dtype=np.int64))
        if x.ndim != 2 or len(x) != len(y) or len(x) < 2:
            raise ValueError("features must be 2-D and align with at least two labels")
        classes = int(y.max().item()) + 1
        if classes < 2:
            raise ValueError("classifier requires at least two classes")

        self._seed(seed)
        width = max(4, x.shape[1] * 2)
        model = nn.Sequential(nn.Linear(x.shape[1], width), nn.ReLU(), nn.Linear(width, classes))
        optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
        loss_fn = nn.CrossEntropyLoss()
        with torch.no_grad():
            initial_loss = float(loss_fn(model(x), y).item())
        for _ in range(epochs):
            optimizer.zero_grad(set_to_none=True)
            loss = loss_fn(model(x), y)
            loss.backward()
            optimizer.step()
        with torch.no_grad():
            logits = model(x)
            final_loss = float(loss_fn(logits, y).item())
            accuracy = float((logits.argmax(dim=1) == y).float().mean().item())
        return {
            "status": "PASS",
            "task": "classification",
            "initial_loss": initial_loss,
            "final_loss": final_loss,
            "training_accuracy": accuracy,
            "samples": len(x),
            "scope_of_conclusion": (
                "Verifies classifier training mechanics on supplied training samples; "
                "training accuracy is not an out-of-sample performance estimate."
            ),
        }


def load_trained_language_model(checkpoint_path: str | Path, device: str = "cpu"):
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)
    if checkpoint.get("format") != "HARMONY360_TRAINING_CHECKPOINT":
        raise ValueError("Not a Harmony360 training checkpoint")
    cfg = checkpoint["model_config"]
    model = TinyCausalLanguageModel(
        vocab_size=cfg["vocab_size"],
        embedding_dim=cfg["embedding_dim"],
        hidden_dim=cfg["hidden_dim"],
    )
    model.load_state_dict(checkpoint["state_dict"])
    model.to(device).eval()
    return model, checkpoint
