---
name: vc-asc-offer-codes
description: Create and manage App Store subscription offer codes via the App Store Connect API - a free-trial offer (e.g. 3 months free) on an auto-renewable subscription, a shared custom code with a redeem link / QR code, production one-time-use codes, and SANDBOX codes for TestFlight testing; list offers, fetch code values, and deactivate a code or offer on demand. Use when the user wants a promo link or QR that installs the app and grants a free period, asks to "create an offer code", "make a promo code", "give users N months free", "generate redemption codes", "test offer codes in TestFlight", or "turn off / stop the promo code". For app metadata, subscriptions or IAP migration use vc-asc-app-manager; for builds and review use vc-asc-ios-release.
---

# App Store Offer Codes

Creates free-trial **subscription offer codes** through the App Store Connect
API, with the same `.p8` API key and `asc_config.json` as `vc-asc-app-manager`.
Authentication is reused from that sibling skill (`../vc-asc-app-manager/scripts/asc_auth.py`),
so install both.

A redeemed code opens Apple's redemption sheet, prompts to install the app if
missing, and starts the subscription at $0 for the offer period; it then renews
at the normal price unless cancelled. Link format:
`https://apps.apple.com/redeem?ctx=offercodes&id={APP_ID}&code={CODE}`.

## Before running anything

1. Need an ASC API key (Admin or App Manager) and `asc_config.json` with
   `key_id`, `issuer_id`, `private_key_path`, optionally `app_id` (or
   `new_app_id`) as the default app. See `vc-asc-app-manager` for the format.
   Never print or commit the `.p8` or the config.
2. Run scripts with the skills venv:
   `$HOME/.claude/skills/.venv/bin/python3 <skill>/scripts/<script>.py`
   (needs `PyJWT`, `requests`; QR PNGs also need `qrcode[pil]`).
3. Pin down with the user, if not already given: which subscription product,
   offer duration, who is eligible, stack with or replace the intro trial,
   custom code text, redemption limit, expiry. Read
   [references/offer-codes.md](references/offer-codes.md) for what each option
   means in Apple's terms.

## Create

```bash
scripts/create_offer_code.py --product-id com.example.monthly \
  --name "Spring promo 3M free" --custom-code SPRING3M \
  [--duration THREE_MONTHS] [--eligibility NEW] [--offer-eligibility REPLACE_INTRO_OFFERS] \
  [--limit 10000] [--expires YYYY-MM-DD] \
  [--one-time-codes N [--one-time-expires YYYY-MM-DD]] \
  [--sandbox-test-codes N] [--qr-out promo.png] \
  [--app-id ID | --bundle-id BID] [--config PATH] --dry-run
```

- **Always `--dry-run` first** and show the user the payloads. A live offer
  can't be edited or deleted, only deactivated. Get explicit approval before
  the real run.
- Resolves the subscription's sale territories and adds a free-trial price
  entry for each one.
- Idempotent on `--name`: an existing offer with the same terms is reused, and
  an existing custom code isn't created twice. Same name with different terms
  stops with an error.
- Free trials only (`FREE_TRIAL`). Paid discount modes need a price point per
  territory and aren't implemented.

## Manage

```bash
scripts/manage_offer_codes.py --list                         # offers, custom codes, batches, redeem URLs
scripts/manage_offer_codes.py --codes BATCH_ID --out codes.csv   # one-time code values (async; retry if not ready)
scripts/manage_offer_codes.py --qr SPRING3M --out promo.png  # QR for an existing custom code
scripts/manage_offer_codes.py --deactivate-custom-code ID [--dry-run]   # stop the shared code
scripts/manage_offer_codes.py --deactivate-codes BATCH_ID [--dry-run]   # stop a one-time batch
scripts/manage_offer_codes.py --deactivate-offer ID [--dry-run]         # stop the whole offer
```

Deactivation stops new redemptions immediately; people who already redeemed
keep their free period. Confirm with the user before deactivating.

## Testing

- Custom codes and PRODUCTION one-time codes only redeem against the live App
  Store app. For TestFlight, create `--sandbox-test-codes N`, fetch them with
  `--codes`, and redeem in the TestFlight build (e.g. via
  `.offerCodeRedemption(isPresented:)` or the redeem URL on a sandbox account).
- New codes can take up to about an hour to become redeemable.

## After creating

Tell the user the redeem URL, the offer/code ids (for later deactivation), and
check the app and backend handle offer-code transactions. The checklist is in
[references/offer-codes.md](references/offer-codes.md#app-and-backend-checklist):
`offerType` 3, no `appAccountToken`, and linking by `originalTransactionId`.
