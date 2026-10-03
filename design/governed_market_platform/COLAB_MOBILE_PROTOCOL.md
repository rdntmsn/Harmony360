# Phone-First Colab Protocol

- One meaningful task per cell.
- Separate mount, targeted discovery, hashing, extraction, analysis, testing and export.
- Report stage, completed/total, elapsed time, shortened current path, warnings and next checkpoint at least every ten seconds.
- Provide quick, standard and full modes.
- Use explicit Drive roots; never recursively hash all Drive by default.
- Cache receipts and resume from checkpoints.
- Print a short diagnosis before raising.
- Default to paper-only execution.
- End with completed work, artifact links, test counts, hashes, classifications, unresolved decisions and the exact next cell.

Configuration must expose RUN_MODE, PAPER_ONLY, DRIVE_ROOTS, GITHUB_REPOSITORY, MAX_FILES, MAX_BYTES, RESUME and FULL_ESTATE_SCAN=false.
