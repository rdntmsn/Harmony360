from __future__ import annotations

from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional
from collections import Counter
import functools
import hashlib
import json
import math
import os
import uuid

# ============================================================
# Harmony360 Original Core Reconstruction
# Pre-product lineage: v10, v11, v12, v13, h360_canonical,
# harmony360_core, .har360 exports, system overview files.
# ============================================================

PHI = (1 + math.sqrt(5)) / 2
PI = math.pi
TAU = 2 * math.pi
FINE_STRUCTURE_CONSTANT = 1 / 137
ALPHA = FINE_STRUCTURE_CONSTANT
PLANCK_LENGTH = 1.616255e-35
HBAR = 1.054571817e-34
C = 299_792_458
G = 6.67430e-11
HARMONY_ETA = PHI * PI + ALPHA
CHI = math.log(PHI) / PI


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def _json_default(obj: Any):
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return str(obj)


def _normalize_vector(values: Iterable[float]) -> List[float]:
    vector = [_safe_float(v) for v in values]
    mag = math.sqrt(sum(v * v for v in vector))
    if mag == 0:
        return vector
    return [v / mag for v in vector]


def h360_sync(func: Optional[Callable] = None, *, ledger_path: Optional[str | Path] = None, tags: Optional[List[str]] = None):
    def decorator(fn: Callable):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            started = datetime.now()
            event = {
                "event_id": "h360sync_" + uuid.uuid4().hex[:12],
                "function": fn.__name__,
                "module": getattr(fn, "__module__", ""),
                "started_at": started.isoformat(),
                "tags": tags or [],
                "status": "RUNNING",
            }
            try:
                result = fn(*args, **kwargs)
                event["status"] = "OK"
                event["result_type"] = type(result).__name__
                return result
            except Exception as exc:
                event["status"] = "ERROR"
                event["error"] = repr(exc)
                raise
            finally:
                finished = datetime.now()
                event["finished_at"] = finished.isoformat()
                event["duration_seconds"] = (finished - started).total_seconds()
                event["sha256"] = _sha256_text(json.dumps(event, sort_keys=True, default=_json_default))

                target = ledger_path or os.environ.get("H360_SYNC_LEDGER", "")
                if target:
                    try:
                        p = Path(target)
                        p.parent.mkdir(parents=True, exist_ok=True)
                        with p.open("a", encoding="utf-8") as f:
                            f.write(json.dumps(event, default=_json_default) + "\n")
                    except Exception:
                        pass

        wrapper.__h360_sync__ = True
        return wrapper

    if callable(func):
        return decorator(func)
    return decorator


@dataclass
class HAR360Record:
    record_id: str
    created_at: str
    source: str
    kind: str
    payload: Dict[str, Any]
    tags: List[str] = field(default_factory=list)
    resonance_anchor: Optional[float] = None
    guardian_status: str = "UNREVIEWED"
    sha256: str = ""

    def finalize(self):
        material = json.dumps({
            "record_id": self.record_id,
            "created_at": self.created_at,
            "source": self.source,
            "kind": self.kind,
            "payload": self.payload,
            "tags": self.tags,
            "resonance_anchor": self.resonance_anchor,
            "guardian_status": self.guardian_status,
        }, sort_keys=True, default=_json_default)
        self.sha256 = _sha256_text(material)
        return self

    def to_dict(self):
        return asdict(self)


