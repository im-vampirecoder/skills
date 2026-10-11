"""
Export App Information (name, subtitle, categories) and one-time
(non-subscription) in-app purchases from a source app.

Does NOT export: screenshots/app previews, app description/keywords/promo
text (those live on app store *versions*, not app info, and are tied to a
specific submitted version — out of scope for this skill), privacy
details, age rating, or App Store availability/territories.

Usage:
    python export_metadata.py [--config PATH] [--out metadata_export.json]
"""
import argparse
import json
import sys

from asc_auth import get_session
from export_subscriptions import get_all  # reuse pagination helper

BASE_V1 = "https://api.appstoreconnect.apple.com/v1"
BASE_V2 = "https://api.appstoreconnect.apple.com/v2"


def export_app_info(session, app_id):
    """App Information: name/subtitle localizations + primary/secondary category.

    Must pass include=primaryCategory,secondaryCategory explicitly — Apple
    omits the "data" member of these to-one relationships (only "links" is
    returned) unless the relationship is included, so reading
    relationships["primaryCategory"]["data"] silently returns nothing on a
    plain GET even when a category is actually set (confirmed live)."""
    infos = get_all(
        session,
        f"{BASE_V1}/apps/{app_id}/appInfos",
        params={"include": "primaryCategory,secondaryCategory"},
    )
    out = []
    for info in infos:
        info_id = info["id"]
        attrs = info.get("attributes", {})
        rels = info.get("relationships", {})
        loc = get_all(session, f"{BASE_V1}/appInfos/{info_id}/appInfoLocalizations")
        out.append(
            {
                "appStoreState": attrs.get("appStoreState"),
                "primaryCategory": rels.get("primaryCategory", {}).get("data", {}).get("id"),
                "secondaryCategory": rels.get("secondaryCategory", {}).get("data", {}).get("id"),
                "localizations": [
                    {
                        "locale": l["attributes"].get("locale"),
                        "name": l["attributes"].get("name"),
                        "subtitle": l["attributes"].get("subtitle"),
                        "privacyPolicyUrl": l["attributes"].get("privacyPolicyUrl"),
                    }
                    for l in loc
                ],
            }
        )
    return out


def export_one_time_iaps(session, app_id):
    """Non-subscription in-app purchases (consumable/non-consumable).
    Endpoint is v1 with the "V2" resource name in the path/relationship
    (`inAppPurchasesV2`), not `/v2/apps/{id}/inAppPurchases` — confirmed live
    (the latter 404s; App Store Connect API docs for "List All In-App
    Purchases for an App" moved this under v1)."""
    iaps = get_all(session, f"{BASE_V1}/apps/{app_id}/inAppPurchasesV2")
    out = []
    for iap in iaps:
        iap_id = iap["id"]
        attrs = iap.get("attributes", {})
        loc = get_all(session, f"{BASE_V1}/inAppPurchasesV2/{iap_id}/inAppPurchaseLocalizations")

        prices = []
        resp = session.get(
            f"{BASE_V1}/inAppPurchasePriceSchedules/{iap_id}/manualPrices",
            # territory is a top-level relationship on the manual price itself,
            # not on the included price point (see export_subscriptions.py).
            params={"include": "inAppPurchasePricePoint,territory"},
        )
        if resp.ok:
            body = resp.json()
            included = {i["id"]: i for i in body.get("included", [])}
            for p in body.get("data", []):
                point_id = (
                    p.get("relationships", {})
                    .get("inAppPurchasePricePoint", {})
                    .get("data", {})
                    .get("id")
                )
                point = included.get(point_id, {})
                point_attrs = point.get("attributes", {})
                territory = (
                    p.get("relationships", {}).get("territory", {}).get("data", {}).get("id")
                )
                prices.append(
                    {"territory": territory, "customerPrice": point_attrs.get("customerPrice")}
                )
        else:
            print(
                f"  (no price schedule readable for IAP {iap_id}, product "
                f"{attrs.get('productId')} — may need App Manager role)",
                file=sys.stderr,
            )

        out.append(
            {
                "attributes": {
                    "name": attrs.get("name"),
                    "productId": attrs.get("productId"),
                    "inAppPurchaseType": attrs.get("inAppPurchaseType"),
                    "familySharable": attrs.get("familySharable", False),
                },
                "localizations": [
                    {
                        "locale": l["attributes"].get("locale"),
                        "name": l["attributes"].get("name"),
                        "description": l["attributes"].get("description"),
                    }
                    for l in loc
                ],
                "prices": prices,
            }
        )
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=None)
    parser.add_argument("--app-id", default=None, help="Overrides old_app_id from config")
    parser.add_argument("--out", default="metadata_export.json")
    args = parser.parse_args()

    session, cfg = get_session(args.config)
    app_id = args.app_id or cfg.get("old_app_id")
    if not app_id:
        print("No app id: pass --app-id or set old_app_id in config", file=sys.stderr)
        sys.exit(1)

    print(f"Exporting app info + one-time IAPs from app {app_id}...")
    data = {
        "app_id": app_id,
        "appInfo": export_app_info(session, app_id),
        "inAppPurchases": export_one_time_iaps(session, app_id),
    }

    print(f"Found {len(data['appInfo'])} app info record(s), {len(data['inAppPurchases'])} one-time IAP(s).")

    with open(args.out, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Wrote {args.out}")
