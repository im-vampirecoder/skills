---
name: vc-asc-app-manager
description: Manage an app in App Store Connect directly via the App Store Connect API — read or edit App Information (name, subtitle, category, Privacy Policy URL) on a single app, read or edit the current App Store Version's localized listing text (description, promotional text, keywords, what's new, marketing/support URL), list apps visible to the API key, and clone/migrate an app's subscriptions, one-time in-app purchases, app info, and prices onto a different app record. Use whenever the user asks to update App Store Connect metadata (e.g. "add the privacy policy link," "rename the app," "change category," "update the description," "set the promotional text"), asks about App Store Connect API automation for subscriptions or IAPs, needs to clone/recreate app configuration after registering a new bundle ID, or mentions "copy subscriptions," "migrate IAP," "clone app metadata," or "bundle ID change" together with App Store Connect/TestFlight.
---

# App Store Connect App Manager

Manages an app in App Store Connect via the API, using an account-scoped
API key (`.p8`) the user has already generated. Two kinds of jobs:

1. **Direct edits on one app** — read or set App Information fields
   (name, subtitle, category, Privacy Policy URL) without touching any
   other app. This is the default for "update X in App Store Connect."
2. **Clone/migrate app data from one app to another** — copies
   subscription groups, one-time IAPs, app info, localizations, and
   prices from a source app record to a target app record. Built for the
   case where a bundle ID changed and a brand-new app record needs to be
   populated from an existing app.

Does NOT cover screenshots/app previews, App Privacy, age rating,
availability/territories, or App Review submission — see
`references/api.md` "Things this skill does NOT automate" for the full
list and why (mostly: no write endpoint exists at all).

## Before running anything

1. Confirm the user has generated an App Store Connect API key with
   **Admin or App Manager** role (Users and Access > Integrations), and
   downloaded the `.p8` private key file. This can only be downloaded once
   — if lost, they must revoke and generate a new key.
