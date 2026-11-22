# Harmony360 visual reading — Pattern Play v0.2

This product adapter uses the retained Harmony360 numerical core. It follows
the separation of core observables and named domain mappings described in the
existing Harmony360 Measurement Specification v0.1. These are image mappings
created for Pattern Play; no frozen core formula is edited or canonical rule
promoted.

| Panel | Input and calculation | Meaning |
| --- | --- | --- |
| Colors found | Up to four median-cut color bins from a maximum 256×256 RGB sample, with pixel shares | Sampled image colors; these can differ from the five-color art palette's decorative anchor |
| Color coherence | Original `coherence_score` on equally weighted brightness values of the sampled dominant colors | Dispersion of those brightness values, clipped by the unchanged core; not a grade for the photo |
| Color spread | Original `harmonic_entropy` on color-bin pixel counts | Spread of the sampled color populations in bits; not temporal or multiscale complexity |
| 3–6–9 visual rhythm | Mean brightness along each axis of a 128×128 grid, compared with `R_369` at 36 equally spaced phases | Largest absolute mean-centered cosine similarity across the two axes; a product-defined fit to the core wave |
| Frame relation to φ | Long side divided by short side, compared with original `core.phi` | Geometric reference and absolute gap; original EXIF-corrected image dimensions are used |
| Mirrored balance | One minus mean absolute normalized-brightness difference from each reflected grid | Pixel resemblance across left/right and top/bottom reflections; uniform regions can score highly |
| φ–π balance projection | Original `fractal_harmonic_projection` on the two dimensionless mirror similarities | Coupled coordinate transform retained in the export; not an estimate of fractal dimension |
| φ–π tone modulation | Original `phi_pi_modulation` on mean dominant-color brightness in [0,1] | A dimensionless core transform retained in the export; no physical frequency is inferred |

Brightness uses `.2126 R + .7152 G + .0722 B`, divided by 255, on encoded RGB.
It is a reproducible image descriptor, not a physical luminance measurement.
RGBA and indexed transparency are composited over white. The comparison grid is
resized to 128×128 for axis profiles and mirror comparisons. Crop, resolution and
framing can therefore change a reading.

Interpretation text uses declared product thresholds: coherence ≥0.75 for close
tones, ≥0.4 for middle-range variation, otherwise stronger tonal contrast;
rhythm fit ≥0.6 for a clear fit; absolute frame-ratio gap ≤0.15 for proximity to
φ. Near-black samples receive a separate zero-baseline explanation. These are
versioned artistic reading rules, not a newly established canonical mapping.

The original core's zero and near-zero handling is retained. In a one-color
sample, entropy can have a tiny negative floating-point value from its historical
epsilon; the export retains it and the display rounds/clamps that numerical
artifact to zero. Constant nonzero colors can have coherence 1. No composite
personal, wellness or physiological score is generated.

Exports include derived brightness profiles and color values for calculation
replay. They do not include original photo bytes, a delivery email or payment
information. The original `.har360` codec binds the payload hash. The record
stays `UNDER_REVIEW` with `canonical_authority_granted: false`.
