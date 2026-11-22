"""Build the static PyScript site without shadowing Python's build package."""
from pathlib import Path
import json
import shutil
from pattern_play.engine import Design, render

root = Path(__file__).resolve().parent
assets = root / "web/assets"
assets.mkdir(parents=True, exist_ok=True)
for style in ("bloom", "orbit", "ripple"):
    render(Design(style=style), 800, 800).save(assets / (style + ".webp"), quality=90)
dist = root / "dist"
dist.mkdir(exist_ok=True)
for name in ("index.html", "style.css", "app.py", "merchant.json"):
    shutil.copy2(root / "web" / name, dist / name)
shutil.copytree(root / "web/assets", dist / "assets", dirs_exist_ok=True)
shutil.copytree(root / "pattern_play", dist / "pattern_play", dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", "fulfill.py"))
files = {"./" + str(p.relative_to(dist)): "./" + str(p.relative_to(dist))
         for p in (dist / "pattern_play").rglob("*.py")}
(dist / "pyscript.json").write_text(json.dumps({"interpreter": "https://cdn.jsdelivr.net/pyodide/v0.29.0/full/pyodide.mjs", "packages": ["numpy", "pillow"], "files": files}, indent=2))
print("Built Pattern Play in", dist)

