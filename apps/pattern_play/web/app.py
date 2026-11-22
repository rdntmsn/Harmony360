"""Browser UI in Python. Photos remain local; payments open provider pages."""
import asyncio
import base64
import json
import random

from pyscript import document, window, when
from pyodide.http import pyfetch
from pyodide.ffi import to_js

from pattern_play.engine import Design, PALETTES, palette_from_image, preview_png, reference, render, png_bytes
from pattern_play.commerce import order_note, payment_url
from pattern_play.reading import read_image, read_photo, reading_carrier

state = {"style": "bloom", "seed": 369, "energy": 85, "colors": PALETTES["cosmic"],
         "palette": "cosmic", "copied": False, "ready": False, "revision": 0, "merchant": {},
         "photo_reading": None, "photo_thumbnail": None, "rendering": False}
download_urls = {}


def el(name):
    return document.getElementById(name)


def design():
    return Design(state["style"], state["seed"], state["energy"], tuple(state["colors"]))


def png_url(raw):
    return "data:image/png;base64," + base64.b64encode(raw).decode("ascii")


def prepare_download(element_id, raw, mimetype):
    """Use a normal Blob download link rather than a large data-URL navigation."""
    parts = window.Array.new()
    parts.push(to_js(raw))
    options = window.Object.new()
    options.type = mimetype
    blob = window.Blob.new(parts, options)
    url = window.URL.createObjectURL(blob)
    previous = download_urls.get(element_id)
    el(element_id).href = url
    download_urls[element_id] = url
    if previous:
        window.URL.revokeObjectURL(previous)


def status(message, error=False):
    el("status").textContent = message
    el("status").classList.toggle("error", error)


def download(raw, filename, mimetype):
    link = document.createElement("a")
    link.href = "data:" + mimetype + ";base64," + base64.b64encode(raw).decode("ascii")
    link.download = filename
    document.body.appendChild(link)
    link.click()
    link.remove()


def refresh_controls():
    for button in document.querySelectorAll(".style-choice"):
        active = button.getAttribute("data-style") == state["style"]
        button.classList.toggle("selected", active)
        button.setAttribute("aria-pressed", str(active).lower())
    for button in document.querySelectorAll(".palette-choice"):
        active = button.getAttribute("data-palette") == state["palette"]
        button.classList.toggle("selected", active)
        button.setAttribute("aria-pressed", str(active).lower())
    el("palette-name").textContent = "Photo colors" if state["palette"] == "photo" else state["palette"].title()
    el("energy-label").textContent = str(state["energy"]) + "%"
    el("design-name").textContent = state["style"].upper() + " / " + el("palette-name").textContent.upper()


def update_order(*_):
    email = el("delivery-email").value.strip()
    enabled = False
    try:
        if not el("delivery-email").checkValidity():
            raise ValueError("Enter your delivery email")
        note = order_note(reference(design()), email)
        el("order-note").value = note
        enabled = bool(state["copied"] and state["merchant"].get("sales_enabled"))
    except ValueError:
        el("order-note").value = "Order: " + reference(design()) + "\nAdd your delivery email above."
    prepare_download("download-recipe", json.dumps(design().recipe(), indent=2).encode(), "application/json")
    for provider, name in (("paypal", "pay-paypal"), ("cashapp", "pay-cashapp")):
        anchor = el(name)
        link = payment_url(state["merchant"].get(provider + "_url"), provider)
        if enabled and link:
            anchor.href = link
            anchor.setAttribute("aria-disabled", "false")
            anchor.setAttribute("tabindex", "0")
        else:
            anchor.removeAttribute("href")
            anchor.setAttribute("aria-disabled", "true")
            anchor.setAttribute("tabindex", "-1")


