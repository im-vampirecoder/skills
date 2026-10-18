# iOS

Skills for shipping and managing iOS apps through App Store Connect. All three use the same `asc_config.json` (ASC API key); `vc-asc-ios-release` and `vc-asc-offer-codes` import `vc-asc-app-manager`'s auth helper, so install them together.

## Model-invoked

- **[vc-asc-app-manager](./vc-asc-app-manager/SKILL.md)** - Read/edit App Information and version listing text, and clone subscriptions/IAPs/prices onto another app record via the App Store Connect API.
- **[vc-asc-ios-release](./vc-asc-ios-release/SKILL.md)** - Upload an `.xcarchive` to App Store Connect, wait for processing, prepare the App Store version with What's New, and submit it for App Review.
- **[vc-asc-offer-codes](./vc-asc-offer-codes/SKILL.md)** - Create free-trial subscription offer codes (shared custom code with redeem link/QR, one-time and TestFlight sandbox codes), list them, and deactivate on demand.
