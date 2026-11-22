"""Deterministic wallpaper art made by calling the original Harmony360 core."""
from __future__ import annotations

import hashlib
import io
import math
import re
import warnings
from dataclasses import asdict, dataclass

import numpy as np
from PIL import Image, ImageDraw, ImageOps, UnidentifiedImageError

from ._numeric import Harmony360

CORE = Harmony360()
STYLES = ("bloom", "orbit", "ripple")
PALETTES = {
    "cosmic": ("100a28", "52278a", "d254ae", "ff9a82", "ffedcc"),
    "sunset": ("22142c", "79365e", "d75564", "ffad72", "fff1b9"),
    "lagoon": ("061e33", "195e6c", "28a7a1", "8ed4ac", "f0e6ae"),
    "electric": ("111329", "333994", "578ed0", "cf6fe0", "f9dfc9"),
}
CORE_METHODS = ("R_369", "fractal_harmonic_wavefield", "fractal_harmonic_projection", "phi_pi_modulation")
MAX_IMAGE_BYTES = 12 * 1024 * 1024
MAX_IMAGE_PIXELS = 24_000_000
FORMATS = {"PNG", "JPEG", "WEBP"}


@dataclass(frozen=True)
class Design:
    style: str = "bloom"
    seed: int = 369
    energy: int = 85
    colors: tuple[str, ...] = PALETTES["cosmic"]

    def __post_init__(self):
        if self.style not in STYLES:
            raise ValueError("Choose Bloom, Orbit or Ripple")
        if type(self.seed) is not int or not 0 <= self.seed <= 999999:
            raise ValueError("Seed must be an integer from 0 to 999999")
        if type(self.energy) is not int or not 20 <= self.energy <= 180:
            raise ValueError("Energy must be an integer from 20 to 180")
        if len(self.colors) != 5 or any(not re.fullmatch(r"[0-9a-f]{6}", c) for c in self.colors):
            raise ValueError("A palette needs five six-digit lowercase hex colors")

    def recipe(self) -> dict:
        return {"schema": "harmony360.pattern-play.v1", **asdict(self),
                "colors": list(self.colors), "order_reference": reference(self)}


def from_recipe(value: dict) -> Design:
    if not isinstance(value, dict) or value.get("schema") != "harmony360.pattern-play.v1":
        raise ValueError("Unknown Pattern Play recipe")
    design = Design(value["style"], value["seed"], value["energy"], tuple(value["colors"]))
    if value.get("order_reference") != reference(design):
        raise ValueError("Recipe and order reference differ")
    return design


def reference(design: Design) -> str:
    """A self-contained, replayable design reference; never evidence of payment."""
    body = f"P1-{STYLES.index(design.style)}-{design.seed}-{design.energy}-" + "".join(design.colors)
    check = hashlib.sha256(body.encode()).hexdigest()[:6]
    return body + "-" + check


def from_reference(value: str) -> Design:
    parts = value.strip().split("-")
    if len(parts) != 6 or parts[0] != "P1" or not re.fullmatch(r"[0-2]", parts[1]):
        raise ValueError("Invalid Pattern Play order reference")
    if not parts[2].isdigit() or not parts[3].isdigit() or not re.fullmatch(r"[0-9a-f]{30}", parts[4]):
        raise ValueError("Invalid Pattern Play order reference")
    colors = tuple(parts[4][i:i+6] for i in range(0, 30, 6))
    result = Design(STYLES[int(parts[1])], int(parts[2]), int(parts[3]), colors)
    if reference(result) != value.strip():
        raise ValueError("Order reference checksum differs")
    return result


