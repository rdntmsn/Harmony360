# Validation — 0.1.0a1

Validation date: November 21, 2026. Local interpreter: Python 3.12.14.

| Check | Result | Scope |
| --- | --- | --- |
| Install adapter and retained core as editable Python packages | PASS | `harmony360-orchestration` 0.1.0a1 and `harmony360-runtime-spine` 1.1.0 |
| New regression suite | 26 PASS | Alert deduplication, material-content fingerprints, baseline rules, pending-alert recovery, source errors, strict JSON, approval/request/plan binding, replay denial, redacted journal events, corruption rejection and candidate constraints |
| Existing core regression suite | 16 PASS | Retained numerical, crypto-vault, serialization and snapshot/ledger tests |
| Real official-source fetch | PASS | 258 published release records and 1 published advisory, including pagination |
| Repeat real source check | PASS | Exit 0, no stdout and no alert output file |
| Installed `h360 core-demo` command | PASS | Existing numerical calls, native `.har360` serialization and checked reconstruction |
| Build source distribution and Python wheel | PASS | Alpha distributions built locally; no release publication |
| Verify original core bytes | PASS | Existing tracked files match the pinned repository source; no core edits |

The source metadata in the initial review was checked against official release
pages, the published advisory and the tagged upstream project configuration.
The tests for a CrewAI-shaped object use local doubles. A real CrewAI install,
real LLM calls, authenticated human approval service, per-tool policy enforcement
and a production deployment have not been validated. The candidate requirements
are not a resolved transitive lock. Only Python 3.12 was exercised locally;
the workflow defines additional Python 3.11 and 3.13 jobs.

The local validation environment reports Pydantic 2.13.4, outside the candidate
CrewAI 1.15.44 constraint. The adapter's inventory identifies that conflict and
the regression suite verifies that candidate execution would be blocked.
This is a development-environment observation, not evidence about the user's
deployed Harmony360 environment. Candidate qualification belongs in a separate
dependency environment.

Journal hashes detect inconsistent local edits, not an attacker capable of
rewriting all records and recomputing the chain. Alert output is acknowledged
after a successful write, with at-least-once behavior across a crash before the
acknowledgement. External execution has no automatic retry or exactly-once
claim. These limits remain part of the alpha contract.

