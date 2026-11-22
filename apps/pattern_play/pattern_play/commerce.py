"""Payment links and manual order notes; links never prove that payment occurred."""
from urllib.parse import urlsplit


def payment_url(value: str | None, provider: str, amount: int = 5) -> str | None:
    if not value:
        return None
    parsed = urlsplit(value)
    hosts = {"paypal": {"paypal.me", "www.paypal.me", "paypal.com", "www.paypal.com"},
             "cashapp": {"cash.app"}}
    if provider not in hosts or parsed.scheme != "https" or parsed.hostname not in hosts[provider] or parsed.username or parsed.password or parsed.port:
        raise ValueError("Unexpected payment destination")
    if not parsed.path.strip("/") or parsed.fragment:
        raise ValueError("Incomplete payment destination")
    if parsed.hostname in {"paypal.me", "www.paypal.me"}:
        handle = parsed.path.strip("/").split("/")[0]
        if not handle.isalnum() or len(handle) > 20:
            raise ValueError("Invalid PayPal.Me handle")
        return "https://paypal.me/" + handle + "/" + str(amount) + "USD"
    return value


def order_note(reference: str, email: str) -> str:
    email = email.strip()
    if not email or len(email) > 254 or "@" not in email or any(c.isspace() for c in email) or "\n" in reference:
        raise ValueError("Enter an email address for delivery")
    return f"Pattern Play $5 | {reference} | Deliver to {email}"