class HAR360Converter:
    extension = ".har360"

    def __init__(self, output_dir: str | Path = "./har360_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def resonance_anchor(self, payload: Dict[str, Any]) -> float:
        text = json.dumps(payload, sort_keys=True, default=_json_default)
        raw = sum(ord(ch) for ch in text)
        return float((raw % 360) / 360)

    def encode_payload(self, payload: Any, source: str = "runtime", kind: str = "memory", tags: Optional[List[str]] = None):
        if not isinstance(payload, dict):
            payload = {"value": payload}
        rec = HAR360Record(
            record_id="har360_" + uuid.uuid4().hex[:16],
            created_at=datetime.now().isoformat(),
            source=source,
            kind=kind,
            payload=payload,
            tags=tags or [],
            resonance_anchor=self.resonance_anchor(payload),
        )
        return rec.finalize()

    def write(self, payload: Any, name: Optional[str] = None, source: str = "runtime", kind: str = "memory", tags: Optional[List[str]] = None):
        rec = self.encode_payload(payload, source=source, kind=kind, tags=tags)
        safe = "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in (name or rec.record_id))
        if not safe.endswith(self.extension):
            safe += self.extension
        path = self.output_dir / safe
        path.write_text(json.dumps(rec.to_dict(), indent=2), encoding="utf-8")
        return path

    def read(self, path: str | Path):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return HAR360Record(**data)


class Harmony360:
    def __init__(self, memory_dir: str | Path = "./har360_output"):
        self.phi = PHI
        self.pi = PI
        self.tau = TAU
        self.alpha = ALPHA
        self.hbar = HBAR
        self.c = C
        self.G = G
        self.lp = PLANCK_LENGTH
        self.eta = HARMONY_ETA
        self.chi = CHI
        self.memory = HAR360Converter(memory_dir)

    def harmonic_eta(self) -> float:
        return self.phi * self.pi + self.alpha

    def harmonic_energy(self, frequency: float) -> float:
        return self.hbar * _safe_float(frequency) * self.harmonic_eta()

    def phi_scale(self, value: float, layer: int = 1) -> float:
        return _safe_float(value) * (self.phi ** int(layer))

    def inverse_phi_scale(self, value: float, layer: int = 1) -> float:
        return _safe_float(value) / (self.phi ** int(layer))

    def resonance(self, values: Iterable[float]) -> float:
        values = [_safe_float(v) for v in values]
        if not values:
            return 0.0
        normalized = _normalize_vector(values)
        phase_sum = sum(math.sin((i + 1) * v * self.phi) for i, v in enumerate(normalized))
        return max(0.0, min(1.0, (phase_sum / len(normalized) + 1) / 2))

    def coherence(self, values: Iterable[float]) -> float:
        values = [_safe_float(v) for v in values]
        if not values:
            return 0.0
        if len(values) == 1:
            return 1.0
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        return 1 / (1 + math.sqrt(variance))

    def entropy(self, values: Iterable[float]) -> float:
        vals = [abs(_safe_float(v)) for v in values]
        total = sum(vals)
        if total <= 0:
            return 0.0
        probs = [v / total for v in vals if v > 0]
        return -sum(p * math.log(p, 2) for p in probs)

    def entropy_profile(self, text: str) -> float:
        if not text:
            return 0.0
        return self.entropy(Counter(text).values())

    @h360_sync(tags=["core", "snapshot"])
    def snapshot(self, label: str = "harmony360_snapshot") -> Dict[str, Any]:
        return {
            "label": label,
            "created_at": datetime.now().isoformat(),
            "constants": {
                "PHI": self.phi,
                "PI": self.pi,
                "ALPHA": self.alpha,
                "PLANCK_LENGTH": self.lp,
                "ETA": self.eta,
                "CHI": self.chi,
            },
        }

    def export_har360(self, payload: Any, name: str = "harmony360_record", tags: Optional[List[str]] = None):
        return self.memory.write(payload, name=name, source="Harmony360", kind="runtime_export", tags=tags or ["harmony360"])


class BaseDivision(Harmony360):
    division_name = "BaseDivision"

    def __init__(self, name: Optional[str] = None, memory_dir: str | Path = "./har360_output"):
        super().__init__(memory_dir=memory_dir)
        self.name = name or self.division_name

    def describe(self):
        return {"division": self.name, "base": "Harmony360", "eta": self.eta, "chi": self.chi}


class TLN369(Harmony360):
    def digital_root(self, n: int) -> int:
        n = abs(int(n))
        if n == 0:
            return 0
        return 1 + ((n - 1) % 9)

    def tln_phase(self, step: int):
        root = self.digital_root(step)
        triad = "3-6-9" if root in {3, 6, 9} else "1-2-4-5-7-8"
        angle = (root / 9) * TAU
        return {
            "step": int(step),
            "digital_root": root,
            "triad": triad,
            "angle": angle,
            "sin": math.sin(angle),
            "cos": math.cos(angle),
            "phi_scaled": self.phi_scale(root or 9),
        }

    def lattice(self, steps: int = 9):
        return [self.tln_phase(i) for i in range(1, int(steps) + 1)]


class QuantumConsciousness(Harmony360):
    def cri(self, vector: Iterable[float]) -> float:
        values = [_safe_float(v) for v in vector]
        if not values:
            return 0.0
        r = self.resonance(values)
        c = self.coherence(values)
        e = self.entropy([abs(v) for v in values])
        return max(0.0, min(1.0, r * 0.4 + c * 0.4 + (1 / (1 + e)) * 0.2))

    def entanglement_signature(self, a: Iterable[float], b: Iterable[float]):
        va = _normalize_vector(a)
        vb = _normalize_vector(b)
        n = min(len(va), len(vb))
        dot = sum(va[i] * vb[i] for i in range(n)) if n else 0.0
        return {
            "dot": dot,
            "alignment": (dot + 1) / 2,
            "cri_a": self.cri(va),
            "cri_b": self.cri(vb),
            "resonance_bridge": self.resonance([dot, self.cri(va), self.cri(vb)]),
        }


class QRC360(Harmony360):
    def fingerprint(self, payload: Any, salt: str = "") -> str:
        material = json.dumps(payload, sort_keys=True, default=_json_default)
        return hashlib.sha256((salt + material + str(self.eta)).encode("utf-8")).hexdigest()

    def verify(self, payload: Any, fingerprint: str, salt: str = "") -> bool:
        return self.fingerprint(payload, salt=salt) == fingerprint

    def qrc_packet(self, payload: Any, salt: str = ""):
        return {
            "payload": payload,
            "fingerprint": self.fingerprint(payload, salt=salt),
            "salted": bool(salt),
            "created_at": datetime.now().isoformat(),
            "qrc": "QRC360",
        }


class Guardian(Harmony360):
    def review(self, payload: Dict[str, Any]):
        issues = []
        text = json.dumps(payload, default=_json_default).lower()
        if not payload:
            issues.append("empty_payload")
        if "error" in text or "traceback" in text:
            issues.append("error_signal_detected")
        if len(text) > 2_000_000:
            issues.append("payload_too_large")
        return {
            "status": "APPROVED" if not issues else "REVIEW_REQUIRED",
            "issues": issues,
            "reviewed_at": datetime.now().isoformat(),
            "guardian": "Guardian",
            "resonance": self.resonance([len(text), len(issues), self.eta]),
        }


class Sekhmet(Guardian):
    def veto(self, payload: Dict[str, Any], threshold: int = 3):
        review = self.review(payload)
        severity = len(review.get("issues", []))
        review["sekhmet"] = "ACTIVE" if severity >= threshold else "STANDBY"
        if severity >= threshold:
            review["status"] = "VETO"
        return review


class DocumentResonator:
    def __init__(self, harmony: Optional[Harmony360] = None):
        self.harmony = harmony or Harmony360()

    def resonate(self, text: str, source: str = "document"):
        text = text or ""
        words = text.split()
        unique_words = len(set(w.lower().strip(".,;:!?()[]{}") for w in words if w.strip()))
        harmonic_sum = sum((ord(ch) % 97) for ch in text[:50000])
        resonance = (math.sin(harmonic_sum * CHI) + 1) / 2 if text else 0.0
        return {
            "source": source,
            "characters": len(text),
            "words": len(words),
            "unique_words": unique_words,
            "phi_density": (unique_words / max(1, len(words))) * PHI if words else 0.0,
            "resonance": resonance,
            "entropy": self.harmony.entropy_profile(text),
            "signature": _sha256_text(text)[:32],
        }


class RecoveredModule(BaseDivision):
    recovered = True

    def __init__(self, module_name: str, memory_dir: str | Path = "./har360_output"):
        super().__init__(name=module_name, memory_dir=memory_dir)

    def signature(self):
        return {
            "module": self.name,
            "recovered": True,
            "base": "Harmony360",
            "resonance": self.resonance([len(self.name), self.eta, self.chi]),
        }


RECOVERED_SYMBOLIC_MODULES = [
    "AtlantisInterface",
    "AuditoryGeometry",
    "BaseDivision",
    "BioResonanceCodex",
    "BiofieldEngine",
    "BiofieldResonator",
    "BlackHoleInformation",
    "ChakraStargateMap",
    "CircleOfFifthsResonator",
    "CodexEditor",
    "CodexForensics",
    "CodexModule",
    "DNAGenetics",
    "DNAMapConfig",
    "FractalEmotionMapper",
    "FractalMusic",
    "FractalPrimes",
    "FractalSeerDivision",
    "GeometryHarmonicsEngine",
    "NumerologyEngine",
    "SacredGeometryEngine",
    "SoulMatchEngine",
]


def build_symbolic_registry(memory_dir: str | Path = "./har360_output"):
    return {name: RecoveredModule(name, memory_dir=memory_dir) for name in RECOVERED_SYMBOLIC_MODULES}


class Elena(Harmony360):
    def __init__(self, memory_dir: str | Path = "./har360_output"):
        super().__init__(memory_dir=memory_dir)
        self.guardian = Guardian(memory_dir=memory_dir)
        self.sekhmet = Sekhmet(memory_dir=memory_dir)
        self.tln = TLN369(memory_dir=memory_dir)
        self.quantum = QuantumConsciousness(memory_dir=memory_dir)
        self.qrc = QRC360(memory_dir=memory_dir)
        self.registry = build_symbolic_registry(memory_dir=memory_dir)

    @h360_sync(tags=["elena", "orchestration"])
    def orchestrate(self, intent: str, payload: Optional[Dict[str, Any]] = None):
        payload = payload or {}
        review = self.guardian.review({"intent": intent, "payload": payload})
        vector = [len(intent), len(json.dumps(payload, default=_json_default)), self.eta, self.chi]
        result = {
            "intent": intent,
            "payload": payload,
            "guardian_review": review,
            "cri": self.quantum.cri(vector),
            "tln_phase": self.tln.tln_phase(len(intent) or 1),
            "qrc": self.qrc.fingerprint({"intent": intent, "payload": payload}),
            "modules_available": sorted(self.registry.keys()),
            "created_at": datetime.now().isoformat(),
        }
        if review["status"] != "APPROVED":
            result["sekhmet_review"] = self.sekhmet.veto(result)
        return result


class Harmony360Runtime(Harmony360):
    def __init__(self, memory_dir: str | Path = "./har360_output"):
        super().__init__(memory_dir=memory_dir)
        self.tln369 = TLN369(memory_dir=memory_dir)
        self.quantum = QuantumConsciousness(memory_dir=memory_dir)
        self.qrc360 = QRC360(memory_dir=memory_dir)
        self.guardian = Guardian(memory_dir=memory_dir)
        self.sekhmet = Sekhmet(memory_dir=memory_dir)
        self.document_resonator = DocumentResonator(self)
        self.elena = Elena(memory_dir=memory_dir)
        self.symbolic_registry = build_symbolic_registry(memory_dir=memory_dir)

    def status(self):
        return {
            "runtime": "Harmony360 Original Core Reconstruction",
            "created_at": datetime.now().isoformat(),
            "constants": self.snapshot("runtime_status")["constants"],
            "modules": {
                "TLN369": True,
                "QuantumConsciousness": True,
                "QRC360": True,
                "Guardian": True,
                "Sekhmet": True,
                "DocumentResonator": True,
                "HAR360Converter": True,
                "Elena": True,
                "RecoveredSymbolicModules": len(self.symbolic_registry),
            },
        }


def create_runtime(memory_dir: str | Path = "./har360_output"):
    return Harmony360Runtime(memory_dir=memory_dir)


__all__ = [
    "PHI", "PI", "TAU", "ALPHA", "FINE_STRUCTURE_CONSTANT", "PLANCK_LENGTH",
    "HARMONY_ETA", "CHI", "HAR360Record", "HAR360Converter",
    "DocumentResonator", "h360_sync", "Harmony360", "BaseDivision",
    "TLN369", "QuantumConsciousness", "QRC360", "Guardian", "Sekhmet",
    "RecoveredModule", "RECOVERED_SYMBOLIC_MODULES", "build_symbolic_registry",
    "Elena", "Harmony360Runtime", "create_runtime",
]
