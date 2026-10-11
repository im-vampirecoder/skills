"""
Shared helpers for the subscription offer code scripts
(create_offer_code.py, toggle_offer_code.py).
"""
import json
import sys

from export_subscriptions import BASE, get_all

REDEEM_URL = "https://apps.apple.com/redeem?ctx=offercodes&id={app_id}&code={code}"


def redeem_url(app_id, code):
    return REDEEM_URL.format(app_id=app_id, code=code)


def check(resp, what):
    """Raise with Apple's error body (much more useful than the bare HTTP status)."""
    if resp.status_code >= 400:
        print(f"{what} failed: HTTP {resp.status_code}\n{resp.text}", file=sys.stderr)
        resp.raise_for_status()
    return resp.json() if resp.content else {}


def find_subscription(session, app_id, product_id):
    """Resolve a subscription resource id from its product id (e.g. ...monthly)."""
    for group in get_all(session, f"{BASE}/apps/{app_id}/subscriptionGroups"):
        for sub in get_all(session, f"{BASE}/subscriptionGroups/{group['id']}/subscriptions"):
            if sub["attributes"].get("productId") == product_id:
                return sub
    raise LookupError(f"Subscription with productId {product_id} not found on app {app_id}")


def list_subscriptions(session, app_id):
    subs = []
    for group in get_all(session, f"{BASE}/apps/{app_id}/subscriptionGroups"):
        subs.extend(get_all(session, f"{BASE}/subscriptionGroups/{group['id']}/subscriptions"))
    return subs


def available_territories(session, subscription_id):
    """Territory ids the subscription is sold in. Offer code prices must be
    supplied per territory; there is no 'all territories' shortcut."""
    resp = session.get(f"{BASE}/subscriptions/{subscription_id}/subscriptionAvailability")
    availability = check(resp, "GET subscriptionAvailability").get("data")
    if not availability:
        raise LookupError(f"Subscription {subscription_id} has no availability record")
    territories = get_all(
        session,
        f"{BASE}/subscriptionAvailabilities/{availability['id']}/availableTerritories",
        params={"limit": 200},
    )
    return sorted(t["id"] for t in territories)


def offer_codes_for_subscription(session, subscription_id):
    return get_all(session, f"{BASE}/subscriptions/{subscription_id}/offerCodes")


def custom_codes_for_offer(session, offer_code_id):
    return get_all(session, f"{BASE}/subscriptionOfferCodes/{offer_code_id}/customCodes")


def write_qr_png(url, out_path):
    """Write a QR PNG if the optional `qrcode` package is installed."""
    try:
        import qrcode
    except ImportError:
        print(
            "  (qrcode package not installed — skip PNG. Install with: "
            "$HOME/.claude/skills/.venv/bin/pip install 'qrcode[pil]')",
            file=sys.stderr,
        )
        return False
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=12, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    qr.make_image().save(out_path)
    return True


def dump(payload):
    print(json.dumps(payload, indent=2))
