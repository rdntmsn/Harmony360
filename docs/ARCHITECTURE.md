# Python program increment 1

The existing `reconciliation/core_runtime_v1` package provides `Harmony360`,
mathematical operations, native serialization, snapshots and its historical
ledger implementation. The new `src/harmony360_orchestration` package imports
that public API. No numerical formula or retained core file is changed.

| Component | Implemented responsibility | Boundary |
| --- | --- | --- |
| `sources.py` | Read published releases and advisories from the official CrewAI GitHub API; reject incomplete coverage | No upstream content execution; no dependency installation |
| `changes.py` | Classify change records and separate official facts from engineering inference | Heuristic release triage; local exposure remains unknown |
| `watch.py` | SQLite baseline, content fingerprints and pending-alert outbox | At-least-once delivery; a crash between output and acknowledgement can repeat an alert |
| `doctor.py` | Inventory installed distributions against one advisory's patch floors | Not a full vulnerability scan or compatibility certification |
| `core_bridge.py` | Call the original core; seal/reconstruct via its existing codec | Strict adapter JSON and expected-file-hash checks; no codec replacement |
| `orchestration.py` | Deny crew entry without trusted request-bound approval; hash journal events and outcomes | Host owns authenticated approvals and the trusted plan; per-tool enforcement is a future integration |
| `cli.py` | Version inventory, local core demonstration and change checking | No live-execution approval command |

The source core identity is recorded in `CORE_PROVENANCE.json`. Its snapshot and
ledger formats are distinct from the later Unified Core v0.2 integration wire
contract. This build does not rename them into one canonical schema. The Unified
Core and Knowledge Factory packages were reviewed to preserve the same layering:
numeric core → evidence/governance → bounded orchestration. Their migration into
installable modules remains a separate, testable step.

Every accepted run receipt stays `UNDER_REVIEW` and grants no canonical authority.
Elena's identity and higher governance policy are not redefined here. Numerical
diagnostics never substitute for a human decision or task-quality evaluation.

## Next increments toward a release

1. Qualify the pinned CrewAI profile with a deterministic local model/provider,
   constructor/kickoff/event contract checks, and no paid model calls.
2. Connect the existing Guardian policy and authenticated approval service to
   individual tools; test replay, expiry, changed plans and denied effects.
3. Move the retained Knowledge Factory worker/curator experiment into a Python
   module with its exact-field controls and source-manifest verification intact.
   Keep the notebook as a small optional interface to the same package.
4. Reconcile the Unified Core and existing GitHub runtime contracts explicitly;
   add schema migration and reconstruction fixtures instead of changing formats
   implicitly.
5. Produce a locked integration profile, cross-version CI evidence and a reviewed
   release candidate. Publishing and enabling production execution are later
   release decisions.

