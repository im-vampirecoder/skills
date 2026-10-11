#!/usr/bin/env bash
# Upload an existing .xcarchive to App Store Connect using the ASC API key
# from asc_config.json (no Apple ID / app-specific password needed).
#
# Usage:
#   upload_build.sh --archive PATH.xcarchive --export-options ExportOptions.plist [--config asc_config.json]
#
# The given ExportOptions plist is copied to a temp file and forced to
# destination=upload and manageAppVersionAndBuildNumber=false, so the build
# keeps exactly the version/build number it was archived with.
set -euo pipefail

CONFIG="./asc_config.json"
ARCHIVE=""
EXPORT_OPTIONS=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --archive) ARCHIVE="$2"; shift 2 ;;
    --export-options) EXPORT_OPTIONS="$2"; shift 2 ;;
    --config) CONFIG="$2"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done
[[ -d "$ARCHIVE" ]] || { echo "Archive not found: $ARCHIVE" >&2; exit 2; }
[[ -f "$EXPORT_OPTIONS" ]] || { echo "Export options not found: $EXPORT_OPTIONS" >&2; exit 2; }
[[ -f "$CONFIG" ]] || { echo "Config not found: $CONFIG" >&2; exit 2; }

# Read key id / issuer / key path without echoing them.
{ read -r KEY_ID; read -r ISSUER_ID; read -r KEY_PATH; } < <(python3 - "$CONFIG" <<'EOF'
import json, os, sys
c = json.load(open(sys.argv[1]))
print(c["key_id"], c["issuer_id"], os.path.abspath(os.path.expanduser(c["private_key_path"])), sep="\n")
EOF
)
[[ -f "$KEY_PATH" ]] || { echo "Private key (.p8) from config not found" >&2; exit 2; }

PLIST_INFO="$ARCHIVE/Info.plist"
echo "Uploading $(/usr/libexec/PlistBuddy -c 'Print :ApplicationProperties:CFBundleIdentifier' "$PLIST_INFO")" \
  "$(/usr/libexec/PlistBuddy -c 'Print :ApplicationProperties:CFBundleShortVersionString' "$PLIST_INFO")" \
  "($(/usr/libexec/PlistBuddy -c 'Print :ApplicationProperties:CFBundleVersion' "$PLIST_INFO"))"

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
cp "$EXPORT_OPTIONS" "$WORK/ExportOptions.plist"
/usr/libexec/PlistBuddy -c 'Set :destination upload' "$WORK/ExportOptions.plist" 2>/dev/null \
  || /usr/libexec/PlistBuddy -c 'Add :destination string upload' "$WORK/ExportOptions.plist"
/usr/libexec/PlistBuddy -c 'Set :manageAppVersionAndBuildNumber false' "$WORK/ExportOptions.plist" 2>/dev/null \
  || /usr/libexec/PlistBuddy -c 'Add :manageAppVersionAndBuildNumber bool false' "$WORK/ExportOptions.plist"

LOG="$WORK/upload.log"
if xcodebuild -exportArchive \
    -archivePath "$ARCHIVE" \
    -exportPath "$WORK/out" \
    -exportOptionsPlist "$WORK/ExportOptions.plist" \
    -allowProvisioningUpdates \
    -authenticationKeyPath "$KEY_PATH" \
    -authenticationKeyID "$KEY_ID" \
    -authenticationKeyIssuerID "$ISSUER_ID" > "$LOG" 2>&1; then
  grep -E '^(Uploaded|warning:)' "$LOG" || true
  echo "UPLOAD SUCCEEDED (Apple processing usually takes 5-30 min; check with check_build.py --wait)"
else
  grep -iE 'error|fail' "$LOG" | tail -20 >&2
  echo "UPLOAD FAILED" >&2
  exit 1
fi
