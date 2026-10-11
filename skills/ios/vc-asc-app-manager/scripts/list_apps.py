"""
List every app visible to the configured App Store Connect API key, with
its numeric app id, bundle id, and name. Use this to discover the app_id
needed by every other script in this skill (they all take a numeric
app id, not a bundle id or app name).

Usage:
    python list_apps.py [--config PATH]
"""
import argparse
import sys

from asc_auth import get_session
from export_subscriptions import get_all  # reuse pagination helper

BASE = "https://api.appstoreconnect.apple.com/v1"


def list_apps(session):
    apps = get_all(session, f"{BASE}/apps")
    out = []
    for app in apps:
        attrs = app.get("attributes", {})
        out.append(
            {
                "id": app["id"],
                "name": attrs.get("name"),
                "bundleId": attrs.get("bundleId"),
                "sku": attrs.get("sku"),
                "primaryLocale": attrs.get("primaryLocale"),
            }
        )
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=None)
    args = parser.parse_args()

    session, cfg = get_session(args.config)
    apps = list_apps(session)

    if not apps:
        print("No apps visible to this API key.", file=sys.stderr)
        sys.exit(1)

    for a in apps:
        print(f"{a['id']}\t{a['bundleId']}\t{a['name']}")
    print(f"\n{len(apps)} app(s). Use the first column as --app-id for other scripts.", file=sys.stderr)
