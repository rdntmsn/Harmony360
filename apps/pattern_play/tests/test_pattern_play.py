from __future__ import annotations

import hashlib
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import numpy as np
from PIL import Image

from pattern_play.commerce import order_note, payment_url
from pattern_play.engine import CORE, PALETTES, Design, from_recipe, from_reference, palette_from_image, png_bytes, reference, render
from pattern_play.fulfill import fulfill
from pattern_play._numeric.serialization import load_har360


class PatternTests(unittest.TestCase):
    def test_deterministic_render_and_distinct_seed_and_style(self):
        first = np.asarray(render(Design(), 96, 96))
        self.assertTrue(np.array_equal(first, np.asarray(render(Design(), 96, 96))))
        for other in (Design(seed=123), Design(style="orbit"), Design(energy=120)):
            self.assertFalse(np.array_equal(first, np.asarray(render(other, 96, 96))))

    def test_all_four_original_core_methods_execute(self):
        names = ("R_369", "fractal_harmonic_wavefield", "fractal_harmonic_projection", "phi_pi_modulation")
        from contextlib import ExitStack
        with ExitStack() as stack:
            calls = [stack.enter_context(patch.object(CORE, name, wraps=getattr(CORE, name))) for name in names]
            render(Design(), 96, 96)
        self.assertTrue(all(call.call_count > 0 for call in calls))

    def test_recipe_and_order_reference_reconstruct_exact_pixels(self):
        original = Design("ripple", 999999, 180, ("001122", "334455", "667788", "99aabb", "ccddee"))
        self.assertEqual(original, from_recipe(original.recipe()))
        recovered = from_reference(reference(original))
        self.assertEqual(original, recovered)
        self.assertEqual(png_bytes(render(original, 64, 64)), png_bytes(render(recovered, 64, 64)))

    def test_changed_or_malformed_reference_is_rejected(self):
        good = reference(Design())
        for bad in (good[:-1] + ("f" if good[-1] != "f" else "e"), "P1-20-1-80-abc-def", "../../etc/passwd", good.replace("-369-", "-0369-")):
            with self.subTest(value=bad), self.assertRaises(ValueError):
                from_reference(bad)

    def test_invalid_values_and_dimensions_are_rejected(self):
        for kwargs in ({"seed": True}, {"energy": 500}, {"style": "script"}, {"colors": ("ffffff",)}):
            with self.assertRaises(ValueError):
                Design(**kwargs)
        with self.assertRaises(ValueError):
            render(Design(), 9000, 9000)

    def test_photo_palette_has_no_photo_bytes_in_recipe(self):
        image = Image.new("RGB", (80, 80), "coral")
        raw = png_bytes(image)
        palette = palette_from_image(raw)
        self.assertEqual(len(palette), 5)
        recipe = Design(colors=palette).recipe()
        self.assertEqual(from_reference(reference(Design(colors=palette))).colors, palette)
        self.assertNotIn("image", recipe)
        self.assertNotIn("photo", json.dumps(recipe))

    def test_bad_oversized_and_unaccepted_photo_formats_fail(self):
        gif = io.BytesIO()
        Image.new("RGB", (4, 4)).save(gif, format="GIF")
        for raw in (b"not an image", gif.getvalue()):
            with self.assertRaises(ValueError):
                palette_from_image(raw)
        with patch("pattern_play.engine.MAX_IMAGE_PIXELS", 100):
            with self.assertRaises(ValueError):
                palette_from_image(png_bytes(Image.new("RGB", (20, 20))))
        with patch("pattern_play.engine.MAX_IMAGE_BYTES", 10):
            with self.assertRaises(ValueError):
                palette_from_image(b"x"*11)

    def test_payment_urls_use_actual_provider_hosts(self):
        self.assertEqual(payment_url("https://paypal.me/RdnTmsn", "paypal"), "https://paypal.me/RdnTmsn/5USD")
        self.assertEqual(payment_url("https://cash.app/$rctumsun", "cashapp"), "https://cash.app/$rctumsun")
        for bad in ("javascript:alert(1)", "https://paypal.me.evil.invalid/name", "https://paypal.me@evil.invalid/a", "http://paypal.me/name"):
            with self.assertRaises(ValueError):
                payment_url(bad, "paypal")

    def test_delivery_note_requires_email_and_preserves_reference(self):
        ref = reference(Design())
        self.assertIn(ref, order_note(ref, "buyer@example.com"))
        with self.assertRaises(ValueError):
            order_note(ref, "")

    def test_retained_core_files_match_their_source_receipts(self):
        root = Path(__file__).resolve().parents[1]
        provenance = json.loads((root/"CORE_PROVENANCE.json").read_text())
        for item in provenance["files"]:
            raw = (root/"pattern_play/_numeric"/item["name"]).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), item["sha256"])
            self.assertEqual(hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest(), item["git_blob_sha"])

    def test_real_delivery_pack_dimensions_hashes_and_native_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)/"pack.zip"
            with self.assertRaises(ValueError):
                fulfill(reference(Design()), "", output)
            fulfill(reference(Design()), "TEST-FIXTURE-NO-REAL-PAYMENT", output)
            with zipfile.ZipFile(output) as archive:
                expected = {"phone": (1440, 2560), "desktop": (2560, 1440), "square": (2048, 2048)}
                for name, dimensions in expected.items():
                    with Image.open(io.BytesIO(archive.read(f"pattern-play-{name}.png"))) as image:
                        self.assertEqual(image.size, dimensions)
                receipt_path = Path(temporary)/"receipt.har360"
                receipt_path.write_bytes(archive.read("creation-receipt.har360"))
                receipt = load_har360(receipt_path)
                self.assertFalse(receipt["payment"]["provider_verification_performed_by_program"])
                self.assertFalse(receipt["canonical_authority_granted"])
                for name, checksum in receipt["artifacts"].items():
                    self.assertEqual(hashlib.sha256(archive.read(name)).hexdigest(), checksum)


if __name__ == "__main__":
    unittest.main()
