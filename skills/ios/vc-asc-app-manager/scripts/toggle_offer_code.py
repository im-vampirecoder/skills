"""
List subscription offer codes and switch them off on demand.

Deactivating a custom code stops new redemptions immediately; customers who
already redeemed keep their offer period. Apple treats deactivation as
permanent in the ASC UI, so to restart a campaign create a new custom code.

Usage:
    python toggle_offer_code.py --list [--app-id APPID]
    python toggle_offer_code.py --deactivate-custom-code CUSTOM_CODE_ID [--dry-run]
    python toggle_offer_code.py --deactivate-offer OFFER_CODE_ID [--dry-run]
    python toggle_offer_code.py --sandbox-values ONE_TIME_USE_BATCH_ID
"""
import argparse
import sys

from asc_auth import get_session
from export_subscriptions import BASE, get_all
from offer_code_helpers import (
    check, custom_codes_for_offer, dump, list_subscriptions, offer_codes_for_subscription, redeem_url,
)


def list_all(session, app_id):
    for sub in list_subscriptions(session, app_id):
        offers = offer_codes_for_subscription(session, sub["id"])
        if not offers:
            continue
        print(f"\n{sub['attributes'].get('productId')} (subscription {sub['id']})")
        for offer in offers:
            a = offer["attributes"]
            print(f"  offer {offer['id']}  '{a.get('name')}'  active={a.get('active')}  "
                  f"{a.get('offerMode')} {a.get('duration')}  eligibility={a.get('customerEligibilities')}  "
                  f"{a.get('offerEligibility')}")
            for code in custom_codes_for_offer(session, offer["id"]):
                c = code["attributes"]
                print(f"    custom {code['id']}  {c.get('customCode')}  active={c.get('active')}  "
                      f"limit={c.get('numberOfCodes')}  expires={c.get('expirationDate')}")
                print(f"      {redeem_url(app_id, c.get('customCode'))}")
            for batch in get_all(session, f"{BASE}/subscriptionOfferCodes/{offer['id']}/oneTimeUseCodes"):
                b = batch["attributes"]
                print(f"    one-time batch {batch['id']}  {b.get('environment')}  n={b.get('numberOfCodes')}  "
                      f"active={b.get('active')}  expires={b.get('expirationDate')}")


def deactivate(session, resource_type, resource_id, dry_run):
    payload = {"data": {"type": resource_type, "id": resource_id, "attributes": {"active": False}}}
    if dry_run:
        print(f"[dry-run] PATCH /v1/{resource_type}/{resource_id}")
        dump(payload)
        return
    check(session.patch(f"{BASE}/{resource_type}/{resource_id}", json=payload), f"Deactivate {resource_type}")
    print(f"Deactivated {resource_type} {resource_id}")


def sandbox_values(session, batch_id):
    """One-time-use codes are generated async; the values endpoint returns CSV text."""
    resp = session.get(f"{BASE}/subscriptionOfferCodeOneTimeUseCodes/{batch_id}/values")
    if resp.status_code >= 400:
        sys.exit(f"Not ready or failed: HTTP {resp.status_code}\n{resp.text}")
    print(resp.text)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config", default=None)
    p.add_argument("--app-id", default=None, help="defaults to new_app_id from config")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true")
    group.add_argument("--deactivate-custom-code", metavar="CUSTOM_CODE_ID")
    group.add_argument("--deactivate-offer", metavar="OFFER_CODE_ID")
    group.add_argument("--sandbox-values", metavar="BATCH_ID")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    session, cfg = get_session(args.config)
    if args.list:
        app_id = args.app_id or cfg.get("new_app_id")
        if not app_id:
            sys.exit("--app-id required (or set new_app_id in config)")
        list_all(session, app_id)
    elif args.deactivate_custom_code:
        deactivate(session, "subscriptionOfferCodeCustomCodes", args.deactivate_custom_code, args.dry_run)
    elif args.deactivate_offer:
        deactivate(session, "subscriptionOfferCodes", args.deactivate_offer, args.dry_run)
    else:
        sandbox_values(session, args.sandbox_values)


if __name__ == "__main__":
    main()
