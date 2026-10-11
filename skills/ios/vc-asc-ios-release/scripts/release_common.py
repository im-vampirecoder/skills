"""
Shared helpers for the vc-asc-ios-release scripts.

Authentication is NOT duplicated here: it reuses asc_auth.py and the
pagination helper from the sibling vc-asc-app-manager skill, so there is a
single place that touches the .p8 key.
"""
import os
import sys

_SIBLING = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "vc-asc-app-manager", "scripts"
)
if not os.path.isdir(_SIBLING):
    sys.exit(f"vc-asc-app-manager skill not found at {_SIBLING} (needed for asc_auth.py)")
sys.path.insert(0, _SIBLING)

from asc_auth import get_session  # noqa: E402
from export_subscriptions import get_all  # noqa: E402

BASE = "https://api.appstoreconnect.apple.com/v1"

# App Store Version states in which the version can still be edited and submitted.
EDITABLE_VERSION_STATES = {
    "PREPARE_FOR_SUBMISSION",
    "DEVELOPER_REJECTED",
    "REJECTED",
    "METADATA_REJECTED",
    "INVALID_BINARY",
}


def add_common_args(parser):
    """--config plus one of --app-id / --bundle-id (falls back to config new_app_id)."""
    parser.add_argument("--config", default=None, help="Path to asc_config.json")
    parser.add_argument("--app-id", default=None, help="ASC app id (numeric)")
    parser.add_argument("--bundle-id", default=None, help="Resolve the app by bundle id instead")


def resolve_app_id(session, cfg, args):
    if args.app_id:
        return args.app_id
    if args.bundle_id:
        apps = session.get(f"{BASE}/apps", params={"filter[bundleId]": args.bundle_id}).json()
        matches = [a for a in apps.get("data", []) if a["attributes"]["bundleId"] == args.bundle_id]
        if not matches:
            sys.exit(f"No app visible to this API key has bundle id {args.bundle_id}")
        return matches[0]["id"]
    if cfg.get("new_app_id"):
        return cfg["new_app_id"]
    sys.exit("Pass --app-id or --bundle-id (config has no new_app_id default)")


def find_build(session, app_id, version, build_number):
    """Return the build resource for marketing version + build number, or None."""
    resp = session.get(f"{BASE}/builds", params={
        "filter[app]": app_id,
        "filter[version]": str(build_number),
        "filter[preReleaseVersion.version]": version,
        "limit": 1,
    })
    resp.raise_for_status()
    data = resp.json().get("data", [])
    return data[0] if data else None


def find_app_store_versions(session, app_id, platform="IOS"):
    return get_all(session, f"{BASE}/apps/{app_id}/appStoreVersions",
                   params={"filter[platform]": platform})


def fail_on_error(resp, what):
    if not resp.ok:
        print(f"{what} failed: HTTP {resp.status_code}\n{resp.text}", file=sys.stderr)
        sys.exit(1)
    return resp
