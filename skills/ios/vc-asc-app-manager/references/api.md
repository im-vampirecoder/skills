# App Store Connect API notes

Apple revises this API regularly. Before running against a real app, verify
current endpoint paths and required fields against the live docs:
https://developer.apple.com/documentation/appstoreconnectapi/managing-in-app-purchases
(web_search / web_fetch these if unsure — do not assume the paths in this
skill's scripts are still exactly correct).

## Auth
- Requires an App Store Connect API key with **Admin or App Manager** role
  (Developer/Marketing roles can read but not create subscriptions or
  write App Information).
- Key is account-scoped, not app-scoped — the same key works for every
  app visible to the account, including both the old and new app records
  in a clone/migrate job.
- JWT expires after 20 minutes; `asc_auth.py` regenerates a fresh token
  per script run, so nothing needs to be cached.

## Listing apps and reading/writing App Information on a single app
No source/target pair required for this — `list_apps.py`,
`get_app_info.py`, and `set_app_info.py` all just need `--app-id`.
- `GET /v1/apps` lists every app the key can see (id, bundleId, name,
  sku, primaryLocale) — used by `list_apps.py` to find an app id.
- `GET /v1/apps/{id}/appInfos` returns the app's appInfo record(s). A
  freshly-created app has exactly one, editable. Once a version has gone
  live there may be a second one with `appStoreState: READY_FOR_SALE`,
  which is read-only history, not the one to edit —
  `set_app_info.py::find_editable_app_info` filters that out.
- `GET /v1/appInfos/{id}/appInfoLocalizations` / `POST
  /v1/appInfoLocalizations` / `PATCH /v1/appInfoLocalizations/{id}` —
  the localizable fields (`name`, `subtitle`, `privacyPolicyUrl`) live
  here, one record per locale. `set_app_info.py` checks whether a
  localization for the target locale already exists and PATCHes it if
  so, POSTs a new one otherwise (`name` is the only field Apple requires
  on a new localization).
- `PATCH /v1/appInfos/{id}` with `relationships.primaryCategory` /
  `secondaryCategory` — category is not localizable, it's set once on
  the appInfo itself, referencing an `appCategories` id (e.g.
  `HEALTH_AND_FITNESS`, `PHOTO_AND_VIDEO`). List valid ids via
  `GET /v1/appCategories` or see
  https://developer.apple.com/documentation/appstoreconnectapi/appcategory.
- There is no bulk "set for every locale/territory" endpoint for any of
  this — each locale needs its own PATCH/POST call.

## Price migration (now automated via --with-prices, still read this first)
Price point IDs are **not portable** — they are composite, resource-scoped
strings (e.g. base64-encoded `{subscriptionId, territory, priceTier}`).
`resolve_prices.py` re-resolves each exported (territory, customerPrice)
pair against the *new* subscription's or IAP's own price points:
1. `GET /v1/subscriptions/{id}/pricePoints?filter[territory]=USA` (or
   `/v1/inAppPurchases/{id}/pricePoints` for one-time IAPs) to list that
   resource's valid price points for one territory at a time.
2. Match by exact `customerPrice`, falling back to closest numeric value.
3. Apply it — subscriptions via `PATCH /v1/subscriptions/{id}` with an
   included `subscriptionPrices` object referencing the matched
   `subscriptionPricePoint`; one-time IAPs via
   `POST /v1/inAppPurchasePriceSchedules` with an included
   `inAppPurchasePrices` object referencing the matched
   `inAppPurchasePricePoint`.
This calls the price-points endpoint once per territory per
subscription/IAP — for an app with many territories priced individually
this is a lot of requests; Apple's own forums confirm there's no bulk
"set for all 175 territories" endpoint (auto-generated foreign pricing
from a single price only happens via the App Store Connect **website**,
not the API). Run `--dry-run --with-prices` first and read the printed
match for each territory before applying for real — this part of the API
is thinly documented and worth double-checking against
developer.apple.com if anything looks off.

## Introductory offers / promotional offers
NOT migrated by this skill (still a manual step). They reference price
points the same way regular prices do, via
`POST /v1/subscriptionIntroductoryOffers`, and — per Apple's own
developer forums — must be created once per territory; there is no
documented bulk-apply-to-all-territories option.

## App Information (name/subtitle/category)
`export_metadata.py` / `import_metadata.py` cover this via `appInfos` +
`appInfoLocalizations`. Apple creates one `appInfo` record automatically
when a new app record is created, so the importer PATCHes that existing
record rather than creating a new one — it does not create a brand new
appInfo.

## One-time (non-subscription) in-app purchases
Covered via the `/v2/inAppPurchases` + `inAppPurchaseLocalizations`
endpoints. Same price-point caveat as subscriptions applies; use
`--with-prices` on `import_metadata.py` to resolve and apply them.

## Sandbox testing after migration
- Metadata changes can take up to ~1 hour to propagate to the sandbox
  environment after creation — don't test immediately.
- Sandbox purchases are tied to the bundle ID they were made under; old
  sandbox transactions won't validate against the new app.
- Use a fresh sandbox Apple ID (Users and Access > Sandbox Testers) to
  avoid stale subscription state from the old app interfering with tests.

## App Store Version localization (description, promo text, keywords, marketing/support URL)
Covered by `get_app_store_version_info.py` / `set_app_store_version_info.py`.
Distinct resource from App Information (`appInfos`/`appInfoLocalizations`)
even though both are per-locale — this is `appStoreVersions` /
`appStoreVersionLocalizations`, versioned and tied to whichever version is
currently open for edits (not `READY_FOR_SALE`).
- `GET /v1/apps/{id}/appStoreVersions` — list versions; filter
  `appStoreState != READY_FOR_SALE` to find the editable one.
- `GET /v1/appStoreVersions/{id}/appStoreVersionLocalizations` /
  `PATCH /v1/appStoreVersionLocalizations/{id}` (existing locale) /
  `POST /v1/appStoreVersionLocalizations` (new locale, needs
  `description` at minimum) — fields: `description` (4000 chars),
  `promotionalText` (170 chars), `keywords` (100 bytes,
  comma-separated), `whatsNew` (4000 chars), `marketingUrl`,
  `supportUrl`.
- `whatsNew` is not shown/required by App Store Connect for an app's
  first-ever version — Apple only exposes it from v1.0.1+ onward.
- `promotionalText` is the one field editable without triggering a new
  App Review (per Apple's docs) — the others require a new build/version
  submission to take effect on the live listing.

## Things this skill does NOT automate
- App Store promotion ordering (promoted in-app purchases list)
- Screenshots, app previews (no write endpoint via this skill)
- Introductory offers, promotional offers (offer codes: see the vc-asc-offer-codes skill)
- App Privacy details, age rating, App Store availability/territory list
- TestFlight groups/testers, Game Center, other capabilities
- App Store Server Notifications V2 endpoint URL (must be manually pointed
  at whatever service handles the new app's notifications)
- Submitting anything for App Review (separate step, only needed once
  you're ready to ship)
