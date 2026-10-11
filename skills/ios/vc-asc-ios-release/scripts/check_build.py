"""
Check an uploaded build's processing state and export-compliance flag.

Usage:
    python check_build.py --version 1.0.3 --build 67 [--app-id ID | --bundle-id BID]
                          [--wait 1800] [--set-encryption false] [--config PATH]

--wait SECONDS   poll every 60s until processingState is VALID (or FAILED/INVALID)
--set-encryption true|false   PATCH usesNonExemptEncryption when the build has
                 no value yet (needed before it can be submitted). Prefer setting
                 ITSAppUsesNonExemptEncryption in Info.plist so this is never needed.
"""
import argparse
import sys
import time

from release_common import BASE, add_common_args, fail_on_error, find_build, get_session, resolve_app_id

parser = argparse.ArgumentParser()
add_common_args(parser)
parser.add_argument("--version", required=True, help="Marketing version, e.g. 1.0.3")
parser.add_argument("--build", required=True, help="Build number, e.g. 67")
parser.add_argument("--wait", type=int, default=0, help="Max seconds to wait for VALID")
parser.add_argument("--set-encryption", choices=["true", "false"], default=None)
args = parser.parse_args()

deadline = time.time() + args.wait
while True:
    # New session each poll: ASC tokens expire after ~20 minutes.
    session, cfg = get_session(args.config)
    app_id = resolve_app_id(session, cfg, args)
    build = find_build(session, app_id, args.version, args.build)
    state = build["attributes"]["processingState"] if build else "NOT_FOUND"
    print(f"{args.version} ({args.build}): {state}", flush=True)
    if state in ("VALID", "FAILED", "INVALID") or time.time() >= deadline:
        break
    time.sleep(60)

if not build:
    sys.exit("Build not visible in App Store Connect yet.")
attrs = build["attributes"]
print(f"BUILD_ID {build['id']}")
print(f"usesNonExemptEncryption {attrs.get('usesNonExemptEncryption')}")
print(f"expired {attrs.get('expired')}  uploaded {attrs.get('uploadedDate')}")

if args.set_encryption is not None:
    if attrs.get("usesNonExemptEncryption") is not None:
        print("Encryption already declared; not changing it.")
    else:
        value = args.set_encryption == "true"
        fail_on_error(session.patch(f"{BASE}/builds/{build['id']}", json={"data": {
            "type": "builds", "id": build["id"],
            "attributes": {"usesNonExemptEncryption": value}}}), "Set encryption")
        print(f"usesNonExemptEncryption set to {value}")

if state != "VALID":
    sys.exit(1)
