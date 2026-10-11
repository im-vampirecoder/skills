"""
Export all subscription groups, subscriptions, localizations, and price
points from a source app in App Store Connect into a single JSON file.

Usage:
    python export_subscriptions.py [--config PATH] [--out subscriptions_export.json]

Reads old_app_id from the config file unless --app-id is passed explicitly.
"""
import argparse
import base64
import json
import sys

from asc_auth import get_session

BASE = "https://api.appstoreconnect.apple.com/v1"


def decode_price_tier(point_id):
    """Price point ids are base64 JSON: {"s": subscriptionId, "t": territory,
    "p": tier}. The tier->customerPrice mapping is universal per territory
    across subscriptions and apps (confirmed live: reusing a tier on a
    different subscription/app yields the identical customerPrice) — capturing
    it lets a later import construct the new subscription's own price point id
    directly instead of paginating through ~800 price points per territory to
    find a customerPrice match."""
    if not point_id:
        return None
    padded = point_id + "=" * (-len(point_id) % 4)
    try:
        return json.loads(base64.b64decode(padded)).get("p")
    except Exception:
        return None


def get_all(session, url, params=None):
    """Follow pagination and return a flat list of `data` entries."""
    items = []
    while url:
        resp = session.get(url, params=params)
        params = None  # only apply on first request; subsequent links are absolute
        resp.raise_for_status()
        body = resp.json()
        items.extend(body.get("data", []))
        url = body.get("links", {}).get("next")
    return items


def export_app_subscriptions(session, app_id):
    result = {"app_id": app_id, "subscriptionGroups": []}

    groups = get_all(session, f"{BASE}/apps/{app_id}/subscriptionGroups")
    for group in groups:
        group_id = group["id"]
        group_out = {
            "attributes": group.get("attributes", {}),
            "localizations": [],
            "subscriptions": [],
        }

        loc = get_all(
            session, f"{BASE}/subscriptionGroups/{group_id}/subscriptionGroupLocalizations"
        )
        group_out["localizations"] = [l["attributes"] for l in loc]

        subs = get_all(session, f"{BASE}/subscriptionGroups/{group_id}/subscriptions")
        for sub in subs:
            sub_id = sub["id"]
            sub_out = {"attributes": sub.get("attributes", {})}

            sub_loc = get_all(session, f"{BASE}/subscriptions/{sub_id}/subscriptionLocalizations")
            sub_out["localizations"] = [l["attributes"] for l in sub_loc]

            # include=subscriptionPricePoint gets customerPrice; territory is a
            # separate top-level relationship on the price itself (NOT on the
            # included pricePoint — that only has equalizations/adjustedEqualizations).
            sub_out["prices"] = []
            url = f"{BASE}/subscriptions/{sub_id}/prices"
            params = {"include": "subscriptionPricePoint,territory"}
            while url:
                resp = session.get(url, params=params)
                params = None
                resp.raise_for_status()
                body = resp.json()
                included = {i["id"]: i for i in body.get("included", [])}
                for p in body.get("data", []):
                    # Only UPFRONT is the subscription's normal price. Other planTypes
                    # (e.g. MONTHLY) are Apple's "Recurring Billing" pay-in-installments
                    # option for the same subscription — a separately-configured
                    # feature this skill doesn't migrate; skip so it doesn't get
                    # carried forward as if it were the base price.
                    if p.get("attributes", {}).get("planType") != "UPFRONT":
                        continue
                    point_id = p.get("relationships", {}).get("subscriptionPricePoint", {}).get("data", {}).get("id")
                    point = included.get(point_id, {})
                    point_attrs = point.get("attributes", {})
                    territory = p.get("relationships", {}).get("territory", {}).get("data", {}).get("id")
                    sub_out["prices"].append(
                        {
                            "id": p["id"],
                            "territory": territory,
                            "customerPrice": point_attrs.get("customerPrice"),
                            "priceTier": decode_price_tier(point_id),
                        }
                    )
                url = body.get("links", {}).get("next")

            intro_offers = get_all(
                session, f"{BASE}/subscriptions/{sub_id}/introductoryOffers"
            )
            sub_out["introductoryOffers"] = [o["attributes"] for o in intro_offers]

            group_out["subscriptions"].append(sub_out)

        result["subscriptionGroups"].append(group_out)

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=None)
    parser.add_argument("--app-id", default=None, help="Overrides old_app_id from config")
    parser.add_argument("--out", default="subscriptions_export.json")
    args = parser.parse_args()

    session, cfg = get_session(args.config)
    app_id = args.app_id or cfg.get("old_app_id")
    if not app_id:
        print("No app id: pass --app-id or set old_app_id in config", file=sys.stderr)
        sys.exit(1)

    print(f"Exporting subscriptions from app {app_id}...")
    data = export_app_subscriptions(session, app_id)

    n_groups = len(data["subscriptionGroups"])
    n_subs = sum(len(g["subscriptions"]) for g in data["subscriptionGroups"])
    print(f"Found {n_groups} subscription group(s), {n_subs} subscription(s).")

    with open(args.out, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Wrote {args.out}")
