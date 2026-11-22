"""Versioned image-to-Harmony360 mappings for Pattern Play's visual reading."""
from __future__ import annotations

import hashlib
import io
import json
import tempfile
import warnings
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

from .engine import CORE, FORMATS, MAX_IMAGE_BYTES, MAX_IMAGE_PIXELS, png_bytes
from ._numeric.serialization import save_har360, load_har360

METHOD = "harmony360.pattern-play.visual-reading.v0.2"
GRID = 128
PHASE_STEPS = 36


def _luminance(rgb):
    # Deliberately a weighted encoded-RGB brightness descriptor, not physical luminance.
    return np.asarray(rgb, dtype=np.float64) @ np.array([.2126, .7152, .0722]) / 255


def rhythm_fit(profile) -> dict:
    values = np.asarray(profile, dtype=np.float64)
    if values.ndim != 1 or len(values) != GRID or not np.isfinite(values).all():
        raise ValueError("Rhythm input must contain 128 finite brightness samples")
    centered = values - values.mean()
    norm = float(np.linalg.norm(centered))
    if norm <= 1e-12:
        return {"value": 0.0, "phase_radians": None, "status": "NO_VARIATION"}
    theta = np.arange(GRID, dtype=np.float64) * 2 * CORE.pi / GRID
    best, phase = 0.0, 0.0
    for step in range(PHASE_STEPS):
        offset = step * 2 * CORE.pi / PHASE_STEPS
        template = CORE.R_369(theta + offset)
        template = template - template.mean()
        score = abs(float(np.dot(centered, template))) / (norm * float(np.linalg.norm(template)))
        if score > best:
            best, phase = score, offset
    return {"value": float(np.clip(best, 0, 1)), "phase_radians": phase, "status": "COMPUTED"}


def _rgb_image(image: Image.Image) -> Image.Image:
    if "A" in image.getbands() or (image.mode == "P" and "transparency" in image.info):
        background = Image.new("RGBA", image.size, "white")
        background.alpha_composite(image.convert("RGBA"))
        return background.convert("RGB")
    return image.convert("RGB")


