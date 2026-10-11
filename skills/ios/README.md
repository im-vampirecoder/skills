# iOS

Skills for shipping and managing iOS apps through App Store Connect. Both use the same `asc_config.json` (ASC API key); `vc-asc-ios-release` imports `vc-asc-app-manager`'s auth helper, so install them together.

## Model-invoked

- **[vc-asc-app-manager](./vc-asc-app-manager/SKILL.md)** - Read/edit App Information and version listing text, create offer codes, and clone subscriptions/IAPs/prices onto another app record via the App Store Connect API.
- **[vc-asc-ios-release](./vc-asc-ios-release/SKILL.md)** - Upload an `.xcarchive` to App Store Connect, wait for processing, prepare the App Store version with What's New, and submit it for App Review.
