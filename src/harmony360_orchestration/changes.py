"""Conservative triage rules. Potential local effects are labelled as inference."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .jsonutil import digest
from .sources import Snapshot, SourceUnavailable

RULES = {
    "security": r"\b(security|vulnerabil\w*|CVE-\S+|GHSA-\S+|SSRF|deserializ\w*|containment|path traversal)\b",
    "breaking_api": r"\b(breaking|backward.incompatible|deprecat\w*|remov\w* (?:API|support|parameter)|migration)\b",
    "compatibility": r"\b(Python|Pydantic|dependenc\w*|compatib\w*|pin|Chroma\w*|Qdrant|provider|schema)\b",
    "governance_logging": r"\b(guardrail\w*|permission\w*|authoriz\w*|human (?:review|feedback)|approval\w*|audit\w*|trac(?:e|es|ing)|logging|ledger\w*|checkpoint\w*|persist\w*|lineage|provenance)\b",
}

STEPS = {
    "security": ["Inventory installed affected packages and compare the advisory ranges with the dependency lock.",
                 "Test the patched versions in isolation; verify denied deserialization, path escapes and SQL writes where used."],
    "breaking_api": ["Compare imports, constructor arguments, kickoff signatures and event payloads with the official migration notes.",
                     "Run the adapter contract tests before updating the pinned version."],
    "compatibility": ["Check Python and Pydantic constraints, resolve a candidate dependency lock, then run python -m pip check.",
                      "Back up storage and test retrieval plus snapshot reconstruction, including explicit Chroma/Qdrant configuration where relevant."],
    "governance_logging": ["Verify denied actions never execute and approvals remain bound to the reviewed request.",
                           "Check run IDs, error events, trace redaction, .har360 round trips and evidence/decision ledger integrity."],
}


@dataclass(frozen=True)
class Change:
    key: str
    fingerprint: str
    kind: str
    version: str
    source_url: str
    published_at: str
    updated_at: str
    categories: tuple[str, ...]
    facts: tuple[str, ...]
    affected_packages: tuple[dict[str, Any], ...] = ()
    prerelease: bool = False


def _official_url(value: Any, prefix: str) -> str:
    if not isinstance(value, str) or not value.startswith(prefix):
        raise SourceUnavailable("Unexpected official record URL")
    return value


def _release_bullets(body: str) -> list[str]:
    bullets, section = [], ""
    has_bullets = False
    for line in body.splitlines():
        if line.startswith("#"):
            section = line.lstrip("# ").lower()
        is_bullet = bool(re.match(r"^\s*[-*]\s+", line))
        has_bullets = has_bullets or is_bullet
        if any(word in section for word in ("documentation", "contributors", "new contributors")):
            continue
        if is_bullet:
            bullets.append(re.sub(r"^\s*[-*]\s+", "", line).strip())
    # Older releases sometimes use a prose announcement instead of bullets.
    if has_bullets:
        return bullets
    return [body.strip()] if body.strip() and not any(x in section for x in ("documentation", "contributors")) else []


def normalize(snapshot: Snapshot) -> list[Change]:
    changes: list[Change] = []
    for row in snapshot.releases:
        if row.get("draft"):
            continue
        try:
            key = "release:" + str(row["id"])
            version = str(row["tag_name"])
            url = _official_url(row["html_url"], "https://github.com/crewAIInc/crewAI/releases/tag/")
            body = row.get("body") or ""
            if not isinstance(body, str):
                raise ValueError("Invalid release body")
            bullets = _release_bullets(body)
            selected = tuple(b for b in bullets if any(re.search(p, b, re.I) for p in RULES.values()))
            categories = tuple(k for k, p in RULES.items() if any(re.search(p, b, re.I) for b in selected))
            bound = {k: row.get(k) for k in ("id", "tag_name", "name", "body", "draft", "prerelease")}
            changes.append(Change(key, digest(bound), "release", version, url,
                                  row.get("published_at") or "unknown", row.get("updated_at") or "unknown",
                                  categories, selected, prerelease=bool(row.get("prerelease"))))
        except (KeyError, TypeError, ValueError) as exc:
            raise SourceUnavailable("Malformed official release record") from exc
    for row in snapshot.advisories:
        try:
            ghsa = row["ghsa_id"]
            url = _official_url(row["html_url"], "https://github.com/crewAIInc/crewAI/security/advisories/")
            packages = tuple({"package": v["package"]["name"],
                              "affected": v.get("vulnerable_version_range"),
                              "patched": v.get("patched_versions")} for v in row.get("vulnerabilities", []))
            bound = {k: row.get(k) for k in ("ghsa_id", "summary", "description", "severity", "vulnerabilities", "withdrawn_at", "cve_id")}
            facts = (str(row.get("summary") or ghsa), "Official severity: " + str(row.get("severity", "unknown")))
            if row.get("withdrawn_at"):
                facts += ("Advisory withdrawn: " + row["withdrawn_at"],)
            changes.append(Change("advisory:" + ghsa, digest(bound), "advisory", ghsa, url,
                                  row.get("published_at") or "unknown", row.get("updated_at") or "unknown",
                                  ("security",), facts, packages))
        except (KeyError, TypeError, ValueError) as exc:
            raise SourceUnavailable("Malformed official advisory record") from exc
    keys = [c.key for c in changes]
    if len(keys) != len(set(keys)):
        raise SourceUnavailable("Duplicate official records; snapshot rejected")
    return changes


def alert(change: Change) -> dict[str, Any]:
    steps = list(dict.fromkeys(step for category in change.categories for step in STEPS[category]))
    return {
        "schema": "harmony360.crewai-alert.v0.1",
        "version": change.version,
        "source": change.source_url,
        "published_at": change.published_at,
        "updated_at": change.updated_at,
        "categories": list(change.categories),
        "confirmed_upstream": {"basis": "Official published record; Harmony360 reproduction is not established",
                               "statements": list(change.facts),
                               "affected_packages": list(change.affected_packages)},
        "potential_harmony360_impact": {"classification": "ENGINEERING_INFERENCE",
            "exposure": "UNVERIFIED: installed versions, enabled tools and deployment configuration are unknown",
            "description": "Review the optional CrewAI adapter, storage and run evidence for the listed change categories. The Harmony360 core remains a separate dependency."},
        "recommended_validation": steps,
        "speculation": [],
        "canonical_authority_granted": False,
    }

