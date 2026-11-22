"""Seller-side export after independently verifying a real payment."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from ._numeric.serialization import save_har360, load_har360
from .engine import CORE, CORE_METHODS, from_reference, png_bytes, render


def fulfill(order_reference: str, payment_reference: str, destination: Path) -> dict:
    if not payment_reference.strip():
        raise ValueError("Verify payment in your provider account, then supply its reference")
    design = from_reference(order_reference)
    files = {}
    for name, dimensions in (("phone", (1440, 2560)), ("desktop", (2560, 1440)), ("square", (2048, 2048))):
        files[f"pattern-play-{name}.png"] = png_bytes(render(design, *dimensions))
    receipt = {"schema": "harmony360.pattern-play.delivery.v1", "created_at": datetime.now(timezone.utc).isoformat(),
               "recipe": design.recipe(), "core_identity": CORE.core_manifest()["identity"],
               "core_methods_executed": list(CORE_METHODS),
               "payment": {"verification": "MANUAL_SELLER_ASSERTION", "reference_sha256": hashlib.sha256(payment_reference.encode()).hexdigest(),
                           "provider_verification_performed_by_program": False},
               "artifacts": {name: hashlib.sha256(raw).hexdigest() for name, raw in files.items()},
               "canonical_authority_granted": False,
               "meaning": "Decorative mathematical art; no scientific or therapeutic measurement."}
    with tempfile.TemporaryDirectory() as temporary:
        carrier = Path(temporary)/"creation-receipt.har360"
        save_har360(receipt, carrier, metadata={"product": "Harmony360 Pattern Play"})
        if load_har360(carrier) != receipt:
            raise ValueError("Native receipt round trip failed")
        files["creation-receipt.har360"] = carrier.read_bytes()
    files["README.txt"] = ("Your Pattern Play pack\n\nThree PNGs for personal use: phone, desktop and square.\n"
                           "The .har360 file records the design and content hashes.\n"
                           "It is a creation receipt, not an automatic payment verification.\n").encode()
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, raw in files.items():
            archive.writestr(name, raw)
    return {"output": str(destination), "order_reference": order_reference, "files": list(files)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--order", required=True, help="Customer's copied Pattern Play reference")
    parser.add_argument("--payment-reference", required=True, help="Transaction verified by the seller; not a credential")
    parser.add_argument("--output", type=Path, default=Path("orders/wallpaper-pack.zip"))
    args = parser.parse_args()
    print(json.dumps(fulfill(args.order, args.payment_reference, args.output)))


if __name__ == "__main__":
    main()

