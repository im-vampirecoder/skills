"""
Read-only: print the current App Information state for a single app —
category, and per-locale name/subtitle/privacyPolicyUrl. Use this before
set_app_info.py to see what's already set and which locales exist, and
after it to confirm the write took effect.

Usage:
    python get_app_info.py --app-id APPID [--config PATH]
"""
import argparse
import json
import sys

from asc_auth import get_session
from export_metadata import export_app_info

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=None)
    parser.add_argument("--app-id", required=True)
    args = parser.parse_args()

    session, cfg = get_session(args.config)
    info = export_app_info(session, args.app_id)

    if not info:
        print(f"No appInfo record found for app {args.app_id}.", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(info, indent=2))
