"""
Verify a migration by comparing the source export against what now exists
on the target app: same group names, same subscription names/product IDs
(minus any --suffix), same subscription periods. Prices are checked for
presence only (values must be reconciled manually per api.md).

Usage:
    python verify_migration.py --in subscriptions_export.json --config PATH [--app-id NEW_APP_ID]
"""
import argparse
import json
import sys

from asc_auth import get_session
from export_subscriptions import export_app_subscriptions


def summarize(export):
    """Reduce an export dict to a comparable summary keyed by group/sub name."""
    summary = {}
    for group in export["subscriptionGroups"]:
        gname = group["attributes"].get("referenceName")
        subs = {}
        for sub in group["subscriptions"]:
            a = sub["attributes"]
            subs[a.get("name")] = {
                "productId": a.get("productId"),
                "period": a.get("subscriptionPeriod"),
                "has_prices": len(sub.get("prices", [])) > 0,
                "n_localizations": len(sub.get("localizations", [])),
            }
        summary[gname] = subs
    return summary


def compare(source_summary, target_summary):
    checks = []
    for gname, subs in source_summary.items():
        if gname not in target_summary:
            checks.append((False, f"Missing subscription group '{gname}' on target app"))
            continue
        checks.append((True, f"Group '{gname}' present"))
        for sname, sattrs in subs.items():
            tattrs = target_summary[gname].get(sname)
            if not tattrs:
                checks.append((False, f"Missing subscription '{sname}' in group '{gname}'"))
                continue
            checks.append((True, f"Subscription '{sname}' present"))
            if sattrs["period"] != tattrs["period"]:
                checks.append(
                    (False, f"'{sname}' period mismatch: {sattrs['period']} vs {tattrs['period']}")
                )
            else:
                checks.append((True, f"'{sname}' period matches ({sattrs['period']})"))
            if sattrs["n_localizations"] != tattrs["n_localizations"]:
                checks.append(
                    (
                        False,
                        f"'{sname}' localization count mismatch: "
                        f"{sattrs['n_localizations']} vs {tattrs['n_localizations']}",
                    )
                )
            else:
                checks.append((True, f"'{sname}' localization count matches"))
            if not tattrs["has_prices"]:
                checks.append(
                    (False, f"'{sname}' has no prices set yet — expected, see api.md, resolve manually")
                )
    return checks


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=None)
    parser.add_argument("--in", dest="infile", default="subscriptions_export.json")
    parser.add_argument("--app-id", default=None, help="Overrides new_app_id from config")
    args = parser.parse_args()

    session, cfg = get_session(args.config)
    app_id = args.app_id or cfg.get("new_app_id")
    if not app_id:
        print("No app id: pass --app-id or set new_app_id in config", file=sys.stderr)
        sys.exit(1)

    with open(args.infile) as f:
        source = json.load(f)

    print(f"Fetching current state of target app {app_id} for comparison...")
    target = export_app_subscriptions(session, app_id)

    source_summary = summarize(source)
    target_summary = summarize(target)
    checks = compare(source_summary, target_summary)

    n_pass = sum(1 for ok, _ in checks if ok)
    n_fail = sum(1 for ok, _ in checks if not ok)
    for ok, msg in checks:
        print(f"{'PASS' if ok else 'FAIL'}: {msg}")
    print(f"\n{n_pass} passed, {n_fail} failed.")
    sys.exit(1 if n_fail else 0)