2. Ask the user for (or help them create) `asc_config.json` in the project
   root, based on `asc_config.example.json` in this skill. It always
   needs: `key_id`, `issuer_id`, `private_key_path`. `old_app_id` and
   `new_app_id` are only needed for the clone/migrate workflow — for
   direct single-app edits pass `--app-id` on the command line instead
   (`python scripts/list_apps.py` finds it if the user doesn't know it).
3. Never print, log, or commit the contents of the `.p8` key or the config
   file. Treat `private_key_path` as sensitive.

## Direct edits on one app (no source/target pair needed)

1. **Discover the app id**, if the user doesn't have it —
   `scripts/list_apps.py` prints every app the key can see: id, bundle
   id, name.
2. **Read current state** — `scripts/get_app_info.py --app-id APPID`
   prints category and every locale's name/subtitle/privacyPolicyUrl.
   Run this first so you know which locale(s) already exist and don't
   accidentally create a stray new localization.
3. **Write** — `scripts/set_app_info.py --app-id APPID --locale en-US
   [--name ...] [--subtitle ...] [--privacy-policy-url ...]
   [--primary-category ID] [--secondary-category ID] [--dry-run]`.
   Only the flags passed are changed; omitted fields are left as-is.
   Always run `--dry-run` first and show the user the payload before the
   real write, since App Information fields are user-facing on the App
   Store product page. Category IDs come from
   `https://developer.apple.com/documentation/appstoreconnectapi/appcategory`
   or `GET /v1/appCategories`.
4. If the app has multiple storefront locales (e.g. the doc's en-AU vs
   en-US vs en-GB fallback situation), repeat step 3 once per locale —
   there is no bulk "set for every locale" endpoint.

### Version listing text (description, promotional text, keywords, marketing/support URL)

These fields live on the app's current **App Store Version** localization
(versioned, tied to the in-progress submission) — a different resource
from App Information above, even though both are per-locale.

1. **Read current state** — `scripts/get_app_store_version_info.py
   --app-id APPID [--platform IOS]` prints the editable version's
   number/state and every locale's description/promotionalText/
   keywords/whatsNew/marketingUrl/supportUrl.
2. **Write** — `scripts/set_app_store_version_info.py --app-id APPID
   --locale en-US [--description ... | --description-file PATH]
   [--promotional-text ...] [--keywords ...] [--whats-new ...]
   [--marketing-url ...] [--support-url ...] [--dry-run]`. Use
   `--description-file` for anything long/multi-line — avoids
   shell-quoting issues with `&`, quotes, newlines. Always `--dry-run`
   first. Repeat once per locale.
3. `whatsNew` isn't shown by App Store Connect for an app's first-ever
   version (Apple doesn't expose the field until v1.0.1+) — don't pass
   it for a brand new app's first submission.

## Subscription offer codes (promo links / QR)

Free-trial offer code + shared custom code, redeemable at
`https://apps.apple.com/redeem?ctx=offercodes&id=APPID&code=CODE` (works as a
QR: scan -> redeem sheet -> install app if missing).

1. **Create** — `scripts/create_offer_code.py --product-id PRODUCT_ID --name
   "Reference name" --custom-code CODE [--duration THREE_MONTHS]
   [--eligibility NEW] [--offer-eligibility REPLACE_INTRO_OFFERS]
   [--limit 10000] [--expires YYYY-MM-DD] [--sandbox-test-codes N]
   [--qr-out promo.png] [--dry-run]`. Resolves the subscription's
   territories and adds a free-trial price entry per territory. Idempotent
   on `--name`. Always `--dry-run` first — a live offer cannot be deleted,
   only deactivated.
2. **List / switch off** — `scripts/toggle_offer_code.py --list`, then
   `--deactivate-custom-code ID` (stop new redemptions) or
   `--deactivate-offer ID` (whole offer). Treat deactivation as permanent.
3. **TestFlight testing** — `--sandbox-test-codes N` creates SANDBOX
   one-time codes; fetch them with `toggle_offer_code.py --sandbox-values
   BATCH_ID` (generated async, retry if not ready). Custom codes are
   production-only.
4. QR PNG needs the optional `qrcode` package
   (`$HOME/.claude/skills/.venv/bin/pip install 'qrcode[pil]'`).

## Clone/migrate app data to a different app record

### Subscriptions
1. **Export** — `scripts/export_subscriptions.py` against the old app ->
   `subscriptions_export.json`. Show the user a quick summary
   (group/subscription counts) and have them sanity-check it — their only
   chance to catch something they meant to retire before it copies forward.
2. **Dry run** — `scripts/import_subscriptions.py --dry-run` (add
   `--with-prices` to also preview price resolution). Prints payloads,
   makes no writes.
3. **Import for real** — same command without `--dry-run`. Creates
   subscription groups, subscriptions, localizations. Add `--with-prices`
   to also resolve and apply prices (matched by territory + customerPrice
   against the new subscription's own price points — see
   `references/api.md`). Introductory/promotional offers are still manual.

### One-time IAPs + App Info
4. **Export** — `scripts/export_metadata.py` against the old app ->
   `metadata_export.json`. Covers app name/subtitle/category/
   privacyPolicyUrl and non-subscription in-app purchases.
5. **Dry run then import** — `scripts/import_metadata.py --dry-run`, then
   for real, both optionally with `--with-prices`. App Information is
   PATCHed onto the new app's auto-created appInfo record (not created
   fresh); pass `--skip-app-info` to migrate only the IAPs.

### Verify
6. `scripts/verify_migration.py` compares the new app's actual state
   against the subscription export and reports pass/fail per check. This
   is the test-case mechanism the user asked for — it hits the real API,
   so encourage running the whole workflow against a sandbox/test app
   record first before touching a real one. (Currently checks
   subscriptions only; for IAPs/app info, spot-check
   `metadata_migration_result.json`, `scripts/get_app_info.py`, and the
   App Store Connect UI.)

7. **Report remaining manual steps** from `references/api.md` under
   "Things this skill does NOT automate."

## Verifying a migration against a sandbox/test app specifically

If the user doesn't have a disposable test app record, suggest creating
one (or using a low-stakes existing test app) so `verify_migration.py` can
run destructively without risk. The natural test sequence is:
export from real old app -> import into throwaway test app -> verify ->
once satisfied the scripts work, run import against the real new app ->
verify again.

## Read before running scripts

Always read `references/api.md` first — it has the price-migration caveat,
current-docs-check reminder, and the full list of what isn't automated.
Apple changes this API over time; if any script fails with an unexpected
4xx, web_search/web_fetch the current App Store Connect API docs for that
endpoint rather than guessing at a fix.
