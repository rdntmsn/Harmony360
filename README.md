# Harmony360

Harmony360 is moving from notebook experiments toward installable Python programs.
The first package, `harmony360-orchestration` **0.1.0a1**, provides an official-source
CrewAI change monitor and a run-level approval boundary around an optional CrewAI
adapter. The existing Harmony360 core remains its own package and implementation.

## Run locally

Use Python 3.11–3.13. From this repository:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e reconciliation/core_runtime_v1 -e .
h360 doctor
h360 core-demo --values 1 2 3 --output runtime-output/core-demo.har360
```

On Windows, activate with `.venv\Scripts\activate`. `core-demo` invokes the actual
`Harmony360` numerical methods, saves through the existing `.har360` codec and
verifies reconstruction. Its numerical diagnostics do not determine truth,
scientific validity, task accuracy or authorization.

## CrewAI change monitoring

Read [the initial upstream review](docs/CURRENT_UPSTREAM_REVIEW.md), then establish
the set of already reviewed releases and advisories:

```bash
h360 crewai-watch --baseline
h360 crewai-watch --output .h360/alerts.json
```

Subsequent runs emit JSON only for new meaningful stable releases or material
advisory changes. An unchanged successful run produces no output and removes a
stale output file. A failed source check exits with status 2, writes an error to
stderr and retains the previous baseline and pending alerts. `--baseline` is a
one-time acknowledgement of existing sources, not a security scan or an upgrade.
Review active advisories before using it. The first baseline deliberately emits
no historical alerts.

Keep `.h360/crewai-watch.sqlite3` between runs. A scheduler can invoke the second
command daily on a persistent host. This repository's CI runs tests and builds;
it does not schedule the watcher or deliver notifications. The separate ChatGPT
watch established with this build is configured to check daily and alert only
when a meaningful change is found.

Sources are the official CrewAI repository's published releases and repository
security advisories. The current monorepo includes `crewai`, `crewai-tools` and
`crewai-files`; this first CLI does not crawl unrelated advisory databases or
legacy repositories. API pagination is bounded at 2,000 records per feed and
fails explicitly on overflow. Public API rate limits apply; an optional
`GITHUB_TOKEN` can be supplied in the environment. It is never included in output.
Release triage is deterministic keyword filtering, so human review remains
necessary and there can be false positives or missed implicit changes.

Each alert separates official upstream statements, unverified local exposure,
engineering inference and recommended validation. The watcher neither installs
dependencies nor applies migrations. Publication of a release or advisory alone
does not prove that a particular Harmony360 deployment is affected.

## Governed orchestration

The Python SDK wraps a **trusted, host-constructed** crew with `CrewAIAdapter`.
`GovernedOrchestrator` denies execution by default. The host must supply an
`ApprovalVerifier` that authenticates the reviewer, checks expiry and scope, and
atomically consumes a single-use approval bound to the action, exact inputs and
reviewed execution manifest. The reviewed plan must describe the actual models
and tools; the host must prevent the crew configuration changing after review.
`prepare_request(adapter, inputs)` returns the exact request to review; the host
binds its approval to `digest(request)` from the package's `jsonutil` module.
There is no CLI flag or serialized reviewer label that grants this authority.

The boundary journals approvals, denials, outcomes and content hashes in SQLite.
Input text, output text, approval tokens and exception messages are excluded
from the journal. Hashes can still reveal low-entropy values, and this local
journal is not signed, remotely anchored or protected against a writer who can
rewrite the entire database. A crash after external execution may leave an
approved run without a terminal event; it must be investigated, never retried
automatically. Approval consumption and external execution are not one atomic
transaction.

This increment controls entry into a crew run. Individual tool calls, production
authentication, network sandboxing and canonical promotion require further host
integration. The historical governance implementations and the Unified Core /
Knowledge Factory experiments remain separate; their controls are not silently
replaced by this adapter.

## Validate and build

```bash
python -m pip install pytest build
python -m unittest discover -s tests -v
python -m pytest reconciliation/core_runtime_v1/tests -q
python -m build
```

CI targets Python 3.11, 3.12 and 3.13. Local validation evidence and its limits are
recorded in [VALIDATION.md](docs/VALIDATION.md). The CrewAI 1.15.44 pins in
[the candidate requirements](requirements/crewai-candidate.txt) are a proposed
integration profile, not a resolved dependency lock or a verified live run.

See [architecture and the next increments](docs/ARCHITECTURE.md).

