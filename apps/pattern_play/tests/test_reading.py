import io
import json
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

import numpy as np
from PIL import Image

from pattern_play.engine import CORE, Design, png_bytes, reference
from pattern_play.reading import GRID, METHOD, read_image, read_photo, reading_carrier, rhythm_fit
from pattern_play._numeric.serialization import load_har360


class ReadingTests(unittest.TestCase):
    def test_known_369_wave_fits_and_noise_and_shuffle_do_not(self):
        theta = np.arange(GRID)*2*CORE.pi/GRID
        wave = CORE.R_369(theta)
        profile = .5 + wave*.1
        self.assertAlmostEqual(rhythm_fit(profile)["value"], 1.0, places=12)
        generator = np.random.default_rng(360)
        self.assertLess(rhythm_fit(generator.permutation(profile))["value"], .5)
        self.assertLess(rhythm_fit(generator.normal(size=GRID))["value"], .5)
        self.assertEqual(rhythm_fit(np.ones(GRID))["value"], 0.0)

    def test_degenerate_and_nonfinite_profiles_are_explicit(self):
        self.assertEqual(rhythm_fit(np.zeros(GRID))["status"], "NO_VARIATION")
        for profile in ([1, 2], np.full(GRID, float("nan")), np.ones((2, GRID))):
            with self.assertRaises(ValueError):
                rhythm_fit(profile)

    def test_reading_calls_the_actual_core_for_all_its_observables(self):
        names = ("coherence_score", "harmonic_entropy", "R_369", "phi_pi_modulation", "fractal_harmonic_projection")
        image = Image.fromarray(np.tile(np.arange(GRID, dtype=np.uint8), (GRID, 1)))
        with ExitStack() as stack:
            calls = [stack.enter_context(patch.object(CORE, name, wraps=getattr(CORE, name))) for name in names]
            reading = read_image(image, source_kind="UPLOADED_PHOTO")
        self.assertTrue(all(call.call_count > 0 for call in calls))
        self.assertEqual(reading["core_calls"], list(names))
        self.assertFalse(reading["canonical_authority_granted"])

    def test_exported_inputs_replay_the_core_results(self):
        image = Image.new("RGB", (40, 20), "coral")
        reading = read_image(image, source_kind="UPLOADED_PHOTO")
        inputs, values = reading["derived_inputs"], reading["core_observables"]
        self.assertEqual(CORE.coherence_score(inputs["dominant_color_brightness"]), values["core_dispersion_coherence"])
        self.assertEqual(CORE.phi_pi_modulation(float(np.mean(inputs["dominant_color_brightness"]))), values["phi_pi_tone_modulation"])
        self.assertEqual(len(inputs["horizontal_brightness_profile"]), GRID)
        self.assertEqual(len(inputs["vertical_brightness_profile"]), GRID)

    def test_constant_color_and_black_have_distinct_truthful_readings(self):
        solid = read_image(Image.new("RGB", (60, 40), "coral"), source_kind="UPLOADED_PHOTO")
        black = read_image(Image.new("RGB", (60, 40), "black"), source_kind="UPLOADED_PHOTO")
        self.assertEqual(solid["core_observables"]["core_dispersion_coherence"], 1.0)
        self.assertEqual(black["core_observables"]["core_dispersion_coherence"], 0.0)
        self.assertIn("dark", black["interpretation"]["title"])
        self.assertEqual(solid["product_mappings"]["rhythm_369"]["value"], 0.0)
        json.dumps(black, allow_nan=False)

    def test_palette_coherence_and_entropy_are_permutation_invariant(self):
        x = np.arange(GRID)*2*CORE.pi/GRID
        row = np.clip((.5+.13*CORE.R_369(x))*255, 0, 255).astype(np.uint8)
        original = np.tile(row, (GRID, 1))
        shuffled = original[:, np.random.default_rng(369).permutation(GRID)]
        first = read_image(Image.fromarray(original), source_kind="UPLOADED_PHOTO")
        second = read_image(Image.fromarray(shuffled), source_kind="UPLOADED_PHOTO")
        for key in ("core_dispersion_coherence", "harmonic_color_spread_bits"):
            self.assertAlmostEqual(first["core_observables"][key], second["core_observables"][key], places=12)
        self.assertGreater(first["product_mappings"]["rhythm_369"]["value"], .99)
        self.assertLess(second["product_mappings"]["rhythm_369"]["value"], .5)

    def test_frame_relation_uses_the_original_dimensions(self):
        reading = read_image(Image.new("RGB", (128, 80), "pink"), source_kind="UPLOADED_PHOTO", source_size=(1618, 1000))
        self.assertEqual(reading["observed"]["frame_ratio_long_to_short"], 1.618)
        self.assertLess(reading["product_mappings"]["phi_frame"]["absolute_gap"], .001)
        self.assertEqual(reading["source"]["width"], 1618)

    def test_exif_orientation_is_applied_before_reporting_dimensions(self):
        image = Image.new("RGB", (80, 40), "teal")
        exif = Image.Exif()
        exif[274] = 6
        stream = io.BytesIO()
        image.save(stream, format="JPEG", exif=exif)
        reading, thumbnail = read_photo(stream.getvalue())
        self.assertEqual((reading["source"]["width"], reading["source"]["height"]), (40, 80))
        with Image.open(io.BytesIO(thumbnail)) as loaded:
            self.assertEqual(loaded.size, (40, 80))

    def test_invalid_uploads_and_limits_fail_before_a_reading(self):
        gif = io.BytesIO()
        Image.new("RGB", (10, 10)).save(gif, format="GIF")
        for raw in (b"invalid-image", gif.getvalue()):
            with self.assertRaises(ValueError):
                read_photo(raw)
        with patch("pattern_play.reading.MAX_IMAGE_BYTES", 10):
            with self.assertRaises(ValueError):
                read_photo(b"x"*11)

    def test_indexed_transparent_png_uses_the_visible_white_background(self):
        image = Image.new("P", (40, 40), 0)
        image.putpalette([255, 0, 0] + [0]*765)
        image.info["transparency"] = 0
        raw = png_bytes(image)
        reading, _ = read_photo(raw)
        self.assertEqual(reading["observed"]["dominant_colors"][0]["hex"], "ffffff")
        from pattern_play.engine import palette_from_image
        self.assertNotIn("ff0000", palette_from_image(raw))

    def test_native_carrier_contains_reading_but_not_the_photo_or_payment(self):
        raw = png_bytes(Image.new("RGB", (30, 40), "blue"))
        reading, _ = read_photo(raw)
        carrier = reading_carrier(reading, reference(Design()))
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)/"reading.har360"
            path.write_bytes(carrier)
            payload = load_har360(path)
            self.assertEqual(payload["reading"]["schema"], METHOD)
            self.assertFalse(payload["canonical_authority_granted"])
            self.assertNotIn("payment", payload)
            self.assertNotIn("photo_bytes", payload["reading"])
            altered = json.loads(carrier)
            altered["payload"]["reading"]["core_observables"]["core_dispersion_coherence"] = .123
            path.write_text(json.dumps(altered))
            with self.assertRaises(ValueError):
                load_har360(path)


if __name__ == "__main__":
    unittest.main()
