from .constants import PHI, PI, ALPHA, ALPHA_LEGACY, PLANCK_LENGTH, HBAR, C
from .core import Harmony360, Harmony360CoreIdentity
from .evidence import EvidenceRecord
from .serialization import save_har360, load_har360
from .snapshot import Harmony360Snapshot
from .ledger import HAR360LedgerManager
from .sync import h360_sync
from .trainer import (
    Harmony360Trainer,
    Harmony360HybridTrainer,
    Harmony360TrainingConfig,
    TinyCausalLanguageModel,
    load_trained_language_model,
)
from .measurement import Harmony360MeasurementContract, MeasurementSemantics
from .phi_pi_tuner import (
    PhiPiTuner,
    TuningCandidate,
    AblationConfig,
    DEFAULT_CANDIDATES,
)
from .fractal_reproduction import (
    ConventionalMLP,
    FractalBranchMLP,
    FractalReproductionConfig,
    FractalStructureReproduction,
    trainable_parameters,
)

__all__ = [
    "Harmony360",
    "Harmony360CoreIdentity",
    "EvidenceRecord",
    "Harmony360Snapshot",
    "HAR360LedgerManager",
    "h360_sync",
    "Harmony360Trainer",
    "Harmony360HybridTrainer",
    "Harmony360TrainingConfig",
    "TinyCausalLanguageModel",
    "load_trained_language_model",
    "Harmony360MeasurementContract",
    "MeasurementSemantics",
    "PhiPiTuner",
    "TuningCandidate",
    "AblationConfig",
    "DEFAULT_CANDIDATES",
    "ConventionalMLP",
    "FractalBranchMLP",
    "FractalReproductionConfig",
    "FractalStructureReproduction",
    "trainable_parameters",
    "PHI", "PI", "ALPHA", "ALPHA_LEGACY", "PLANCK_LENGTH", "HBAR", "C",
    "save_har360", "load_har360",
]

__version__ = "1.5.0"
