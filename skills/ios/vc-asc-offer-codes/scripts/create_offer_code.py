"""
Create a free-trial subscription offer code, plus any of: a shared custom code
(one code, many redemptions: QR / promo link), a batch of production
one-time-use codes, and a batch of SANDBOX one-time-use codes for TestFlight.

Idempotent on --name: an offer with the same name on the subscription is
reused (offers can't be edited, so a name match with different terms stops
with an error instead of silently reusing the wrong offer). An existing
custom code with the same value is not created twice.

Usage:
    python create_offer_code.py --product-id com.example.monthly \
        --name "Spring promo 3M free" [--app-id ID | --bundle-id BID] \
        [--duration THREE_MONTHS] [--eligibility NEW[,EXPIRED,EXISTING]] \
        [--offer-eligibility REPLACE_INTRO_OFFERS] \
        [--custom-code SPRING3M --limit 10000 --expires YYYY-MM-DD] \
        [--one-time-codes N --one-time-expires YYYY-MM-DD] \
        [--sandbox-test-codes N] [--qr-out promo.png] [--dry-run]
"""
import argparse
import datetime
import json
import re
import sys

from offer_codes_common import (
    BASE, DURATIONS, ELIGIBILITIES, add_common_args, available_territories, check,
    custom_codes_for_offer, find_subscription, get_session, offer_codes_for_subscription,
    redeem_url, resolve_app_id, write_qr_png,
)


def days_from_today(days):
    return (datetime.date.today() + datetime.timedelta(days=days)).isoformat()


def offer_terms(args):
    return {
        "customerEligibilities": sorted(args.eligibility),
        "offerEligibility": args.offer_eligibility,
        "offerMode": "FREE_TRIAL",
        "duration": args.duration,
        "numberOfPeriods": 1,
    }


def build_offer_payload(args, subscription_id, territories):
    # FREE_TRIAL prices carry only a territory: no price point, the customer pays nothing.
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
            "attributes": {"name": args.name, **offer_terms(args)},
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


def build_one_time_payload(count, expires, environment, offer_code_id):
    return {
        "data": {
            "type": "subscriptionOfferCodeOneTimeUseCodes",
            "attributes": {"numberOfCodes": count, "expirationDate": expires, "environment": environment},
            "relationships": {"offerCode": {"data": {"type": "subscriptionOfferCodes", "id": offer_code_id}}},
        }
    }


def send(session, path, payload, what, dry_run, preview=None):
    """POST unless --dry-run; on dry-run print the payload (or a trimmed preview)."""
    if dry_run:
        print(f"\n[dry-run] POST /v1/{path}")
        print(json.dumps(preview or payload, indent=2))
        return None
    body = check(session.post(f"{BASE}/{path}", json=payload), what)
    return body["data"]["id"]


