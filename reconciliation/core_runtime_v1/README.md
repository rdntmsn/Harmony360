# Harmony360 Canonical Runtime Spine v1

This package reconciles the recovered v10-v13 Harmony360 core into a stable
Python inheritance surface for current Harmony360 capability development.

## Design rule

**When a name claims a capability, correct the implementation until the capability is real.**

## What belongs here

- foundational constants;
- historical core mathematical transforms;
- Harmony360-defined mathematical quantities (`eta`, `chi`, `EH360`);
- deterministic `.har360` serialization and integrity checks;
- evidence record primitives;
- a stable `Harmony360` base class for capability modules.

## What does NOT belong directly in the root class

Cryptography, model training, databases, black-hole research, EEG analysis,
Guardian orchestration, and other specialized capabilities live in modules
that inherit from or compose the canonical core.

## Important reconciliation

Historical Harmony360 used `1/137` as `ALPHA`. This package preserves that
as `ALPHA_LEGACY`, while `ALPHA` uses the 2022 CODATA recommended
fine-structure constant value.

Implementing a Harmony360 formula records a mathematical definition. It is
not, by itself, evidence that the formula is a law of nature.
