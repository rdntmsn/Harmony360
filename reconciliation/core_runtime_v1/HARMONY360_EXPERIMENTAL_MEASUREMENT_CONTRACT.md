# Harmony360 Experimental Measurement Contract v1

## Status
Governed engineering/research contract for all future Harmony360 experiments.

## Standing rule
Every governed Harmony360 experiment MUST instantiate the canonical Harmony360 core measurement layer and capture applicable Harmony360-native mathematical observables for every experimental arm, including neutral and conventional controls.

Inheritance from `Harmony360` alone does not constitute use of the Harmony360 core.

Harmony360 measurement and Harmony360 intervention are separate concepts:

- **Measurement:** every arm is observed through the same canonical Harmony360 mathematics.
- **Intervention:** only the designated treatment arm(s) receive a Harmony360-specific modification.

This preserves falsifiability while preventing decorative or inheritance-only use of the core.

## Required measurement base
At minimum, where mathematically applicable, record:

- φ
- π
- α
- η = φπ + α
- χ = ln(φ) / π
- `phi_pi_modulation(x) = sin(2πx/φ)`
- `R_369(x)`
- resonance scaling
- fractal harmonic projection
- coherence score
- harmonic entropy

Additional modules such as RECL may be required when the experiment invokes them.

## Required parallel domain metrics
Harmony360-native observables do not replace accepted domain metrics. Record both.

Examples:

- model training: validation loss, accuracy, calibration, convergence, stability
- turbulence: Reynolds number, kinetic energy, enstrophy, dissipation, vorticity
- markets: out-of-sample error, drawdown, turnover, risk-adjusted return
- geometry: reconstruction error, symmetry metrics, ratio residuals

## Required arm structure
Every arm must contain:

1. `arm_name`
2. `domain_metrics`
3. `harmony360_measurement`
4. `intervention_flags`

The control arm MUST have Harmony360 measurement enabled while treatment flags remain off.

Example conceptual matrix:

| Arm | Harmony360 measurement | Harmony360 intervention |
|---|---:|---:|
| Conventional control | ON | OFF |
| Harmony360 treatment | ON | ON |

## Claim boundary
Harmony360 observables are mathematical measurements unless a physical or empirical mapping is explicitly defined and independently validated.

A change in Harmony360 coherence, φ/π modulation, R369, harmonic entropy, or fractal projection does not by itself prove improved task performance, physical resonance, or causal significance.

## Experimental obligations
Every governed experiment must:

1. preserve a neutral/domain-standard outcome metric;
2. measure every arm through the canonical Harmony360 core;
3. independently switch Harmony360 interventions ON/OFF;
4. state the null hypothesis;
5. retain matched controls wherever possible;
6. record seeds, data split, architecture, optimizer/budget, and environment;
7. persist snapshots/ledger/evidence;
8. limit conclusions to the tested conditions;
9. fail validation if Harmony360 is inherited but not actually measured.

## Current implementation
Runtime API:

- `Harmony360MeasurementContract`
- `MeasurementSemantics`

The measurement contract currently records:

- canonical core constants;
- domain summary statistics;
- φ/π modulation trajectory;
- R369 trajectory;
- resonance-scaling trajectory;
- fractal-harmonic projection;
- coherence score;
- harmonic entropy.

`PhiPiTuner` v1.1 has been upgraded so every candidate—including baseline controls—is measured through this contract while intervention flags remain explicit.

## Lineage
Canonical Core Runtime Spine -> Trainer v1 -> PhiPiTuner controlled ablation v1 -> Experimental Measurement Contract v1.

Historical results remain valid only to their original scope. New runs should use this contract unless an explicitly governed exception is recorded.

## Principle
**The control is measured through Harmony360 without being modified by Harmony360.**

That is the distinction that allows Harmony360 to be the project’s common mathematical measurement frame without making every comparison circular.
