# Harmony360 Pattern Play

A first creative product built with the existing Harmony360 Python numerical
core: create geometric wallpaper art, save a free preview and order a matching
phone, desktop and square pack for an experimental **$5 USD** price.

The renderer and interactive behavior are written in Python. The browser runs
them with PyScript/Pyodide; HTML and CSS supply the page layout. Photos supply
five palette colors and stay on the customer's device. The stored recipe and
order reference contain colors and rendering parameters, not the photo itself.
There are no model calls, health claims, or resonance-based measurements.

## Run and test

```bash
python -m pip install -e .
python build_site.py
python -m http.server 8000 --directory dist
python -m unittest discover -s tests -v
```

Open http://localhost:8000. The first visit downloads the pinned Python browser
runtime and NumPy/Pillow. Later visits can reuse the browser cache. Internet
access to the PyScript/Pyodide CDNs is required for a first launch.

## How sales work in version 0.1

The customer adds their delivery email, copies the order note, then chooses
PayPal or Cash App. Payment links go to **PayPal.Me/RdnTmsn** and **$rctumsun**.
The PayPal link requests 5 USD. The Cash App profile link requires the buyer to
enter $5 themselves. In either provider the buyer must paste the copied note.
The current app does not prefill provider notes or verify payment.

There is no order database or outgoing email service in this version. Your
provider's received payment and its note are the order record. If a customer
omits the note, use the provider's supported contact/refund process to resolve
the order. A saved design JSON is not proof of purchase.

Before accepting orders, confirm that both handles identify your intended
accounts, use PayPal's purchase/Goods and Services flow, and confirm that your
Cash App account supports commercial payments. A cashtag alone does not prove
Business eligibility. No accounts were modified or test payments sent.

Official references:

- [PayPal.Me and requesting an amount](https://www.paypal.com/us/cshelp/article/paypalme-frequently-asked-questions-help432)
- [Cash App Business terms](https://cash.app/us/en/legal/cash-payment-terms)

## Fulfill an order

First verify receipt of the real payment in your own PayPal or Cash App account.
Copy the `P1-...` reference from the note. On a Python machine run:

```bash
python -m pattern_play.fulfill \
  --order 'P1-REFERENCE-FROM-THE-CUSTOMER' \
  --payment-reference 'YOUR-LOCALLY-VERIFIED-TRANSACTION-REFERENCE' \
  --output orders/customer-pack.zip
```

The result contains three PNGs: 1440×2560 phone, 2560×1440 desktop and 2048×2048
square, plus a native `.har360` creation receipt. Email the ZIP to the delivery
address in the payment note. The receipt records a seller assertion of manual
verification and hashes the supplied transaction reference; it does not contact
or authenticate a payment provider.

The accompanying GitHub seller workflow offers the same rendering from the
Actions interface once its workflow is on the default branch. Confirm payment
there and enter only the design reference. Customer emails, photos and actual
transaction identifiers do not belong in public workflow inputs or logs.
The artifact is a ZIP you deliver yourself; a public repository must not be
treated as a private customer vault.

## Original core

The files in `pattern_play/_numeric` retain the existing repository's `core.py`,
`constants.py` and `serialization.py` bytes. `CORE_PROVENANCE.json` binds their
Git blob IDs and SHA-256 hashes; tests verify both. The small package initializer
exposes only the numerical class so the browser does not need unrelated crypto
or database packages.

Every render calls the original `R_369`, `fractal_harmonic_wavefield`,
`fractal_harmonic_projection` and `phi_pi_modulation` methods. Original core
formulas are not changed or replaced by a JavaScript implementation.

## Revenue experiment

Start with the one-time $5 pack; avoid subscriptions until there is repeat
demand. Share a free preview and a short screen recording showing the photo
palette and three styles. Track real visits, orders, fees and fulfillment time
outside the app to decide whether the offer is useful. No traffic, conversions
or earnings have been established by this build.
