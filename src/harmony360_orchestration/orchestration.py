"""A run-level approval boundary, with a small transactional evidence journal.

The host supplies authenticated, single-use approval consumption. No JSON field,
reviewer label or LLM response can grant authority through this module.
"""
from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path
from typing import Protocol

from .core_bridge import CoreBridge
from .doctor import inspect_versions
from .jsonutil import canonical, digest, strict_loads, utcnow


class ActionDenied(PermissionError):
    pass


class ApprovalVerifier(Protocol):
    def consume(self, *, approval_id: str, action: str, request_sha256: str) -> bool:
        """Authenticate, bind, expire and atomically consume a one-time host approval."""
        ...


class RejectAllApprovals:
    def consume(self, **kwargs) -> bool:
        return False


class Adapter(Protocol):
    def manifest(self) -> dict:
        """Trusted host's execution plan, including enabled models/tools and versions."""
        ...

    def kickoff(self, inputs: dict) -> str:
        ...


def prepare_request(adapter: Adapter, inputs: dict) -> dict:
    """Return the exact reviewable request whose digest the host must approve."""
    return strict_loads(canonical({"action": "crewai.kickoff", "inputs": inputs,
                                  "adapter": adapter.manifest()}))


class CrewAIAdapter:
    """Wrap a trusted, host-constructed crew. Never deserialize a crew from data."""
    def __init__(self, crew, *, reviewed_plan: dict):
        inventory = inspect_versions()
        if not inventory["installed_versions"].get("crewai"):
            raise RuntimeError("CrewAI is not installed")
        if any(x["status"] in {"BELOW_PATCH_FLOOR", "UNKNOWN_VERSION"} for x in inventory["findings"]):
            raise ActionDenied("An installed CrewAI component does not meet the advisory patch floor")
        if inventory["installed_versions"].get("crewai") == inventory["crewai_candidate"] and any(
                x["status"] != "CONSTRAINT_MET" for x in inventory["candidate_constraint_checks"]):
            raise ActionDenied("The candidate CrewAI Python/Pydantic constraints are not met")
        self.crew = crew
        self._manifest = strict_loads(canonical({"adapter": "crewai", "reviewed_plan": reviewed_plan,
                                               "installed_versions": inventory["installed_versions"]}))

    def manifest(self) -> dict:
        return strict_loads(canonical(self._manifest))

    def kickoff(self, inputs: dict) -> str:
        result = self.crew.kickoff(inputs=inputs)
        raw = getattr(result, "raw", result)
        if not isinstance(raw, str):
            raise TypeError("Expected a text CrewAI result")
        return raw


class EvidenceJournal:
    def __init__(self, path: Path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, timeout=30)
        self.db.execute("CREATE TABLE IF NOT EXISTS events (sequence INTEGER PRIMARY KEY, body TEXT NOT NULL, hash TEXT NOT NULL)")
        self.db.commit()

    def close(self):
        self.db.close()

    def _verify(self) -> dict:
        previous = None
        count = 0
        for sequence, body, saved in self.db.execute("SELECT sequence,body,hash FROM events ORDER BY sequence"):
            value = strict_loads(body)
            if sequence != count + 1 or value["previous_sha256"] != previous or digest(value) != saved:
                raise ValueError("Evidence journal integrity failure")
            previous, count = saved, count + 1
        return {"valid": True, "events": count, "head_sha256": previous}

    def verify(self) -> dict:
        return self._verify()

    def append(self, event: dict) -> str:
        try:
            self.db.execute("BEGIN IMMEDIATE")
            state = self._verify()
            body = {"event": event, "at": utcnow(), "previous_sha256": state["head_sha256"]}
            value = digest(body)
            self.db.execute("INSERT INTO events VALUES(?,?,?)", (state["events"] + 1, canonical(body), value))
            self.db.commit()
            return value
        except BaseException:
            self.db.rollback()
            raise


class GovernedOrchestrator:
    def __init__(self, core: CoreBridge, journal: EvidenceJournal,
                 approvals: ApprovalVerifier | None = None):
        self.core, self.journal = core, journal
        self.approvals = approvals if approvals is not None else RejectAllApprovals()

    def execute(self, adapter: Adapter, inputs: dict, *, approval_id: str = "") -> dict:
        request = prepare_request(adapter, inputs)
        frozen_inputs = request["inputs"]
        input_hash = digest(frozen_inputs)
        run_id = "h360-" + uuid.uuid4().hex
        action = request["action"]
        execution_manifest = request["adapter"]
        request_hash = digest(request)
        self.journal.verify()  # Corruption blocks both authorization and execution.
        if self.approvals.consume(approval_id=approval_id, action=action, request_sha256=request_hash) is not True:
            self.journal.append({"run_id": run_id, "decision": "DENIED", "action": action,
                                 "input_sha256": input_hash, "request_sha256": request_hash})
            raise ActionDenied("A trusted host approval is required for this exact request")
        decision_hash = self.journal.append({"run_id": run_id, "decision": "APPROVED", "action": action,
                                             "input_sha256": input_hash, "request_sha256": request_hash,
                                             "approval_id_sha256": digest(approval_id)})
        try:
            output = adapter.kickoff(frozen_inputs)
            if not isinstance(output, str):
                raise TypeError("Adapter must return text")
        except Exception as exc:
            self.journal.append({"run_id": run_id, "outcome": "FAILED", "error_type": type(exc).__name__})
            raise
        receipt = {"schema": "harmony360.orchestration-receipt.v0.1", "run_id": run_id,
                   "state": "UNDER_REVIEW", "action": action, "input_sha256": input_hash,
                   "request_sha256": request_hash, "execution_manifest_sha256": digest(execution_manifest),
                   "output_sha256": digest(output), "decision_sha256": decision_hash,
                   "core_manifest": self.core.core.core_manifest(),
                   "canonical_authority_granted": False,
                   "scope": "Run-level approval only; individual tool calls require the host's separate controls."}
        self.journal.append({"run_id": run_id, "outcome": "COMPLETED", "receipt_sha256": digest(receipt)})
        return receipt