def read_image(image: Image.Image, *, source_kind: str, source_size=None) -> dict:
    if source_kind not in {"UPLOADED_PHOTO", "GENERATED_ARTWORK"}:
        raise ValueError("Unknown reading source")
    if not image.width or not image.height or image.width * image.height > MAX_IMAGE_PIXELS:
        raise ValueError("Unsupported image dimensions")
    source_width, source_height = source_size or image.size
    if min(source_width, source_height) <= 0:
        raise ValueError("Unsupported source dimensions")
    rgb = _rgb_image(image)
    rgb.thumbnail((256, 256), Image.Resampling.LANCZOS)
    quantized = rgb.quantize(colors=4, method=Image.Quantize.MEDIANCUT)
    palette = quantized.getpalette()
    entries = sorted(quantized.getcolors(), reverse=True)
    total = rgb.width * rgb.height
    colors = [{"hex": "%02x%02x%02x" % tuple(palette[index*3:index*3+3]),
               "sample_pixels": count, "share": count/total}
              for count, index in entries]
    tones = _luminance([[int(color["hex"][i:i+2], 16) for i in (0, 2, 4)] for color in colors])
    coherence = float(CORE.coherence_score(tones))
    entropy = float(CORE.harmonic_entropy([row["sample_pixels"] for row in colors]))
    grid = np.asarray(rgb.resize((GRID, GRID), Image.Resampling.BILINEAR), dtype=np.float64)
    brightness = _luminance(grid)
    horizontal_profile = brightness.mean(axis=0)
    vertical_profile = brightness.mean(axis=1)
    horizontal = rhythm_fit(horizontal_profile)
    vertical = rhythm_fit(vertical_profile)
    axis = "horizontal" if horizontal["value"] >= vertical["value"] else "vertical"
    fit = horizontal if axis == "horizontal" else vertical
    mirror_x = float(np.clip(1-np.mean(np.abs(brightness - brightness[:, ::-1])), 0, 1))
    mirror_y = float(np.clip(1-np.mean(np.abs(brightness - brightness[::-1, :])), 0, 1))
    projection = [float(v) for v in CORE.fractal_harmonic_projection(mirror_x, mirror_y)]
    mean_tone = float(np.mean(tones))
    modulation = float(CORE.phi_pi_modulation(mean_tone))
    ratio = max(source_width, source_height)/min(source_width, source_height)
    gap = abs(ratio - CORE.phi)
    if mean_tone <= 1e-12:
        tone_title = "A deep, dark starting point"
        tone_text = "The sample is near black. Harmony360's core returns its zero-baseline coherence value, so the darkness leads this visual reading."
    elif coherence >= .75:
        tone_title = "A palette that holds together"
        tone_text = "The sampled colors sit close in brightness under the Harmony360 coherence formula. Read this as a quiet, unified tonal foundation."
    elif coherence >= .4:
        tone_title = "Light and shade in conversation"
        tone_text = "The sampled colors move between lighter and darker tones. This Harmony360 reading treats that contrast as a balance of unity and variation."
    else:
        tone_title = "A palette with visual tension"
        tone_text = "The sampled colors have strong light-dark separation under the core formula. This Harmony360 reading treats that separation as an energetic contrast in the artwork."
    rhythm_text = ("The brightness profile has a clear fit to the core's 3–6–9 wave across the " + axis + " axis."
                   if fit["value"] >= .6 else
                   "The brightness profile has a softer fit to the core's 3–6–9 wave; color and shape can lead the artwork instead.")
    frame = "near the golden-ratio reference" if gap <= .15 else ("more elongated than the golden-ratio reference" if ratio > CORE.phi else "more compact than the golden-ratio reference")
    result = {
        "schema": METHOD, "lifecycle_state": "UNDER_REVIEW", "canonical_authority_granted": False,
        "source": {"kind": source_kind, "width": source_width, "height": source_height,
                   "comparison_grid": [GRID, GRID], "sample_size": [rgb.width, rgb.height],
                   "sample_sha256": hashlib.sha256(rgb.tobytes()).hexdigest()},
        "observed": {"dominant_colors": colors, "frame_ratio_long_to_short": ratio,
                     "mirror_similarity_horizontal": mirror_x, "mirror_similarity_vertical": mirror_y,
                     "brightness_descriptor": "weighted encoded RGB; alpha composited over white"},
        "core_observables": {"core_dispersion_coherence": coherence, "harmonic_color_spread_bits": entropy,
                             "phi_pi_tone_modulation": modulation, "phi_pi_balance_projection": projection},
        "derived_inputs": {"dominant_color_brightness": tones.tolist(),
                           "horizontal_brightness_profile": horizontal_profile.tolist(),
                           "vertical_brightness_profile": vertical_profile.tolist()},
        "product_mappings": {"rhythm_369": {"value": fit["value"], "axis": axis, "horizontal": horizontal,
                                            "vertical": vertical, "phase_steps": PHASE_STEPS},
                             "phi_frame": {"phi": float(CORE.phi), "absolute_gap": gap, "description": frame}},
        "interpretation": {"classification": "HARMONY360_ARTISTIC_INTERPRETATION", "title": tone_title,
                           "text": tone_text + " " + rhythm_text,
                           "frame_text": "The frame is " + frame + "."},
        "methods": {"coherence_input": "equally weighted brightness values of up to four sampled dominant colors",
                    "entropy_input": "sample pixel counts of the quantized color bins",
                    "rhythm": "maximum absolute mean-centered cosine similarity with R_369 across two axes and 36 phases",
                    "balance_projection_input": "horizontal and vertical mirror similarities, each dimensionless in [0,1]",
                    "modulation_input": "mean dominant-color brightness, dimensionless in [0,1]",
                    "phi_relation": "absolute difference between long/short frame ratio and core.phi",
                    "interpretation_thresholds": {"coherence_high": .75, "coherence_middle": .4, "rhythm_clear": .6, "phi_near_gap": .15},
                    "mapping_scope": "Pattern Play v0.2 product mappings above the original core; not a new canonical theory rule"},
        "core_calls": ["coherence_score", "harmonic_entropy", "R_369", "phi_pi_modulation", "fractal_harmonic_projection"],
        "core_identity": CORE.core_manifest()["identity"],
        "meaning": "A Harmony360 visual interpretation of this image; the numbers describe the declared image mappings.",
    }
    json.dumps(result, allow_nan=False)
    return result


def read_photo(raw: bytes) -> tuple[dict, bytes]:
    if len(raw) > MAX_IMAGE_BYTES:
        raise ValueError("Choose a photo smaller than 12 MB")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as opened:
                if opened.format not in FORMATS:
                    raise ValueError("Use a JPG, PNG or WebP photo")
                if opened.width * opened.height > MAX_IMAGE_PIXELS:
                    raise ValueError("Choose a photo with fewer than 24 million pixels")
                image = ImageOps.exif_transpose(opened)
                dimensions = image.size
                image.thumbnail((256, 256), Image.Resampling.LANCZOS)
                image = _rgb_image(image)
                reading = read_image(image, source_kind="UPLOADED_PHOTO", source_size=dimensions)
                return reading, png_bytes(image)
    except (UnidentifiedImageError, Image.DecompressionBombError, Image.DecompressionBombWarning, OSError):
        raise ValueError("This photo could not be read. Try a smaller JPG, PNG or WebP.") from None


def reading_carrier(reading: dict, design_reference: str) -> bytes:
    json.dumps(reading, allow_nan=False)
    payload = {"schema": METHOD + ".export", "reading": reading,
               "artwork_design_reference": design_reference, "canonical_authority_granted": False,
               "scope": "Local image reading; this export is separate from the paid wallpaper fulfillment reference."}
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary)/"harmony360-reading.har360"
        save_har360(payload, path, metadata={"product": "Pattern Play", "mapping_version": METHOD})
        if load_har360(path) != payload:
            raise ValueError("Reading carrier round-trip mismatch")
        return path.read_bytes()
