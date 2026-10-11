"""
Directly edit App Store Version Localization fields on a single app's
editable version — description, promotionalText, keywords, whatsNew,
marketingUrl, supportUrl. These are versioned fields (tied to the
in-progress submission), distinct from set_app_info.py's appInfo fields
(name/subtitle/category/privacyPolicyUrl).

Only the fields you pass are changed; everything else is left as-is.

Usage:
    python set_app_store_version_info.py --app-id APPID --locale en-US \\
        [--config PATH] [--platform IOS] \\
        [--description TEXT] [--promotional-text TEXT] [--keywords TEXT] \\
        [--whats-new TEXT] [--marketing-url URL] [--support-url URL] \\
        [--dry-run]

Field limits (enforced by Apple, not this script — it will just fail the
PATCH): description 4000 chars, promotionalText 170 chars, keywords 100
bytes comma-separated, whatsNew 4000 chars.
"""
import argparse
import json
import sys

from asc_auth import get_session
from export_subscriptions import get_all  # reuse pagination helper
from get_app_store_version_info import find_editable_version

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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=None)
    parser.add_argument("--app-id", required=True)
    parser.add_argument("--platform", default="IOS")
    parser.add_argument("--locale", required=True, help="e.g. en-US, en-AU, en-GB, en-CA")
    parser.add_argument("--description")
    parser.add_argument("--description-file", help="Read --description value from a file instead (avoids shell-quoting long/multi-line text)")
    parser.add_argument("--promotional-text")
    parser.add_argument("--keywords")
    parser.add_argument("--whats-new")
    parser.add_argument("--marketing-url")
    parser.add_argument("--support-url")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.description and args.description_file:
        print("Pass only one of --description / --description-file", file=sys.stderr)
        sys.exit(1)

    attrs = {}
    if args.description_file is not None:
        with open(args.description_file) as f:
            attrs["description"] = f.read().strip()
    elif args.description is not None:
        attrs["description"] = args.description
    if args.promotional_text is not None:
        attrs["promotionalText"] = args.promotional_text
    if args.keywords is not None:
        attrs["keywords"] = args.keywords
    if args.whats_new is not None:
        attrs["whatsNew"] = args.whats_new
    if args.marketing_url is not None:
        attrs["marketingUrl"] = args.marketing_url
    if args.support_url is not None:
        attrs["supportUrl"] = args.support_url

    if not attrs:
        print("Nothing to do — pass at least one field to set.", file=sys.stderr)
        sys.exit(1)

    session, cfg = get_session(args.config)
    version = find_editable_version(session, args.app_id, args.platform)
    if not version:
        print(f"No app store version found for app {args.app_id}.", file=sys.stderr)
        sys.exit(1)

    locs = get_all(session, f"{BASE}/appStoreVersions/{version['id']}/appStoreVersionLocalizations")
    match = next((l for l in locs if l["attributes"].get("locale") == args.locale), None)

    if match:
        payload = {
            "data": {"type": "appStoreVersionLocalizations", "id": match["id"], "attributes": attrs}
        }
        request(session, "PATCH", f"{BASE}/appStoreVersionLocalizations/{match['id']}", payload, args.dry_run)
        print(f"Localization '{args.locale}' patched: {list(attrs.keys())}")
    else:
        attrs["locale"] = args.locale
        if "description" not in attrs:
            print(
                f"No existing localization for '{args.locale}' and --description not given — "
                f"Apple requires 'description' on a new appStoreVersionLocalization.",
                file=sys.stderr,
            )
            sys.exit(1)
        payload = {
            "data": {
                "type": "appStoreVersionLocalizations",
                "attributes": attrs,
                "relationships": {
                    "appStoreVersion": {"data": {"type": "appStoreVersions", "id": version["id"]}}
                },
            }
        }
        request(session, "POST", f"{BASE}/appStoreVersionLocalizations", payload, args.dry_run)
        print(f"Localization '{args.locale}' created: {list(attrs.keys())}")

    print("Done." if not args.dry_run else "Dry run complete, no writes made.")
