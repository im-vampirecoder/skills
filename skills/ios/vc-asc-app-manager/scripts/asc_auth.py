"""
App Store Connect API authentication helper.

Reads credentials from a config file (default: ./asc_config.json in the
project root, or a path passed via --config / ASC_CONFIG env var) and
produces a signed JWT bearer token for use with the App Store Connect API.

Config file format (asc_config.json):
{
  "key_id": "ABC123DEFG",
  "issuer_id": "69a6de70-...-...-...-...",
  "private_key_path": "./AuthKey_ABC123DEFG.p8",
  "old_app_id": "1234567890",
  "new_app_id": "0987654321"
}

The private key (.p8) is downloaded once from App Store Connect
(Users and Access > Integrations > In-App Purchase or App Store Connect
API keys) and must have at least the App Manager role to read AND write
subscriptions. Never commit the .p8 file or the config file to source
control if it contains a real path someone could exfiltrate the key from.
"""
import json
import os
import time
import sys

import jwt


def load_config(config_path: str | None = None) -> dict:
    path = config_path or os.environ.get("ASC_CONFIG", "./asc_config.json")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Config file not found at {path}. Create it with key_id, issuer_id, "
            f"private_key_path, old_app_id, new_app_id. See references/api.md."
        )
    with open(path) as f:
        cfg = json.load(f)
    required = ["key_id", "issuer_id", "private_key_path"]
    missing = [k for k in required if k not in cfg]
    if missing:
        raise ValueError(f"Config missing required fields: {missing}")
    return cfg


def generate_token(cfg: dict) -> str:
    key_path = cfg["private_key_path"]
    if not os.path.exists(key_path):
        raise FileNotFoundError(f"Private key .p8 not found at {key_path}")
    with open(key_path) as f:
        private_key = f.read()

    now = int(time.time())
    payload = {
        "iss": cfg["issuer_id"],
        "iat": now,
        "exp": now + 60 * 19,  # ASC tokens max at 20 min; stay under
        "aud": "appstoreconnect-v1",
    }
    headers = {"alg": "ES256", "kid": cfg["key_id"], "typ": "JWT"}
    token = jwt.encode(payload, private_key, algorithm="ES256", headers=headers)
    return token


def get_session(config_path: str | None = None):
    """Returns (requests.Session with auth header set, cfg dict)."""
    import requests

    cfg = load_config(config_path)
    token = generate_token(cfg)
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {token}"})
    return session, cfg


if __name__ == "__main__":
    # Quick self-test: just prints whether a token can be generated.
    try:
        cfg = load_config(sys.argv[1] if len(sys.argv) > 1 else None)
        tok = generate_token(cfg)
        print(f"Token generated OK ({len(tok)} chars). Issuer: {cfg['issuer_id'][:8]}...")
    except Exception as e:
        print(f"FAILED: {e}", file=sys.stderr)
        sys.exit(1)
