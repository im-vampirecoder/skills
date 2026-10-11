"""
Directly edit App Information on a single existing app — no source app
required. Covers the per-locale localizable fields (name, subtitle,
privacyPolicyUrl) and the primary/secondary category. This is the tool
for "add the Privacy Policy URL to the app record," "rename the app,"
"change category" — anything that isn't a clone-from-another-app job
(for that, see the clone/migrate workflow in SKILL.md instead).

Only the fields you pass are changed. Omitted fields are left as-is: if a
localization already exists for --locale, only the passed attributes are
included in the PATCH body (Apple leaves unset attributes untouched on a
partial PATCH); if no localization exists yet for --locale, a new one is
POSTed and any field you didn't pass is omitted (Apple will reject a new
localization missing "name", the one genuinely required field).

Usage:
    python set_app_info.py --app-id APPID --locale en-US \\
        [--config PATH] [--name NAME] [--subtitle SUBTITLE] \\
        [--privacy-policy-url URL] \\
        [--primary-category ID] [--secondary-category ID] \\
        [--dry-run]

Category IDs are App Store Connect appCategories ids (e.g.
HEALTH_AND_FITNESS, PHOTO_AND_VIDEO) — see
https://developer.apple.com/documentation/appstoreconnectapi/appcategory
or GET /v1/appCategories to list them.
"""
import argparse
import json
import sys

from asc_auth import get_session
from export_subscriptions import get_all  # reuse pagination helper

BASE = "https://api.appstoreconnect.apple.com/v1"


def request(session, method, url, payload, dry_run):
    if dry_run:
        print(f"[dry-run] {method} {url}\n{json.dumps(payload, indent=2)}\n")
        return {"data": {"id": "DRY_RUN_ID"}}
    resp = session.request(method, url, json=payload)
    if not resp.ok:
        print(f"FAILED {method} {url}: {resp.status_code} {resp.text[:500]}", file=sys.stderr)
        resp.raise_for_status()
    return resp.json() if resp.text else {}


def find_editable_app_info(session, app_id):
    """An app normally has exactly one editable (non-live) appInfo record;
    if a version is already live there may be a second, read-only, live
    one. Prefer the one whose appStoreState is editable-ish; fall back to
    the first if that can't be determined."""
    resp = session.get(f"{BASE}/apps/{app_id}/appInfos")
    resp.raise_for_status()
    infos = resp.json().get("data", [])
    if not infos:
        return None
    non_live = [
        i for i in infos
        if i.get("attributes", {}).get("appStoreState") not in ("READY_FOR_SALE",)
    ]
    return (non_live[0] if non_live else infos[0])["id"]


def set_category(session, app_info_id, primary_category, secondary_category, dry_run):
    relationships = {}
    if primary_category:
        relationships["primaryCategory"] = {
            "data": {"type": "appCategories", "id": primary_category}
        }
    if secondary_category:
        relationships["secondaryCategory"] = {
            "data": {"type": "appCategories", "id": secondary_category}
        }
    if not relationships:
        return
    payload = {
        "data": {"type": "appInfos", "id": app_info_id, "relationships": relationships}
    }
    request(session, "PATCH", f"{BASE}/appInfos/{app_info_id}", payload, dry_run)
    print(f"Category updated: {relationships.keys()}")


def set_localization(session, app_info_id, locale, name, subtitle, privacy_policy_url, dry_run):
    attrs = {}
    if name is not None:
        attrs["name"] = name
    if subtitle is not None:
        attrs["subtitle"] = subtitle
    if privacy_policy_url is not None:
        attrs["privacyPolicyUrl"] = privacy_policy_url
    if not attrs:
        return

    existing = get_all(session, f"{BASE}/appInfos/{app_info_id}/appInfoLocalizations")
    match = next((l for l in existing if l["attributes"].get("locale") == locale), None)

    if match:
        payload = {
            "data": {"type": "appInfoLocalizations", "id": match["id"], "attributes": attrs}
        }
        request(session, "PATCH", f"{BASE}/appInfoLocalizations/{match['id']}", payload, dry_run)
        print(f"Localization '{locale}' patched: {list(attrs.keys())}")
    else:
        if "name" not in attrs:
            print(
                f"No existing localization for '{locale}' and --name not given — "
                f"Apple requires 'name' on a new appInfoLocalization. Pass --name to create it.",
                file=sys.stderr,
            )
            sys.exit(1)
        attrs["locale"] = locale
        payload = {
            "data": {
                "type": "appInfoLocalizations",
                "attributes": attrs,
                "relationships": {"appInfo": {"data": {"type": "appInfos", "id": app_info_id}}},
            }
        }
        request(session, "POST", f"{BASE}/appInfoLocalizations", payload, dry_run)
        print(f"Localization '{locale}' created: {list(attrs.keys())}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=None)
    parser.add_argument("--app-id", required=True)
    parser.add_argument("--locale", help="e.g. en-US, en-AU, en-GB — required if setting name/subtitle/privacy-policy-url")
    parser.add_argument("--name")
    parser.add_argument("--subtitle")
    parser.add_argument("--privacy-policy-url")
    parser.add_argument("--primary-category")
    parser.add_argument("--secondary-category")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if (args.name or args.subtitle or args.privacy_policy_url) and not args.locale:
        print("--locale is required when setting name/subtitle/privacy-policy-url", file=sys.stderr)
        sys.exit(1)

    session, cfg = get_session(args.config)
    app_info_id = find_editable_app_info(session, args.app_id)
    if not app_info_id:
        print(f"No appInfo record found for app {args.app_id}.", file=sys.stderr)
        sys.exit(1)

    set_category(session, app_info_id, args.primary_category, args.secondary_category, args.dry_run)
    if args.locale:
        set_localization(
            session, app_info_id, args.locale, args.name, args.subtitle,
            args.privacy_policy_url, args.dry_run,
        )

    print("Done." if not args.dry_run else "Dry run complete, no writes made.")
