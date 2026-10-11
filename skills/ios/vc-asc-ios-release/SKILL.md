---
name: vc-asc-ios-release
description: Ship an iOS build through App Store Connect via the ASC API key - upload an archived build (.xcarchive) to App Store Connect/TestFlight, wait for processing, create or update the App Store version, attach the build, set What's New, and submit it for App Review. Use when the user asks to "upload the build", "push to TestFlight", "upload to App Store Connect", "submit for review", "submit to Apple", "release this build", or "send it to App Review". For editing app metadata, subscriptions or IAPs use vc-asc-app-manager instead.
---

# ASC iOS Release

Upload -> process -> prepare version -> submit for review, all with the
account API key in `asc_config.json` (same config as `vc-asc-app-manager`;
this skill imports that skill's `asc_auth.py`, so both must be installed
side by side).

Run every script from the **workspace root** (where `asc_config.json`
lives; `private_key_path` in it is resolved relative to the cwd). Python:
`$HOME/.claude/skills/.venv/bin/python3` (needs `pyjwt`, `requests`).
Never print the config or `.p8` contents. Scripts live in this skill's
folder: `SKILL_DIR=$HOME/.claude/skills/vc-asc-ios-release`.

App selection: `--app-id ID`, or `--bundle-id BID`, or default
`new_app_id` from the config. Check the project's `CLAUDE.md` for which
app is production vs staging; never submit a staging/TestFlight-only app
to review unless asked.

## 1. Build (precondition)

Version/build number come from the archive. Use the project's documented
archive steps (see its `CLAUDE.md`) if it has them. Otherwise: bump
`MARKETING_VERSION` / `CURRENT_PROJECT_VERSION` in every build config of
`project.pbxproj`, then per scheme:

```bash
xcodebuild archive -workspace "<App>.xcworkspace" -scheme "<Scheme>" \
  -destination 'generic/platform=iOS' -archivePath "build/<App>.xcarchive" -allowProvisioningUpdates
xcodebuild -exportArchive -archivePath "build/<App>.xcarchive" -exportPath "build/<App>-Export" \
  -exportOptionsPlist "build/ExportOptions.plist" -allowProvisioningUpdates
```

Archives can take ~10 min each; run them in the background.

## 2. Upload

```bash
"$SKILL_DIR/scripts/upload_build.sh" \
  --archive "build/<App>.xcarchive" \
  --export-options "build/ExportOptions.plist"
```

Forces `destination=upload` and `manageAppVersionAndBuildNumber=false`
on a temp copy of the export options, so the build number is not changed
by Xcode. An "Upload Symbols Failed" warning for a framework shipped
without dSYM (e.g. Firebase's `openssl_grpc.framework`) is expected and
does not fail the upload.

## 3. Wait for processing / export compliance

```bash
python3 "$SKILL_DIR/scripts/check_build.py" --version 1.2.0 --build 42 --wait 1800
```

Exits 0 once `VALID`. If `usesNonExemptEncryption` is `None`, ask the
user, then pass `--set-encryption false|true`. (Apps that set
`ITSAppUsesNonExemptEncryption=false` in Info.plist already report
`False`.)

## 4. Prepare the App Store version

Write What's New to a file first (user-facing; max 4000 chars; show it
to the user and get approval of the wording). Then dry-run:

```bash
python3 "$SKILL_DIR/scripts/prepare_app_store_version.py" \
  --version 1.2.0 --build 42 --whats-new-file whatsnew.txt --dry-run
```

Re-run without `--dry-run`. Creates the version (or reuses/renames the
single editable one), attaches the build, sets release type (default
`MANUAL`; `--release-type AFTER_APPROVAL` only if the user asks), and
sets What's New on every existing locale unless `--locale` limits it.

## 5. Submit for review

```bash
python3 "$SKILL_DIR/scripts/submit_for_review.py" --version 1.2.0 --dry-run
python3 "$SKILL_DIR/scripts/submit_for_review.py" --version 1.2.0
```

Expect `STATE WAITING_FOR_REVIEW`. Apple's error text is printed as-is
when something is missing (screenshots, app privacy, age rating, review
contact) - those must be fixed in the ASC UI; see vc-asc-app-manager's
"Things this skill does NOT automate".

## Confirmation and permissions

Steps 4-5 change the live App Store record and step 5 cannot be undone
from the API (a submission can only be withdrawn in the ASC UI). Get the
user's explicit go-ahead for the specific version/build before running
them without `--dry-run`.

Claude Code's permission system may block steps 4-5 as a production
deploy. If a call is denied, don't retry it or rephrase it to get past
the check. Tell the user and offer the exact command for them to run
themselves (prefixed with `!`), or let them add an allow rule in settings.

## After submitting

Report: version, build, submission id, state, release type, and (for
`MANUAL`) that the release must be done in ASC after approval. Update the
task's `.docs-for-review/` note if one exists.
