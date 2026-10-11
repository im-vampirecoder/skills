"""
Submit an App Store version for App Review (reviewSubmissions API).

Usage:
    python submit_for_review.py --version 1.0.3 [--app-id ID | --bundle-id BID]
                                [--config PATH] [--dry-run]

Flow: find the version -> reuse an open (READY_FOR_REVIEW) review submission
or create one -> add the version as an item -> PATCH submitted=true.
Refuses if a submission is already WAITING_FOR_REVIEW / IN_REVIEW.
"""
import argparse
import sys

from release_common import (BASE, add_common_args, fail_on_error, find_app_store_versions,
                            get_all, get_session, resolve_app_id)

parser = argparse.ArgumentParser()
add_common_args(parser)
parser.add_argument("--version", required=True)
parser.add_argument("--dry-run", action="store_true")
args = parser.parse_args()

session, cfg = get_session(args.config)
app_id = resolve_app_id(session, cfg, args)

version = next((v for v in find_app_store_versions(session, app_id)
                if v["attributes"]["versionString"] == args.version), None)
if not version:
    sys.exit(f"Version {args.version} not found; run prepare_app_store_version.py first.")
vid = version["id"]
attached = session.get(f"{BASE}/appStoreVersions/{vid}/build").json().get("data")
if not attached:
    sys.exit("No build attached to this version.")
print(f"Version {args.version} [{version['attributes']['appStoreState']}] "
      f"build {attached['attributes']['version']} release {version['attributes'].get('releaseType')}")

submissions = get_all(session, f"{BASE}/reviewSubmissions",
                      params={"filter[app]": app_id, "filter[platform]": "IOS"})
busy = [s for s in submissions if s["attributes"]["state"] in ("WAITING_FOR_REVIEW", "IN_REVIEW")]
if busy:
    sys.exit(f"A submission is already {busy[0]['attributes']['state']} ({busy[0]['id']}).")
open_sub = next((s for s in submissions if s["attributes"]["state"] == "READY_FOR_REVIEW"), None)

if args.dry_run:
    print(f"DRY RUN: would {'reuse ' + open_sub['id'] if open_sub else 'create a review submission'}, "
          f"add version {vid}, and submit.")
    sys.exit(0)

if open_sub:
    rid = open_sub["id"]
else:
    resp = fail_on_error(session.post(f"{BASE}/reviewSubmissions", json={"data": {
        "type": "reviewSubmissions", "attributes": {"platform": "IOS"},
        "relationships": {"app": {"data": {"type": "apps", "id": app_id}}}}}), "Create submission")
    rid = resp.json()["data"]["id"]
print(f"SUBMISSION {rid}")

items = session.get(f"{BASE}/reviewSubmissions/{rid}/items", params={"include": "appStoreVersion"}).json()
already = any((i.get("relationships", {}).get("appStoreVersion", {}).get("data") or {}).get("id") == vid
              for i in items.get("data", []))
if not already:
    fail_on_error(session.post(f"{BASE}/reviewSubmissionItems", json={"data": {
        "type": "reviewSubmissionItems",
        "relationships": {
            "reviewSubmission": {"data": {"type": "reviewSubmissions", "id": rid}},
            "appStoreVersion": {"data": {"type": "appStoreVersions", "id": vid}}}}}), "Add item")

resp = fail_on_error(session.patch(f"{BASE}/reviewSubmissions/{rid}", json={"data": {
    "type": "reviewSubmissions", "id": rid, "attributes": {"submitted": True}}}), "Submit")
print(f"STATE {resp.json()['data']['attributes'].get('state')}")
