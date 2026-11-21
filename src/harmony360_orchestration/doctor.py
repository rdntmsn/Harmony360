"""Dependency inventory, not a general security certification."""
from __future__ import annotations

import sys
from importlib import metadata

from packaging.specifiers import SpecifierSet
from packaging.version import InvalidVersion, Version

SECURITY_FLOORS = {"crewai": "1.15.31", "crewai-tools": "1.15.31", "crewai-files": "1.15.44"}
ADVISORY = "https://github.com/crewAIInc/crewAI/security/advisories/GHSA-wp6h-6xxh-g8fp"
CANDIDATE = "1.15.44"
CANDIDATE_CONSTRAINTS = {"python": ">=3.10,<3.14", "pydantic": ">=2.11.9,<2.13"}


def inspect_versions(versions: dict[str, str | None] | None = None) -> dict:
    if versions is None:
        versions = {}
        for name in (*SECURITY_FLOORS, "crewai-core", "pydantic", "harmony360-runtime-spine"):
            try:
                versions[name] = metadata.version(name)
            except metadata.PackageNotFoundError:
                versions[name] = None
    findings = []
    for name, floor in SECURITY_FLOORS.items():
        installed = versions.get(name)
        if installed is None:
            status = "NOT_INSTALLED"
        else:
            try:
                v = Version(installed)
                status = "BELOW_PATCH_FLOOR" if v < Version(floor) or v.is_prerelease or v.is_devrelease else "PATCH_FLOOR_MET"
            except InvalidVersion:
                status = "UNKNOWN_VERSION"
        findings.append({"package": name, "installed": installed, "patched_from": floor, "status": status})
    compatibility = []
    for dependency, constraint in CANDIDATE_CONSTRAINTS.items():
        installed = sys.version.split()[0] if dependency == "python" else versions.get(dependency)
        try:
            status = "NOT_INSTALLED" if installed is None else (
                "CONSTRAINT_MET" if Version(installed) in SpecifierSet(constraint) else "INCOMPATIBLE_WITH_CANDIDATE")
        except InvalidVersion:
            status = "UNKNOWN_VERSION"
        compatibility.append({"dependency": dependency, "installed": installed,
                              "candidate_constraint": constraint, "status": status})
    return {"schema": "harmony360.environment-inventory.v0.1", "python": sys.version.split()[0],
            "installed_versions": versions, "advisory": ADVISORY, "findings": findings,
            "crewai_candidate": CANDIDATE, "live_crewai_compatibility": "NOT_VALIDATED",
            "candidate_constraint_checks": compatibility,
            "meaning": "Patch floors cover this one advisory. They do not establish overall safety or local exploitability."}

