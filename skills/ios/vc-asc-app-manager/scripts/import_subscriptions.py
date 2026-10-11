"""
Recreate subscription groups, subscriptions, localizations, and prices on a
target app in App Store Connect, from a JSON file produced by
export_subscriptions.py.

Usage:
    python import_subscriptions.py --in subscriptions_export.json [--config PATH] [--dry-run]

Reads new_app_id from the config file unless --app-id is passed explicitly.

IMPORTANT: product IDs must be unique per app but the SAME string can be
reused across app records (old and new), which keeps client StoreKit code
unchanged. This script keeps product IDs exactly as exported by default.
Pass --suffix to append a suffix instead, e.g. if you need to avoid a
collision (product IDs are sometimes globally reserved for a short window
after deletion).
"""
import argparse
import json
import sys

from asc_auth import get_session
from resolve_prices import apply_prices

BASE = "https://api.appstoreconnect.apple.com/v1"


def post(session, url, payload, dry_run):
    if dry_run:
        print(f"[dry-run] POST {url}\n{json.dumps(payload, indent=2)}\n")
        return {"data": {"id": "DRY_RUN_ID"}}
    resp = session.post(url, json=payload)
    if not resp.ok:
        print(f"FAILED POST {url}: {resp.status_code} {resp.text}", file=sys.stderr)
        resp.raise_for_status()
    return resp.json()


def import_subscriptions(session, app_id, data, dry_run, suffix="", apply_prices_flag=False):
    created = {"subscriptionGroups": []}

    for group in data["subscriptionGroups"]:
        group_payload = {
            "data": {
                "type": "subscriptionGroups",
                "attributes": {"referenceName": group["attributes"].get("referenceName")},
                "relationships": {"app": {"data": {"type": "apps", "id": app_id}}},
            }
        }
        group_resp = post(session, f"{BASE}/subscriptionGroups", group_payload, dry_run)
        new_group_id = group_resp["data"]["id"]

        for loc in group["localizations"]:
            loc_payload = {
                "data": {
                    "type": "subscriptionGroupLocalizations",
                    "attributes": {
                        "name": loc.get("name"),
                        "locale": loc.get("locale"),
                    },
                    "relationships": {
                        "subscriptionGroup": {"data": {"type": "subscriptionGroups", "id": new_group_id}}
                    },
                }
            }
            post(session, f"{BASE}/subscriptionGroupLocalizations", loc_payload, dry_run)

        new_subs = []
        for sub in group["subscriptions"]:
            attrs = sub["attributes"]
            product_id = attrs.get("productId", "") + suffix
            sub_payload = {
                "data": {
                    "type": "subscriptions",
                    "attributes": {
                        "name": attrs.get("name"),
                        "productId": product_id,
                        "subscriptionPeriod": attrs.get("subscriptionPeriod"),
                        "familySharable": attrs.get("familySharable", False),
                    },
                    "relationships": {
                        "group": {"data": {"type": "subscriptionGroups", "id": new_group_id}}
                    },
                }
            }
            sub_resp = post(session, f"{BASE}/subscriptions", sub_payload, dry_run)
            new_sub_id = sub_resp["data"]["id"]

            for loc in sub["localizations"]:
                loc_payload = {
                    "data": {
                        "type": "subscriptionLocalizations",
                        "attributes": {
                            "name": loc.get("name"),
                            "locale": loc.get("locale"),
                            "description": loc.get("description"),
                        },
                        "relationships": {
                            "subscription": {"data": {"type": "subscriptions", "id": new_sub_id}}
                        },
                    }
                }
                post(session, f"{BASE}/subscriptionLocalizations", loc_payload, dry_run)

            # Price points are subscription-scoped — re-resolve against the
            # new subscription's own available price points, matched by
            # territory + customerPrice (see references/api.md).
            if apply_prices_flag:
                n_ok, n_fail = apply_prices(
                    session, BASE, "subscription", new_sub_id, sub["prices"], dry_run
                )
                print(f"  prices for '{attrs.get('name')}': {n_ok} applied, {n_fail} failed")
            else:
                print(
                    f"NOTE: {len(sub['prices'])} price point(s) for '{attrs.get('name')}' "
                    f"NOT applied (pass --with-prices to resolve and apply them)."
                )
            if sub["introductoryOffers"]:
                print(
                    f"NOTE: {len(sub['introductoryOffers'])} introductory offer(s) for "
                    f"'{attrs.get('name')}' were not migrated — these reference price "
                    f"points too and must be re-created after prices are set. See "
                    f"references/api.md."
                )

            new_subs.append({"old_product_id": attrs.get("productId"), "new_id": new_sub_id})

        created["subscriptionGroups"].append(
            {"new_group_id": new_group_id, "subscriptions": new_subs}
        )

    return created


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=None)
    parser.add_argument("--app-id", default=None, help="Overrides new_app_id from config")
    parser.add_argument("--in", dest="infile", default="subscriptions_export.json")
    parser.add_argument("--suffix", default="", help="Append to product IDs to avoid collisions")
    parser.add_argument("--dry-run", action="store_true", help="Print requests without sending")
    parser.add_argument(
        "--with-prices", action="store_true",
        help="Resolve and apply prices by matching territory+customerPrice against the "
             "new subscription's own price points (see references/api.md before using)",
    )
    args = parser.parse_args()

    session, cfg = get_session(args.config)
    app_id = args.app_id or cfg.get("new_app_id")
    if not app_id:
        print("No app id: pass --app-id or set new_app_id in config", file=sys.stderr)
        sys.exit(1)

    with open(args.infile) as f:
        data = json.load(f)

    print(f"Importing into app {app_id} (dry_run={args.dry_run})...")
    result = import_subscriptions(
        session, app_id, data, args.dry_run, suffix=args.suffix, apply_prices_flag=args.with_prices
    )

    with open("migration_result.json", "w") as f:
        json.dump(result, f, indent=2)
    print("Wrote migration_result.json — check it for new IDs and required manual follow-ups.")
