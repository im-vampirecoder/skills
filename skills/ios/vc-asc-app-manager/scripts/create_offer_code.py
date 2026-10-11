"""
Create a subscription offer code (free trial) plus a shared custom code,
print its App Store redemption URL, and optionally write a QR PNG.

Optionally also generates a batch of SANDBOX one-time-use codes for the
same offer, so the redemption flow can be tested on TestFlight before the
production custom code is handed out.

Idempotent on --name: if an offer code with the same name already exists
on the subscription it is reused instead of creating a duplicate.

Usage:
    python create_offer_code.py --product-id com.example.monthly \
        --name "Sam Promo 3M Free" --custom-code BNA3FREE \
        [--app-id APPID] [--duration THREE_MONTHS] [--eligibility NEW] \
        [--offer-eligibility REPLACE_INTRO_OFFERS] [--limit 10000] \
        [--expires YYYY-MM-DD] [--sandbox-test-codes 5] \
        [--qr-out promo.png] [--dry-run]
"""
import argparse
import datetime
import re
import sys

from asc_auth import get_session
from export_subscriptions import BASE
from offer_code_helpers import (
    available_territories, check, custom_codes_for_offer, dump, find_subscription,
    offer_codes_for_subscription, redeem_url, write_qr_png,
)

DURATIONS = ["THREE_DAYS", "ONE_WEEK", "TWO_WEEKS", "ONE_MONTH", "TWO_MONTHS",
             "THREE_MONTHS", "SIX_MONTHS", "ONE_YEAR"]


def build_offer_payload(args, subscription_id, territories):
    # FREE_TRIAL prices carry only a territory — no price point, since the
    # customer pays nothing during the offer period.
    included = [
        {
            "type": "subscriptionOfferCodePrices",
            "id": f"${{price-{t}}}",
            "relationships": {"territory": {"data": {"type": "territories", "id": t}}},
        }
        for t in territories
    ]
    return {
        "data": {
            "type": "subscriptionOfferCodes",
            "attributes": {
                "name": args.name,
                "customerEligibilities": args.eligibility.split(","),
                "offerEligibility": args.offer_eligibility,
                "offerMode": "FREE_TRIAL",
                "duration": args.duration,
                "numberOfPeriods": 1,
            },
            "relationships": {
                "subscription": {"data": {"type": "subscriptions", "id": subscription_id}},
                "prices": {"data": [{"type": p["type"], "id": p["id"]} for p in included]},
            },
        },
        "included": included,
    }


def build_custom_code_payload(args, offer_code_id):
    attributes = {"customCode": args.custom_code, "numberOfCodes": args.limit}
    if args.expires:
        attributes["expirationDate"] = args.expires
    return {
        "data": {
            "type": "subscriptionOfferCodeCustomCodes",
            "attributes": attributes,
            "relationships": {"offerCode": {"data": {"type": "subscriptionOfferCodes", "id": offer_code_id}}},
        }
    }


def build_sandbox_codes_payload(count, offer_code_id):
    expires = (datetime.date.today() + datetime.timedelta(days=30)).isoformat()
    return {
        "data": {
            "type": "subscriptionOfferCodeOneTimeUseCodes",
            "attributes": {"numberOfCodes": count, "expirationDate": expires, "environment": "SANDBOX"},
            "relationships": {"offerCode": {"data": {"type": "subscriptionOfferCodes", "id": offer_code_id}}},
        }
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config", default=None)
    p.add_argument("--app-id", default=None, help="defaults to new_app_id from config")
    p.add_argument("--product-id", required=True)
    p.add_argument("--name", required=True, help="offer reference name (internal, shown in ASC)")
    p.add_argument("--custom-code", required=True)
    p.add_argument("--duration", default="THREE_MONTHS", choices=DURATIONS)
    p.add_argument("--eligibility", default="NEW", help="comma list of NEW,EXISTING,EXPIRED")
    p.add_argument("--offer-eligibility", default="REPLACE_INTRO_OFFERS",
                   choices=["REPLACE_INTRO_OFFERS", "STACK_WITH_INTRO_OFFERS"])
    p.add_argument("--limit", type=int, default=10000, help="max redemptions of the custom code")
    p.add_argument("--expires", default=None, help="YYYY-MM-DD; omit for no expiry")
    p.add_argument("--sandbox-test-codes", type=int, default=0, help="N sandbox one-time codes for TestFlight")
    p.add_argument("--qr-out", default=None)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    if not re.fullmatch(r"[A-Za-z0-9]+", args.custom_code):
        sys.exit("--custom-code must be letters and digits only")

    session, cfg = get_session(args.config)
    app_id = args.app_id or cfg.get("new_app_id")
    if not app_id:
        sys.exit("--app-id required (or set new_app_id in config)")

    sub = find_subscription(session, app_id, args.product_id)
    territories = available_territories(session, sub["id"])
    print(f"Subscription {sub['id']} ({args.product_id}), {len(territories)} territories")

    existing = [o for o in offer_codes_for_subscription(session, sub["id"])
                if o["attributes"].get("name") == args.name]
    offer_code_id = existing[0]["id"] if existing else None

    if offer_code_id:
        print(f"Reusing existing offer code {offer_code_id} named '{args.name}'")
    else:
        payload = build_offer_payload(args, sub["id"], territories)
        if args.dry_run:
            print("\n[dry-run] POST /v1/subscriptionOfferCodes")
            shown = dict(payload, included=payload["included"][:2] + [f"... {len(territories)} total"])
            dump(shown)
            offer_code_id = "<OFFER_CODE_ID>"
        else:
            body = check(session.post(f"{BASE}/subscriptionOfferCodes", json=payload), "Create offer code")
            offer_code_id = body["data"]["id"]
            print(f"Created offer code {offer_code_id}")

    have_custom = existing and any(
        c["attributes"].get("customCode", "").upper() == args.custom_code.upper()
        for c in custom_codes_for_offer(session, offer_code_id)
    )
    if have_custom:
        print(f"Custom code {args.custom_code} already exists on this offer")
    else:
        payload = build_custom_code_payload(args, offer_code_id)
        if args.dry_run:
            print("\n[dry-run] POST /v1/subscriptionOfferCodeCustomCodes")
            dump(payload)
        else:
            body = check(session.post(f"{BASE}/subscriptionOfferCodeCustomCodes", json=payload),
                         "Create custom code")
            print(f"Created custom code {args.custom_code} (id {body['data']['id']})")

    if args.sandbox_test_codes:
        payload = build_sandbox_codes_payload(args.sandbox_test_codes, offer_code_id)
        if args.dry_run:
            print("\n[dry-run] POST /v1/subscriptionOfferCodeOneTimeUseCodes")
            dump(payload)
        else:
            body = check(session.post(f"{BASE}/subscriptionOfferCodeOneTimeUseCodes", json=payload),
                         "Create sandbox codes")
            batch_id = body["data"]["id"]
            print(f"Sandbox code batch {batch_id} requested. Codes are generated async; fetch with:\n"
                  f"  python toggle_offer_code.py --sandbox-values {batch_id}")

    url = redeem_url(app_id, args.custom_code)
    print(f"\nRedeem URL: {url}")
    if args.qr_out and not args.dry_run and write_qr_png(url, args.qr_out):
        print(f"QR written: {args.qr_out}")
    if not args.dry_run:
        print("Note: new codes can take up to ~1 hour before they are redeemable.")


if __name__ == "__main__":
    main()
