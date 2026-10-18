# Offer codes: Apple behaviour and integration notes

Checked against Apple's App Store Connect OpenAPI spec (October 2026). If an
endpoint returns an unexpected 4xx, re-check the current spec before guessing:
`https://developer.apple.com/sample-code/app-store-connect/app-store-connect-openapi-specification.zip`.

## Options

| Option | Values | Meaning |
|---|---|---|
| `customerEligibilities` | `NEW`, `EXISTING`, `EXPIRED` | `NEW` = Apple ID never subscribed to any product in the subscription group (anyone who used the intro trial is NOT new). `EXISTING` = currently subscribed. `EXPIRED` = lapsed. Checked per Apple ID, not per app account. |
| `offerEligibility` | `REPLACE_INTRO_OFFERS`, `STACK_WITH_INTRO_OFFERS` | Replace: the code's period instead of the intro trial. Stack: intro trial first, then the code's period. |
| `offerMode` | `FREE_TRIAL` (scripts), `PAY_AS_YOU_GO`, `PAY_UP_FRONT` | Paid modes need a `subscriptionPricePoint` per territory; not implemented here. |
| `duration` | `THREE_DAYS` ... `ONE_YEAR` | Free-trial length. `numberOfPeriods` is 1 for free trials. |
| Custom code | letters/digits, `numberOfCodes` required, `expirationDate` optional | One shared code, many redemptions up to the limit. Production only. |
| One-time codes | `numberOfCodes`, `expirationDate` required, `environment` `PRODUCTION`/`SANDBOX` | Unique codes, one redemption each. Generated async; values come back as CSV. |
| `targetSubscriptionPlanType` | `MONTHLY`, `UPFRONT` (optional) | For plans with monthly billing of an annual commitment; omitted by the scripts. |

## Endpoints used

- `POST /v1/subscriptionOfferCodes` (with `included` `subscriptionOfferCodePrices`, one per territory)
- `POST /v1/subscriptionOfferCodeCustomCodes`
- `POST /v1/subscriptionOfferCodeOneTimeUseCodes`, `GET .../{id}/values`
- `PATCH` each of the three with `{"active": false}` to deactivate
- `GET /v1/subscriptions/{id}/offerCodes`, `GET /v1/subscriptionOfferCodes/{id}/customCodes|oneTimeUseCodes`
- `GET /v1/subscriptions/{id}/subscriptionAvailability` → `.../availableTerritories`

## App and backend checklist

A code redeemed through the App Store happens **outside the app**, which
changes what the app and backend receive:

1. **Transaction claims.** `offerType` is `3` (offer code) and
   `offerDiscountType` is `FREE_TRIAL`. A backend that only treats
   `offerType == 1` (intro offer) as a trial will store the promo as a paid,
   active subscription. Treat `offerType 3 + FREE_TRIAL` as a trial, in both
   the receipt-verification path and the App Store Server Notification path.
2. **No `appAccountToken`.** It is only set by `Product.purchase(options:)`
   inside the app. The backend has to link the subscription to a user by
   `originalTransactionId`, the first time the signed-in app posts the
   transaction. Notifications that arrive before that have no user to match;
   that's expected.
3. **Redeem before sign-up.** First launch is usually signed out, so a
   `Transaction.updates` delivery can't be verified with the backend and is
   left unfinished. After sign-in, sync `Transaction.currentEntitlements` to
   the backend before showing a paywall, otherwise the user lands on the
   paywall and has to tap Restore. Only auto-claim transactions whose
   `appAccountToken` is empty or matches the signed-in user, so a shared device
   doesn't silently move another account's in-app purchase.
4. **Optional in-app entry.** `.offerCodeRedemption(isPresented:)` (SwiftUI)
   lets users type a code without leaving the app.
