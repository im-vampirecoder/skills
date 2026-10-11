"""
Apply exported App Information (name/subtitle/categories) and recreate
one-time (non-subscription) in-app purchases on a target app.

Usage:
    python import_metadata.py --in metadata_export.json [--config PATH] [--dry-run] [--with-prices]
"""
import argparse
import json
import sys

from asc_auth import get_session
from resolve_prices import apply_prices

BASE_V1 = "https://api.appstoreconnect.apple.com/v1"
BASE_V2 = "https://api.appstoreconnect.apple.com/v2"


def request(session, method, url, payload, dry_run):
    if dry_run:
        print(f"[dry-run] {method} {url}\n{json.dumps(payload, indent=2)}\n")
        return {"data": {"id": "DRY_RUN_ID"}}
    resp = session.request(method, url, json=payload)
    if not resp.ok:
        print(f"FAILED {method} {url}: {resp.status_code} {resp.text[:500]}", file=sys.stderr)
        resp.raise_for_status()
    return resp.json() if resp.text else {}


def import_app_info(session, app_id, app_info_list, dry_run):
    """App Information is created automatically when the app record is
    created — this PATCHes the existing appInfo (name/subtitle/category)
    rather than creating a new one. Fetch the new app's own appInfo id
    first."""
    if dry_run:
        print(f"[dry-run] GET {BASE_V1}/apps/{app_id}/appInfos")
        target_info_id = "DRY_RUN_APPINFO_ID"
    else:
        resp = session.get(f"{BASE_V1}/apps/{app_id}/appInfos")
        resp.raise_for_status()
        target_infos = resp.json().get("data", [])
        if not target_infos:
            print("No appInfo found on target app — cannot apply metadata.", file=sys.stderr)
            return
        target_info_id = target_infos[0]["id"]

    for info in app_info_list:
        if info.get("primaryCategory"):
            payload = {
                "data": {
                    "type": "appInfos",
                    "id": target_info_id,
                    "relationships": {
                        "primaryCategory": {
                            "data": {"type": "appCategories", "id": info["primaryCategory"]}
                        }
                    },
                }
            }
            if info.get("secondaryCategory"):
                payload["data"]["relationships"]["secondaryCategory"] = {
                    "data": {"type": "appCategories", "id": info["secondaryCategory"]}
                }
            request(session, "PATCH", f"{BASE_V1}/appInfos/{target_info_id}", payload, dry_run)

        for loc in info["localizations"]:
            loc_payload = {
                "data": {
                    "type": "appInfoLocalizations",
                    "attributes": {
                        "locale": loc.get("locale"),
                        "name": loc.get("name"),
                        "subtitle": loc.get("subtitle"),
                        "privacyPolicyUrl": loc.get("privacyPolicyUrl"),
                    },
                    "relationships": {
                        "appInfo": {"data": {"type": "appInfos", "id": target_info_id}}
                    },
                }
            }
            request(session, "POST", f"{BASE_V1}/appInfoLocalizations", loc_payload, dry_run)
        break  # only one editable (non-live) appInfo is normally present


def import_one_time_iaps(session, app_id, iaps, dry_run, suffix="", apply_prices_flag=False):
    created = []
    for iap in iaps:
        attrs = iap["attributes"]
        product_id = attrs.get("productId", "") + suffix
        payload = {
            "data": {
                "type": "inAppPurchases",
                "attributes": {
                    "name": attrs.get("name"),
                    "productId": product_id,
                    "inAppPurchaseType": attrs.get("inAppPurchaseType"),
                    "familySharable": attrs.get("familySharable", False),
                },
                "relationships": {"app": {"data": {"type": "apps", "id": app_id}}},
            }
        }
        resp = request(session, "POST", f"{BASE_V2}/inAppPurchases", payload, dry_run)
        new_id = resp["data"]["id"]

        for loc in iap["localizations"]:
            loc_payload = {
                "data": {
                    "type": "inAppPurchaseLocalizations",
                    "attributes": {
                        "name": loc.get("name"),
                        "locale": loc.get("locale"),
                        "description": loc.get("description"),
                    },
                    "relationships": {
                        "inAppPurchaseV2": {"data": {"type": "inAppPurchases", "id": new_id}}
                    },
                }
            }
            request(session, "POST", f"{BASE_V2}/inAppPurchaseLocalizations", loc_payload, dry_run)

        if apply_prices_flag:
            n_ok, n_fail = apply_prices(session, BASE_V1, "iap", new_id, iap["prices"], dry_run)
            print(f"  prices for '{attrs.get('name')}': {n_ok} applied, {n_fail} failed")
        else:
            print(
                f"NOTE: {len(iap['prices'])} price point(s) for '{attrs.get('name')}' "
                f"NOT applied (pass --with-prices to resolve and apply them)."
            )

        created.append({"old_product_id": attrs.get("productId"), "new_id": new_id})
    return created


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=None)
    parser.add_argument("--app-id", default=None, help="Overrides new_app_id from config")
    parser.add_argument("--in", dest="infile", default="metadata_export.json")
    parser.add_argument("--suffix", default="")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--with-prices", action="store_true")
    parser.add_argument("--skip-app-info", action="store_true", help="Only migrate IAPs, not name/category")
    args = parser.parse_args()

    session, cfg = get_session(args.config)
    app_id = args.app_id or cfg.get("new_app_id")
    if not app_id:
        print("No app id: pass --app-id or set new_app_id in config", file=sys.stderr)
        sys.exit(1)

    with open(args.infile) as f:
        data = json.load(f)

    print(f"Importing metadata into app {app_id} (dry_run={args.dry_run})...")

    if not args.skip_app_info:
        import_app_info(session, app_id, data.get("appInfo", []), args.dry_run)

    created = import_one_time_iaps(
        session, app_id, data.get("inAppPurchases", []), args.dry_run,
        suffix=args.suffix, apply_prices_flag=args.with_prices,
    )

    with open("metadata_migration_result.json", "w") as f:
        json.dump({"inAppPurchases": created}, f, indent=2)
    print("Wrote metadata_migration_result.json")