def palette_from_image(raw: bytes) -> tuple[str, ...]:
    """Extract colors locally. No image bytes are included in a recipe or order."""
    if len(raw) > MAX_IMAGE_BYTES:
        raise ValueError("Choose a photo smaller than 12 MB")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as image:
                if image.format not in FORMATS:
                    raise ValueError("Use a JPG, PNG or WebP photo")
                if image.width * image.height > MAX_IMAGE_PIXELS:
                    raise ValueError("Choose a photo with fewer than 24 million pixels")
                image = ImageOps.exif_transpose(image)
                image.thumbnail((128, 128))
                if "A" in image.getbands():
                    flattened = Image.new("RGBA", image.size, "white")
                    flattened.alpha_composite(image.convert("RGBA"))
                    image = flattened.convert("RGB")
                else:
                    image = image.convert("RGB")
                quantized = image.quantize(colors=4, method=Image.Quantize.MEDIANCUT)
                palette = quantized.getpalette()
                entries = sorted(quantized.getcolors(), reverse=True)
                colors = [tuple(palette[index*3:index*3+3]) for _, index in entries]
                while len(colors) < 4:
                    base = colors[-1]
                    colors.append(tuple(min(255, int(c*.7 + 64)) for c in base))
                colors.sort(key=lambda c: .2126*c[0]+.7152*c[1]+.0722*c[2])
                # Keep a dark anchor and four colors derived from the photo.
                dark = tuple(max(5, int(c*.16)) for c in colors[0])
                return tuple("%02x%02x%02x" % c for c in [dark, *colors])
    except (UnidentifiedImageError, Image.DecompressionBombError, Image.DecompressionBombWarning, OSError):
        raise ValueError("This photo could not be read. Try a smaller JPG, PNG or WebP.") from None


def render(design: Design, width: int = 640, height: int = 640) -> Image.Image:
    if type(width) is not int or type(height) is not int or min(width, height) < 32 or max(width, height) > 4096 or width*height > 9_000_000:
        raise ValueError("Unsupported artwork dimensions")
    # Rows bound memory use on phones and also allow larger seller-side exports.
    colors = np.array([[int(color[i:i+2], 16) for i in (0, 2, 4)] for color in design.colors], dtype=np.float32)
    canvas = np.empty((height, width, 3), dtype=np.uint8)
    aspect = width / height
    x_axis = np.linspace(-1, 1, width, dtype=np.float64) * max(1.0, aspect)
    y_axis = np.linspace(-1, 1, height, dtype=np.float64) * max(1.0, 1/aspect)
    phase = (design.seed * CORE.phi % 1) * 2 * CORE.pi
    energy = design.energy / 100
    modulation = float(CORE.phi_pi_modulation((design.seed % 997 + 1) / 997))
    for start in range(0, height, 96):
        x, y = np.meshgrid(x_axis, y_axis[start:start+96])
        angle = np.arctan2(y, x)
        radius = np.sqrt(x*x + y*y)
        wave = CORE.R_369(angle + phase)
        fx, fy = CORE.fractal_harmonic_projection(x, y)
        harmonic = CORE.fractal_harmonic_wavefield(fx*.30*energy + phase, fy*.30*energy)
        if design.style == "bloom":
            field = radius * (8 + energy*7) - wave*(.35 + energy*.15) + harmonic*.25 + phase
        elif design.style == "orbit":
            field = (fx*np.cos(phase) + fy*np.sin(phase)) * energy * 1.3 + harmonic*.85 + wave*.18
        else:
            field = np.sqrt((x+.24*modulation)**2+(y-.22*modulation)**2)*(11+energy*5) + harmonic*.7 + wave*.12 + phase
        t = (.5 + .5*np.sin(field)) * 3.999
        index = np.floor(t).astype(np.int32)
        f = (t-index)[..., None]
        f = f*f*(3-2*f)
        rgb = colors[index]*(1-f) + colors[np.minimum(index+1, 4)]*f
        # Fine contour highlights and a soft edge falloff are decorative.
        highlight = np.exp(-((np.sin(field+.2))/.075)**2)[..., None]*.10
        rgb = rgb*(1-highlight) + colors[-1]*highlight
        shade = np.clip(1.04 - radius*.14, .58, 1.0)[..., None]
        canvas[start:start+len(y)] = np.clip(rgb*shade, 0, 255).astype(np.uint8)
    return Image.fromarray(canvas)


def png_bytes(image: Image.Image) -> bytes:
    output = io.BytesIO()
    image.save(output, format="PNG", optimize=False)
    return output.getvalue()


def preview_png(design: Design) -> bytes:
    image = render(design, 640, 640)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((18, 594, 235, 625), radius=10, fill=(12, 10, 24))
    draw.text((30, 604), "PATTERN PLAY  /  FREE PREVIEW", fill=(255, 239, 218))
    return png_bytes(image)

