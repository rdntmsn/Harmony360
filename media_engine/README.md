# Harmony360 Media Engine v0.1

A Harmony360-native Python agent pipeline for creating governed YouTube media.

This repository module was built from the pre-build architecture mandate that **all Harmony360-owned executable media classes inherit from and use the retained Harmony360 core class**.

## What v0.1 does

- preserves the recovered Harmony360 core verbatim;
- creates governed source, claim, script, storyboard, caption, render, review, and publication contracts;
- enforces a claim gate;
- requires human approval before upload preparation;
- prepares YouTube uploads as **private** only;
- writes episode JSON plus core-native `.har360` receipts;
- includes a Colab notebook and tests proving the inheritance mandate.

## What v0.1 deliberately does not do

- no blind public autopublishing;
- no generated image is treated as evidence;
- no external image/TTS/LLM provider is silently selected;
- no Harmony360 claim is promoted because a video was generated or published.

## Quick start

```bash
pip install -e .[dev]
pytest -q
```

## Core provenance

Runtime base:

- Drive source: `Harmony360_Original_Core_Recovery/20260624_005825/harmony360_original_core_reconstruction/harmony360_original_core.py`
- SHA-256: `b14681dcfc821c87d2a887e012061e2b266fbc0f778c54d977146c492e30159c`

See `source_provenance.json` and `docs/ARCHITECTURE.md`.
