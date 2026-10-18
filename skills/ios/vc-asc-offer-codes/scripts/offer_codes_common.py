"""
Shared helpers for the vc-asc-offer-codes scripts.

Authentication is NOT duplicated here: it reuses asc_auth.py and the
pagination helper from the sibling vc-asc-app-manager skill, so there is a
single place that touches the .p8 key.
"""
import os
import sys

_SIBLING = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "vc-asc-app-manager", "scripts"
)
if not os.path.isdir(_SIBLING):
    sys.exit(f"vc-asc-app-manager skill not found at {_SIBLING} (needed for asc_auth.py)")
sys.path.insert(0, _SIBLING)

from asc_auth import get_session  # noqa: E402,F401  (re-exported for the scripts)
from export_subscriptions import get_all  # noqa: E402

BASE = "https://api.appstoreconnect.apple.com/v1"
REDEEM_URL = "https://apps.apple.com/redeem?ctx=offercodes&id={app_id}&code={code}"

DURATIONS = ["THREE_DAYS", "ONE_WEEK", "TWO_WEEKS", "ONE_MONTH", "TWO_MONTHS",
             "THREE_MONTHS", "SIX_MONTHS", "ONE_YEAR"]
ELIGIBILITIES = {"NEW", "EXISTING", "EXPIRED"}


def add_common_args(parser):
    """--config plus one of --app-id / --bundle-id (falls back to config app_id / new_app_id)."""
    parser.add_argument("--config", default=None, help="Path to asc_config.json")
    parser.add_argument("--app-id", default=None, help="ASC app id (numeric)")
    parser.add_argument("--bundle-id", default=None, help="Resolve the app by bundle id instead")


def resolve_app_id(session, cfg, args):
    if args.app_id:
        return args.app_id
    if args.bundle_id:
        resp = session.get(f"{BASE}/apps", params={"filter[bundleId]": args.bundle_id})
        matches = [a for a in check(resp, "GET apps").get("data", [])
                   if a["attributes"]["bundleId"] == args.bundle_id]
        if not matches:
            sys.exit(f"No app visible to this API key has bundle id {args.bundle_id}")
        return matches[0]["id"]
    app_id = cfg.get("app_id") or cfg.get("new_app_id")
    if app_id:
        return app_id
    sys.exit("Pass --app-id or --bundle-id (config has no app_id / new_app_id default)")


def check(resp, what):
    """Raise with Apple's error body (much more useful than the bare HTTP status)."""
    if resp.status_code >= 400:
        print(f"{what} failed: HTTP {resp.status_code}\n{resp.text}", file=sys.stderr)
        resp.raise_for_status()
    return resp.json() if resp.content else {}


def redeem_url(app_id, code):
    return REDEEM_URL.format(app_id=app_id, code=code)


def list_subscriptions(session, app_id):
    subs = []
    for group in get_all(session, f"{BASE}/apps/{app_id}/subscriptionGroups"):
        subs.extend(get_all(session, f"{BASE}/subscriptionGroups/{group['id']}/subscriptions"))
    return subs


def find_subscription(session, app_id, product_id):
    """Resolve a subscription resource from its product id (e.g. com.example.monthly)."""
    subs = list_subscriptions(session, app_id)
    for sub in subs:
        if sub["attributes"].get("productId") == product_id:
            return sub
    known = ", ".join(s["attributes"].get("productId", "?") for s in subs) or "none"
    sys.exit(f"Subscription {product_id} not found on app {app_id}. Known: {known}")


def available_territories(session, subscription_id):
    """Territory ids the subscription is sold in. Offer code prices must be
    supplied per territory; there is no 'all territories' shortcut."""
    resp = session.get(f"{BASE}/subscriptions/{subscription_id}/subscriptionAvailability")
    availability = check(resp, "GET subscriptionAvailability").get("data")
    if not availability:
        sys.exit(f"Subscription {subscription_id} has no availability record (set territories in ASC first)")
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


def one_time_batches_for_offer(session, offer_code_id):
    return get_all(session, f"{BASE}/subscriptionOfferCodes/{offer_code_id}/oneTimeUseCodes")


def write_qr_png(url, out_path):
    """Write a QR PNG if the optional `qrcode` package is installed."""
    try:
        import qrcode
    except ImportError:
        print("  (qrcode package not installed, skipping PNG. Install with: "
              "$HOME/.claude/skills/.venv/bin/pip install 'qrcode[pil]')", file=sys.stderr)
        return False
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=12, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    qr.make_image().save(out_path)
    return True
