"""
Shared logic to resolve exported (territory, customerPrice) pairs into real
price point IDs on a NEW app/subscription/IAP, and submit them.

Price point IDs are subscription/IAP-scoped composite strings — they are
NOT portable between apps or even between two different subscriptions.
This is why prices can't just be copied: every price must be re-resolved
against the target resource's own available price points, matched by
territory + customer price.

Payload shapes below are based on Apple's documented schema plus
confirmed working examples from Apple's own developer forums (this part
of the API is notoriously under-documented — verify against
developer.apple.com if a request fails with an unexpected 4xx/5xx).
"""
import base64
import json
import sys


def encode_price_point_id(subscription_id, territory, tier):
    """Inverse of the tier decoding in export_subscriptions.py. Price point ids
    are base64 JSON {"s": subscriptionId, "t": territory, "p": tier} and the
    tier->customerPrice mapping is universal per territory across subscriptions
    and apps (confirmed live) — so the new subscription's own price point for
    a given territory+tier can be constructed directly, no pagination needed."""
    raw = json.dumps({"s": str(subscription_id), "t": territory, "p": tier}, separators=(",", ":"))
    return base64.b64encode(raw.encode()).decode().rstrip("=")


def get_price_points(session, base, kind, resource_id, territory, dry_run=False):
    """kind: 'subscription' or 'iap'. Returns list of price point dicts
    with id + attributes.customerPrice for the given territory.
    Paginates fully — Apple returns ~50 per page out of ~800 total per
    territory, and a partial (first-page-only) list silently produces the
    wrong "closest" match instead of an error. Only used as a fallback when
    a priceTier isn't available in the export (see encode_price_point_id)."""
    if kind == "subscription":
        url = f"{base}/subscriptions/{resource_id}/pricePoints"
    else:
        url = f"{base}/inAppPurchases/{resource_id}/pricePoints"
    if dry_run:
        print(f"  [dry-run] GET {url} territory={territory}")
        # Fabricate a single matching point so the dry-run can still show
        # the downstream POST/PATCH payload shape.
        return [{"id": "DRY_RUN_PRICE_POINT", "attributes": {"customerPrice": "0"}}]
    points = []
    params = {"filter[territory]": territory}
    while url:
        resp = session.get(url, params=params)
        params = None
        resp.raise_for_status()
        body = resp.json()
        points.extend(body.get("data", []))
        url = body.get("links", {}).get("next")
    return points


def find_closest_price_point(price_points, target_price):
    """Match by exact customerPrice string first, else closest numeric."""
    exact = [p for p in price_points if p["attributes"].get("customerPrice") == target_price]
    if exact:
        return exact[0]
    try:
        target = float(target_price)
        by_diff = sorted(
            price_points, key=lambda p: abs(float(p["attributes"]["customerPrice"]) - target)
        )
        return by_diff[0] if by_diff else None
    except (ValueError, TypeError):
        return price_points[0] if price_points else None


def apply_prices(session, base, kind, resource_id, exported_prices, dry_run):
    """
    exported_prices: list of dicts with at least 'territory' and
    'customerPrice' (as captured from the export).
    Returns (n_applied, n_failed).
    """
    n_ok, n_fail = 0, 0
    for price in exported_prices:
        territory = price.get("territory")
        target = price.get("customerPrice")
        if not territory or target is None:
            n_fail += 1
            continue

        tier = price.get("priceTier")
        if tier is not None and not dry_run and kind == "subscription":
            match = {"id": encode_price_point_id(resource_id, territory, tier)}
        else:
            points = get_price_points(session, base, kind, resource_id, territory, dry_run=dry_run)
            match = find_closest_price_point(points, target)
        if not match:
            print(f"  no price point found for territory={territory} target={target}", file=sys.stderr)
            n_fail += 1
            continue

        # JSON:API inline-creation local ids must be wrapped as "${...}" — a bare
        # string like "NEW_PRICE" is rejected with ENTITY_ERROR.INCLUDED.INVALID_ID
        # ("must be a local id with the format '${local-id}'"), confirmed live.
        local_id = "${NEW_PRICE}"

        if kind == "subscription":
            payload = {
                "data": {
                    "type": "subscriptions",
                    "id": resource_id,
                    "relationships": {
                        "prices": {"data": [{"type": "subscriptionPrices", "id": local_id}]}
                    },
                },
                "included": [
                    {
                        "type": "subscriptionPrices",
                        "id": local_id,
                        "attributes": {"preserveCurrentPrice": False},
                        "relationships": {
                            "subscriptionPricePoint": {
                                "data": {"type": "subscriptionPricePoints", "id": match["id"]}
                            },
                            "subscription": {"data": {"type": "subscriptions", "id": resource_id}},
                        },
                    }
                ],
            }
            url = f"{base}/subscriptions/{resource_id}"
            method = "PATCH"
        else:
            payload = {
                "data": {
                    "type": "inAppPurchasePriceSchedules",
                    "relationships": {
                        "inAppPurchase": {"data": {"type": "inAppPurchases", "id": resource_id}},
                        "manualPrices": {
                            "data": [{"type": "inAppPurchasePrices", "id": local_id}]
                        },
                    },
                },
                "included": [
                    {
                        "type": "inAppPurchasePrices",
                        "id": local_id,
                        "attributes": {"startDate": None},
                        "relationships": {
                            "inAppPurchaseV2": {"data": {"type": "inAppPurchases", "id": resource_id}},
                            "inAppPurchasePricePoint": {
                                "data": {"type": "inAppPurchasePricePoints", "id": match["id"]}
                            },
                        },
                    }
                ],
            }
            url = f"{base}/inAppPurchasePriceSchedules"
            method = "POST"

        if dry_run:
            print(f"  [dry-run] {method} {url} territory={territory} -> price point {match['id']}")
            n_ok += 1
            continue

        resp = session.request(method, url, json=payload)
        if not resp.ok:
            print(f"  FAILED {territory}: {resp.status_code} {resp.text[:300]}", file=sys.stderr)
            n_fail += 1
        else:
            n_ok += 1

    return n_ok, n_fail
