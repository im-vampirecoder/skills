"""
List subscription offer codes, fetch one-time code values, draw a QR for a
custom code, and switch offers off on demand.

Deactivating stops new redemptions immediately; customers who already
redeemed keep their offer period. Treat deactivation as permanent (the ASC
UI offers no reactivation); to restart a campaign create a new custom code.

Usage:
    python manage_offer_codes.py --list [--app-id ID | --bundle-id BID]
    python manage_offer_codes.py --codes BATCH_ID [--out codes.csv]
    python manage_offer_codes.py --qr CUSTOM_CODE --out promo.png
    python manage_offer_codes.py --deactivate-custom-code CUSTOM_CODE_ID [--dry-run]
    python manage_offer_codes.py --deactivate-codes BATCH_ID [--dry-run]
    python manage_offer_codes.py --deactivate-offer OFFER_CODE_ID [--dry-run]
"""
import argparse
import json
import sys

from offer_codes_common import (
    BASE, add_common_args, check, custom_codes_for_offer, get_session, list_subscriptions,
    offer_codes_for_subscription, one_time_batches_for_offer, redeem_url, resolve_app_id, write_qr_png,
)


def list_all(session, app_id):
    found = False
    for sub in list_subscriptions(session, app_id):
        offers = offer_codes_for_subscription(session, sub["id"])
        if not offers:
            continue
        found = True
        print(f"\n{sub['attributes'].get('productId')} (subscription {sub['id']})")
        for offer in offers:
            a = offer["attributes"]
            print(f"  offer {offer['id']}  '{a.get('name')}'  active={a.get('active')}  "
                  f"{a.get('offerMode')} {a.get('duration')}  eligibility={a.get('customerEligibilities')}  "
                  f"{a.get('offerEligibility')}  codes: prod={a.get('productionCodeCount')} "
                  f"sandbox={a.get('sandboxCodeCount')}")
            for code in custom_codes_for_offer(session, offer["id"]):
                c = code["attributes"]
                print(f"    custom {code['id']}  {c.get('customCode')}  active={c.get('active')}  "
                      f"limit={c.get('numberOfCodes')}  expires={c.get('expirationDate')}")
                print(f"      {redeem_url(app_id, c.get('customCode'))}")
            for batch in one_time_batches_for_offer(session, offer["id"]):
                b = batch["attributes"]
                print(f"    one-time {batch['id']}  {b.get('environment')}  n={b.get('numberOfCodes')}  "
                      f"active={b.get('active')}  expires={b.get('expirationDate')}")
    if not found:
        print(f"No offer codes on any subscription of app {app_id}")


def deactivate(session, resource_type, resource_id, dry_run):
    payload = {"data": {"type": resource_type, "id": resource_id, "attributes": {"active": False}}}
    if dry_run:
        print(f"[dry-run] PATCH /v1/{resource_type}/{resource_id}")
        print(json.dumps(payload, indent=2))
        return
    check(session.patch(f"{BASE}/{resource_type}/{resource_id}", json=payload), f"Deactivate {resource_type}")
    print(f"Deactivated {resource_type} {resource_id}")


def fetch_codes(session, batch_id, out_path):
    """One-time-use codes are generated async; the values endpoint returns CSV text."""
    resp = session.get(f"{BASE}/subscriptionOfferCodeOneTimeUseCodes/{batch_id}/values")
    if resp.status_code >= 400:
        sys.exit(f"Codes not ready or request failed (generation is async, retry in a minute): "
                 f"HTTP {resp.status_code}\n{resp.text}")
    if out_path:
        with open(out_path, "w") as f:
            f.write(resp.text)
        print(f"Wrote {len(resp.text.splitlines())} lines to {out_path}")
    else:
        print(resp.text)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_common_args(p)
    action = p.add_mutually_exclusive_group(required=True)
    action.add_argument("--list", action="store_true")
    action.add_argument("--codes", metavar="BATCH_ID", help="print/save one-time code values")
    action.add_argument("--qr", metavar="CUSTOM_CODE", help="write the redeem QR for a custom code")
    action.add_argument("--deactivate-custom-code", metavar="CUSTOM_CODE_ID")
    action.add_argument("--deactivate-codes", metavar="BATCH_ID")
    action.add_argument("--deactivate-offer", metavar="OFFER_CODE_ID")
    p.add_argument("--out", default=None, help="output file for --codes (CSV) or --qr (PNG)")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    session, cfg = get_session(args.config)
    if args.list:
        list_all(session, resolve_app_id(session, cfg, args))
    elif args.codes:
        fetch_codes(session, args.codes, args.out)
    elif args.qr:
        url = redeem_url(resolve_app_id(session, cfg, args), args.qr)
        print(url)
        if not args.out:
            sys.exit("--qr needs --out promo.png")
        if write_qr_png(url, args.out):
            print(f"QR written: {args.out}")
    elif args.deactivate_custom_code:
        deactivate(session, "subscriptionOfferCodeCustomCodes", args.deactivate_custom_code, args.dry_run)
    elif args.deactivate_codes:
        deactivate(session, "subscriptionOfferCodeOneTimeUseCodes", args.deactivate_codes, args.dry_run)
    else:
        deactivate(session, "subscriptionOfferCodes", args.deactivate_offer, args.dry_run)


if __name__ == "__main__":
    main()