def show_reading(reading, thumbnail):
    source = reading["source"]
    values = reading["core_observables"]
    observed = reading["observed"]
    rhythm = reading["product_mappings"]["rhythm_369"]
    el("reading-source").textContent = "YOUR PHOTO" if source["kind"] == "UPLOADED_PHOTO" else "YOUR GENERATED ART"
    el("reading-thumb").src = thumbnail
    el("reading-thumb").alt = "The photo being read" if source["kind"] == "UPLOADED_PHOTO" else "The generated art being read"
    el("reading-source-detail").textContent = f'{source["width"]} × {source["height"]} pixels'
    el("reading-title").textContent = reading["interpretation"]["title"]
    el("reading-summary").textContent = reading["interpretation"]["text"]
    el("reading-coherence").textContent = f'{values["core_dispersion_coherence"]:.2f}'
    el("reading-rhythm").textContent = f'{rhythm["value"]:.2f}'
    el("reading-rhythm-axis").textContent = rhythm["axis"].title() + " brightness profile"
    ratio = observed["frame_ratio_long_to_short"]
    el("reading-frame").textContent = (f'{ratio:.3f}:1' if ratio < 1000 else f'{ratio:.3g}:1')
    el("reading-frame-detail").textContent = reading["interpretation"]["frame_text"]
    el("reading-balance").textContent = f'{observed["mirror_similarity_horizontal"]*100:.0f}% / {observed["mirror_similarity_vertical"]*100:.0f}%'
    el("reading-spread").textContent = f'Color spread: {max(0,values["harmonic_color_spread_bits"]):.2f} bits across the sampled color bins.'
    swatches = el("reading-colors")
    swatches.replaceChildren()
    for color in observed["dominant_colors"]:
        chip = document.createElement("span")
        dot = document.createElement("i")
        dot.style.backgroundColor = "#" + color["hex"]
        text = document.createElement("small")
        text.textContent = f'#{color["hex"].upper()} · {color["share"]*100:.0f}%'
        chip.appendChild(dot)
        chip.appendChild(text)
        swatches.appendChild(chip)
    prepare_download("download-reading", reading_carrier(reading, reference(design())), "application/json")
    el("download-reading").setAttribute("aria-disabled", "false")
    el("reading-panel").setAttribute("data-source-kind", source["kind"])


async def repaint():
    state["revision"] += 1
    revision = state["revision"]
    state["copied"] = False
    state["rendering"] = True
    for action in document.querySelectorAll(".open-order"):
        action.disabled = True
    for name in ("download-preview", "download-reading"):
        el(name).removeAttribute("href")
        el(name).setAttribute("aria-disabled", "true")
    refresh_controls()
    el("render-indicator").classList.remove("hidden")
    await asyncio.sleep(.05)
    if revision != state["revision"]:
        return
    try:
        current = design()
        image = render(current, 640, 640)
        raw = png_bytes(image)
        uri = png_url(raw)
        el("artwork").src = uri
        el("artwork").alt = current.style.title() + " geometric pattern in your chosen colors, generated by Harmony360"
        el("order-art").src = uri
        prepare_download("download-preview", preview_png(current), "image/png")
        el("download-preview").setAttribute("aria-disabled", "false")
        for mock in document.querySelectorAll(".mock-art"):
            mock.src = uri
        reading = state["photo_reading"] or read_image(image, source_kind="GENERATED_ARTWORK")
        thumbnail = png_url(state["photo_thumbnail"]) if state["photo_thumbnail"] else uri
        show_reading(reading, thumbnail)
        el("art-description").textContent = "Your colors. Your pattern. Your little original."
        status("Ready to play · Your photos stay on this device")
        update_order()
        for action in document.querySelectorAll(".open-order"):
            action.disabled = False
        return True
    except Exception:
        status("That pattern could not be made. Try another palette or reload.", True)
        return False
    finally:
        if revision == state["revision"]:
            state["rendering"] = False
        el("render-indicator").classList.add("hidden")


@when("click", ".style-choice")
async def choose_style(event):
    state["style"] = event.target.closest(".style-choice").getAttribute("data-style")
    await repaint()


@when("click", ".palette-choice")
async def choose_palette(event):
    key = event.target.closest(".palette-choice").getAttribute("data-palette")
    state["palette"], state["colors"] = key, PALETTES[key]
    state["photo_reading"], state["photo_thumbnail"] = None, None
    el("photo-input").value = ""
    el("clear-photo").classList.add("hidden")
    el("photo-palette").classList.add("hidden")
    el("photo-label").textContent = "Choose a photo, or try a palette below"
    await repaint()


