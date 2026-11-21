# Changelog

## 0.1.0a1 — 2026-11-21

- Add an installable Python CLI for official CrewAI release/advisory monitoring.
- Persist reviewed baselines, changed-content fingerprints and pending alerts.
- Keep failed checks distinct from successful unchanged checks.
- Add a bridge to the existing Harmony360 numerical core and `.har360` codec.
- Add a default-deny crew entry boundary with host-supplied approval consumption,
  request/plan binding and a transactional hash journal.
- Add regression tests, candidate CrewAI requirements and a Python CI/build workflow.

This is an alpha development increment. Live CrewAI/provider execution and a
production authentication service have not been qualified.

