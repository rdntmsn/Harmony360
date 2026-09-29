# Harmony360 Core Reconciliation — Crypto Vault v1

This directory reconciles the historical `HarmonicCryptoVault` / QRC360 security intent with a legitimate authenticated-encryption implementation.

## Contract

- AES-256-GCM provides confidentiality and authentication.
- `.har360` metadata is authenticated as AAD.
- Raw keys are never written into artifacts.
- Harmony360 adds identity, lineage, lifecycle/policy hooks, evidence, and reconstruction metadata.
- Historical φ/π and QRC360 transforms are preserved as lineage/research concepts, **not** used as cryptographic security primitives.

## Files

- `harmonic_crypto_vault.py` — reusable implementation.
- `tests/test_harmonic_crypto_vault.py` — verification tests.
- `Harmony360_CryptoVault_Reconciliation_v1.ipynb` — Colab workflow.

## Core reconciliation rule

**When the name claims a capability, correct the implementation until the capability is real.**