def resolve_offer(session, args, sub, territories):
    """Reuse an offer with the same name, or create one. Returns its id."""
    existing = [o for o in offer_codes_for_subscription(session, sub["id"])
                if o["attributes"].get("name") == args.name]
    if existing:
        offer = existing[0]
        a = offer["attributes"]
        live = {k: (sorted(a.get(k) or []) if k == "customerEligibilities" else a.get(k)) for k in offer_terms(args)}
        if live != offer_terms(args):
            sys.exit(f"Offer '{args.name}' ({offer['id']}) exists with different terms: {live}. "
                     f"Offers can't be edited; use a new --name.")
        print(f"Reusing offer {offer['id']} '{args.name}' (active={a.get('active')})")
        return offer["id"], True

    payload = build_offer_payload(args, sub["id"], territories)
    preview = dict(payload, included=payload["included"][:2] + [f"... {len(territories)} territories"])
    offer_id = send(session, "subscriptionOfferCodes", payload, "Create offer code", args.dry_run, preview)
    if offer_id:
        print(f"Created offer {offer_id} '{args.name}'")
    return offer_id or "<OFFER_CODE_ID>", False


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_common_args(p)
    p.add_argument("--product-id", required=True, help="subscription product id the offer applies to")
    p.add_argument("--name", required=True, help="offer reference name (internal, shown in ASC)")
    p.add_argument("--duration", default="THREE_MONTHS", choices=DURATIONS)
    p.add_argument("--eligibility", default="NEW", help="comma list of NEW,EXISTING,EXPIRED")
    p.add_argument("--offer-eligibility", default="REPLACE_INTRO_OFFERS",
                   choices=["REPLACE_INTRO_OFFERS", "STACK_WITH_INTRO_OFFERS"])
    p.add_argument("--custom-code", default=None, help="shared code, letters and digits only")
    p.add_argument("--limit", type=int, default=10000, help="max redemptions of the custom code (API requires one)")
    p.add_argument("--expires", default=None, help="custom code expiry YYYY-MM-DD; omit for none")
    p.add_argument("--one-time-codes", type=int, default=0, help="N production one-time-use codes")
    p.add_argument("--one-time-expires", default=None, help="YYYY-MM-DD (required by Apple; default +90 days)")
    p.add_argument("--sandbox-test-codes", type=int, default=0, help="N SANDBOX one-time codes for TestFlight")
    p.add_argument("--qr-out", default=None, help="write the custom code's redeem URL as a QR PNG")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    args.eligibility = [e.strip().upper() for e in args.eligibility.split(",") if e.strip()]
    if not args.eligibility or not set(args.eligibility) <= ELIGIBILITIES:
        sys.exit(f"--eligibility must be a comma list of {sorted(ELIGIBILITIES)}")
    if args.custom_code and not re.fullmatch(r"[A-Za-z0-9]+", args.custom_code):
        sys.exit("--custom-code must be letters and digits only")
    if not (args.custom_code or args.one_time_codes or args.sandbox_test_codes):
        sys.exit("Nothing to create: pass --custom-code, --one-time-codes and/or --sandbox-test-codes")

    session, cfg = get_session(args.config)
    app_id = resolve_app_id(session, cfg, args)
    sub = find_subscription(session, app_id, args.product_id)
    territories = available_territories(session, sub["id"])
    print(f"App {app_id} · subscription {sub['id']} ({args.product_id}) · "
          f"{len(territories)} territories: {' '.join(territories)}")

    offer_id, reused = resolve_offer(session, args, sub, territories)

    if args.custom_code:
        exists = reused and any(
            c["attributes"].get("customCode", "").upper() == args.custom_code.upper()
            for c in custom_codes_for_offer(session, offer_id)
        )
        if exists:
            print(f"Custom code {args.custom_code} already exists on this offer")
        else:
            code_id = send(session, "subscriptionOfferCodeCustomCodes",
                           build_custom_code_payload(args, offer_id), "Create custom code", args.dry_run)
            if code_id:
                print(f"Created custom code {args.custom_code} (id {code_id})")

    batches = []
    if args.one_time_codes:
        batches.append((args.one_time_codes, args.one_time_expires or days_from_today(90), "PRODUCTION"))
    if args.sandbox_test_codes:
        batches.append((args.sandbox_test_codes, days_from_today(30), "SANDBOX"))
    for count, expires, env in batches:
        batch_id = send(session, "subscriptionOfferCodeOneTimeUseCodes",
                        build_one_time_payload(count, expires, env, offer_id), f"Create {env} codes", args.dry_run)
        if batch_id:
            print(f"{env} one-time batch {batch_id} requested ({count} codes, expires {expires}). "
                  f"Generated async; fetch with:\n  python manage_offer_codes.py --codes {batch_id} --out codes.csv")

    if args.custom_code:
        url = redeem_url(app_id, args.custom_code)
        print(f"\nRedeem URL: {url}")
        if args.qr_out and not args.dry_run and write_qr_png(url, args.qr_out):
            print(f"QR written: {args.qr_out}")
    if not args.dry_run:
        print("New codes can take up to ~1 hour before they are redeemable.")


if __name__ == "__main__":
    main()
