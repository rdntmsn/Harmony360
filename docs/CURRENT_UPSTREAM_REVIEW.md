# Initial CrewAI review — November 21, 2026

The installed versions and enabled tools of the user's running Harmony360
deployment have not been established. The records below establish upstream
facts and a monitoring baseline, not a local vulnerability finding.

| Official record | Confirmed upstream fact | Potential effect and validation |
| --- | --- | --- |
| [GHSA-wp6h-6xxh-g8fp](https://github.com/crewAIInc/crewAI/security/advisories/GHSA-wp6h-6xxh-g8fp), published November 19 | High severity. `crewai` and `crewai-tools` versions through 1.15.30 are affected; 1.15.31 is patched. `crewai-files` versions through 1.15.43 are affected; 1.15.44 is patched. The advisory covers deserialization, read-only SQL and symlink containment. | Exposure is unverified. Inventory the three packages and enabled features. Qualify patched candidates against untrusted serialized tool data, denied writes and symlink escapes where those features are used. The advisory says ordinary absolute paths outside the working directory remain allowed: the file patch is not a complete filesystem sandbox. |
| [1.15.42](https://github.com/crewAIInc/crewAI/releases/tag/1.15.42), November 18 | Knowledge storage defaults change to local Qdrant; Chroma becomes optional. The release also adjusts Flow identity, timeouts and structured task-output persistence. | Engineering inference: implicit storage assumptions or existing vector indexes may need explicit configuration and migration. Back up indexes; compare retrieval results and persisted outputs on a copied dataset before an upgrade. |
| [1.15.44](https://github.com/crewAIInc/crewAI/releases/tag/1.15.44), November 19 | Latest stable release observed at setup. It adds artifact versioning/sharing and fixes guardrail output handling and file-path validation. | Engineering inference: map artifact identifiers to Harmony360 lineage and compare non-string guardrail results. Review sharing behavior before enabling it. Artifact versioning alone does not establish an immutable evidence ledger or canonical authority. |

The official [1.15.44 package metadata](https://github.com/crewAIInc/crewAI/blob/1.15.44/lib/crewai/pyproject.toml)
declares Python `>=3.10,<3.14` and Pydantic `>=2.11.9,<2.13`. This new adapter package
targets Python 3.11–3.13. Resolve the complete dependency graph in isolation,
inspect the resulting lock, run `python -m pip check`, and validate the adapter
contract before enabling model or tool execution. The proposed top-level pins
are not a complete lock.

No claim of exploitation in Harmony360, empirical reproduction of the upstream
bugs, or completed live CrewAI migration is made. No unconfirmed report is used
as a confirmed issue.