@when("input", "#energy")
async def change_energy(event):
    state["energy"] = int(event.target.value)
    await repaint()


@when("click", "#surprise")
async def surprise(_):
    state["seed"] = random.SystemRandom().randrange(1_000_000)
    await repaint()


@when("change", "#photo-input")
async def upload_photo(event):
    if not event.target.files.length:
        return
    photo = event.target.files.item(0)
    if photo.size > 12 * 1024 * 1024:
        status("Choose a photo smaller than 12 MB.", True)
        return
    try:
        status("Borrowing the colors from your photo…")
        from js import Uint8Array
        buffer = await photo.arrayBuffer()
        raw = bytes(Uint8Array.new(buffer).to_py())
        colors = palette_from_image(raw)
        reading, thumbnail = read_photo(raw)
        del raw, buffer
        state["colors"], state["palette"] = colors, "photo"
        state["photo_reading"], state["photo_thumbnail"] = reading, thumbnail
        el("photo-label").textContent = "Colors from " + str(photo.name)[:45]
        swatches = el("photo-palette")
        swatches.replaceChildren()
        for color in colors:
            chip = document.createElement("span")
            chip.style.backgroundColor = "#" + color
            swatches.appendChild(chip)
        swatches.classList.remove("hidden")
        el("clear-photo").classList.remove("hidden")
        await repaint()
    except ValueError as exc:
        status(str(exc), True)
    except Exception:
        status("That photo could not be read. Try a JPG, PNG or WebP.", True)


@when("click", "#clear-photo")
async def clear_photo(_):
    el("photo-input").value = ""
    state["colors"], state["palette"] = PALETTES["cosmic"], "cosmic"
    state["photo_reading"], state["photo_thumbnail"] = None, None
    el("photo-label").textContent = "Choose a photo, or try a palette below"
    el("photo-palette").classList.add("hidden")
    el("clear-photo").classList.add("hidden")
    await repaint()


@when("click", ".open-order")
def open_order(_):
    if not state["ready"] or state["rendering"]:
        status("Let your pattern finish before opening the order.")
        return
    state["copied"] = False
    el("copy-note").textContent = "Copy order note"
    el("order-status").textContent = "Add your delivery email, then copy the note before paying."
    update_order()
    el("order-dialog").showModal()


@when("click", "#close-order")
def close_order(_):
    el("order-dialog").close()


@when("input", "#delivery-email")
def change_email(_):
    state["copied"] = False
    el("copy-note").textContent = "Copy order note"
    update_order()


@when("click", "#copy-note")
async def copy_note(_):
    if not el("delivery-email").reportValidity():
        return
    update_order()
    try:
        await window.navigator.clipboard.writeText(el("order-note").value)
        copied = True
    except Exception:
        el("order-note").select()
        copied = bool(document.execCommand("copy"))
    state["copied"] = copied
    if copied:
        el("copy-note").textContent = "Copied · paste into your payment note"
        el("order-status").textContent = "Choose PayPal or Cash App. Paste the copied note and pay $5."
    else:
        el("order-status").textContent = "Select the note and copy it. Your browser blocked automatic copying."
        # Manual copying can still be followed by the provider links without a fake payment assertion.
        state["copied"] = True
    update_order()


async def start():
    try:
        response = await pyfetch("./merchant.json")
        state["merchant"] = await response.json()
        for provider in ("paypal", "cashapp"):
            payment_url(state["merchant"].get(provider + "_url"), provider)
        if not await repaint():
            raise RuntimeError("Studio initialization failed")
        state["ready"] = True
        document.body.setAttribute("data-ready", "true")
        for control in document.querySelectorAll(".style-choice,.palette-choice,#photo-input,#energy,#surprise,#download-preview,#get-pack"):
            control.disabled = False
    except Exception:
        status("The studio could not start. Check your connection and reload the page.", True)


await start()

