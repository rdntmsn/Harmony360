# Pattern Play 0.1 — validation

Validated November 21, 2026 on Python 3.12 and desktop Chrome.

- **11 Python tests pass.** They cover deterministic rendering, changes in seed
  and style, execution of the four original core methods, palette extraction,
  image limits, invalid order references, provider URL validation and fulfillment.
- Three retained core source files match both their recorded Git blob IDs and
  SHA-256 digests. Only a minimal package initializer was added.
- A complete seller export was generated in a temporary directory. The phone,
  desktop and square PNG dimensions and hashes were verified against a receipt
  written and loaded through the existing `.har360` codec.
- Browser checks exercised style and palette selection, energy, randomization,
  a local WebP upload, order-note copying and both payment destinations.
- A real browser download completed. The downloaded file was opened with Pillow
  and confirmed to be a **640 × 640 PNG**. Browser downloads use Blob links.
- The browser UI source compiles as Python with top-level async support. The
  static build includes the exact numerical Python files used by the renderer.

The photo-upload test used generated sample art, not a customer's private photo.
Responsive CSS is included; a physical Android or iOS device was not tested.
Provider links were inspected without sending money. No recipient-ownership or
Business-account eligibility verification was performed. Payment confirmation
and email delivery are manual, and no revenue or conversion result is claimed.
