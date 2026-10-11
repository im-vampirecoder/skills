"""
Read-only: print the current App Store Version state for a single app —
the editable (non-live) version's number/state, and per-locale
description, promotionalText, keywords, whatsNew, marketingUrl,
supportUrl. These fields live on appStoreVersionLocalizations (versioned,
tied to a submission), NOT on appInfo — a separate resource from
get_app_info.py/set_app_info.py.

Usage:
    python get_app_store_version_info.py --app-id APPID [--config PATH] [--platform IOS]
"""
import argparse
import json
import sys

from asc_auth import get_session
from export_subscriptions import get_all  # reuse pagination helper

BASE = "https://api.appstoreconnect.apple.com/v1"

VERSION_LOCALIZATION_FIELDS = (
    "locale", "description", "promotionalText", "keywords",
    "whatsNew", "marketingUrl", "supportUrl",
)


def find_editable_version(session, app_id, platform):
    """An app normally has at most one non-READY_FOR_SALE version at a
    time — the one still open for edits (PREPARE_FOR_SUBMISSION, or
    similar pre-release states). Live/history versions are read-only."""
    versions = get_all(
        session, f"{BASE}/apps/{app_id}/appStoreVersions",
        params={"filter[platform]": platform} if platform else None,
    )
    editable = [
        v for v in versions
        if v.get("attributes", {}).get("appStoreState") != "READY_FOR_SALE"
    ]
    return (editable[0] if editable else (versions[0] if versions else None))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=None)
    parser.add_argument("--app-id", required=True)
    parser.add_argument("--platform", default="IOS")
    args = parser.parse_args()

    session, cfg = get_session(args.config)
    version = find_editable_version(session, args.app_id, args.platform)
    if not version:
        print(f"No app store version found for app {args.app_id}.", file=sys.stderr)
        sys.exit(1)

    v_attrs = version["attributes"]
    print(json.dumps(
        {
            "versionId": version["id"],
            "versionString": v_attrs.get("versionString"),
            "appStoreState": v_attrs.get("appStoreState"),
            "appVersionState": v_attrs.get("appVersionState"),
        },
        indent=2,
    ))

    locs = get_all(session, f"{BASE}/appStoreVersions/{version['id']}/appStoreVersionLocalizations")
    out = []
    for loc in locs:
        attrs = loc["attributes"]
        out.append({"id": loc["id"], **{f: attrs.get(f) for f in VERSION_LOCALIZATION_FIELDS}})
    print(json.dumps(out, indent=2))
