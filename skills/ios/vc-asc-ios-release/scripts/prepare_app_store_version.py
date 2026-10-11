"""
Create (or reuse) the editable App Store version, attach a processed build,
set release type, and set What's New on every locale (or the ones given).

Usage:
    python prepare_app_store_version.py --version 1.0.3 --build 67 --whats-new-file whatsnew.txt
        [--release-type MANUAL|AFTER_APPROVAL] [--locale en-US --locale en-AU]
        [--app-id ID | --bundle-id BID] [--config PATH] [--dry-run]

If an editable version already exists with a different version string, it is
renamed to --version (same as editing the number in the ASC UI) rather than
creating a second one, since ASC allows only one open version per platform.
"""
import argparse
import sys

from release_common import (BASE, EDITABLE_VERSION_STATES, add_common_args, fail_on_error,
                            find_app_store_versions, find_build, get_session, resolve_app_id)

parser = argparse.ArgumentParser()
add_common_args(parser)
parser.add_argument("--version", required=True)
parser.add_argument("--build", required=True, help="Build number to attach")
parser.add_argument("--whats-new-file", required=True)
parser.add_argument("--release-type", default="MANUAL", choices=["MANUAL", "AFTER_APPROVAL"])
parser.add_argument("--locale", action="append", default=None, help="Limit to these locales")
parser.add_argument("--dry-run", action="store_true")
args = parser.parse_args()

session, cfg = get_session(args.config)
app_id = resolve_app_id(session, cfg, args)
whats_new = open(args.whats_new_file, encoding="utf-8").read().strip()
if len(whats_new) > 4000:
    sys.exit(f"What's New is {len(whats_new)} chars; ASC limit is 4000.")

build = find_build(session, app_id, args.version, args.build)
if not build or build["attributes"]["processingState"] != "VALID":
    sys.exit("Build not found or not VALID yet; run check_build.py --wait first.")
if build["attributes"].get("usesNonExemptEncryption") is None:
    print("WARNING: build has no export-compliance answer; submission will fail. "
          "Use check_build.py --set-encryption.", file=sys.stderr)

versions = find_app_store_versions(session, app_id)
editable = [v for v in versions if v["attributes"]["appStoreState"] in EDITABLE_VERSION_STATES]
existing = editable[0] if editable else None
if not existing:
    # Same version string already past the editable stage (in review, approved, live...).
    locked = next((v for v in versions if v["attributes"]["versionString"] == args.version), None)
    if locked:
        sys.exit(f"Version {args.version} already exists in state "
                 f"{locked['attributes']['appStoreState']} and can't be edited; use a new version.")

print(f"App {app_id} | build {args.version} ({args.build}) id {build['id']}")
if existing:
    print(f"Reusing editable version {existing['attributes']['versionString']} "
          f"[{existing['attributes']['appStoreState']}] id {existing['id']}")
else:
    print(f"Will create version {args.version} ({args.release_type})")
print(f"What's New ({len(whats_new)} chars) -> {args.locale or 'all locales'}:\n{whats_new}\n")
if args.dry_run:
    print("DRY RUN: no changes made.")
    sys.exit(0)

if existing:
    vid = existing["id"]
    fail_on_error(session.patch(f"{BASE}/appStoreVersions/{vid}", json={"data": {
        "type": "appStoreVersions", "id": vid,
        "attributes": {"versionString": args.version, "releaseType": args.release_type}}}),
        "Update version")
    fail_on_error(session.patch(f"{BASE}/appStoreVersions/{vid}/relationships/build", json={
        "data": {"type": "builds", "id": build["id"]}}), "Attach build")
else:
    resp = fail_on_error(session.post(f"{BASE}/appStoreVersions", json={"data": {
        "type": "appStoreVersions",
        "attributes": {"platform": "IOS", "versionString": args.version,
                       "releaseType": args.release_type},
        "relationships": {
            "app": {"data": {"type": "apps", "id": app_id}},
            "build": {"data": {"type": "builds", "id": build["id"]}}}}}), "Create version")
    vid = resp.json()["data"]["id"]
print(f"VERSION {vid}")

locs = session.get(f"{BASE}/appStoreVersions/{vid}/appStoreVersionLocalizations").json()["data"]
for loc in locs:
    code = loc["attributes"]["locale"]
    if args.locale and code not in args.locale:
        continue
    fail_on_error(session.patch(f"{BASE}/appStoreVersionLocalizations/{loc['id']}", json={"data": {
        "type": "appStoreVersionLocalizations", "id": loc["id"],
        "attributes": {"whatsNew": whats_new}}}), f"Set What's New ({code})")
    print(f"whatsNew set: {code}")

attached = session.get(f"{BASE}/appStoreVersions/{vid}/build").json().get("data")
print(f"BUILD ATTACHED {attached['attributes']['version'] if attached else None}")
