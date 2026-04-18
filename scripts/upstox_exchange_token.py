"""
One-shot helper: exchange an Upstox OAuth authorization code for access_token.

1. Register an app at https://account.upstox.com/developer/apps
2. Open the authorization URL (see Upstox docs) in a browser, log in, approve.
3. Copy the `code` query param from the redirect URL.
4. Run:

   python scripts/upstox_exchange_token.py --code YOUR_CODE

   with UPSTOX_CLIENT_ID and UPSTOX_CLIENT_SECRET (and matching UPSTOX_REDIRECT_URI)
   in the environment.

Paste the printed access_token into `.streamlit/secrets.toml` as `upstox_access_token`.
"""

from __future__ import annotations

import argparse
import os
import sys

import requests


def main() -> None:
    parser = argparse.ArgumentParser(description="Exchange Upstox OAuth code for access token")
    parser.add_argument("--code", required=True, help="Authorization code from redirect")
    args = parser.parse_args()

    client_id = os.environ.get("UPSTOX_CLIENT_ID", "")
    client_secret = os.environ.get("UPSTOX_CLIENT_SECRET", "")
    redirect_uri = os.environ.get("UPSTOX_REDIRECT_URI", "")

    if not client_id or not client_secret or not redirect_uri:
        print(
            "Set UPSTOX_CLIENT_ID, UPSTOX_CLIENT_SECRET, and UPSTOX_REDIRECT_URI in the environment.",
            file=sys.stderr,
        )
        sys.exit(1)

    url = "https://api.upstox.com/v2/login/authorization/token"
    resp = requests.post(
        url,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
        data={
            "code": args.code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        },
        timeout=30,
    )
    try:
        payload = resp.json()
    except Exception:
        payload = {"raw": resp.text}

    if resp.status_code >= 400:
        print("Token exchange failed:", file=sys.stderr)
        print(payload, file=sys.stderr)
        sys.exit(1)

    access = payload.get("access_token")
    if not access:
        print("Unexpected response:", payload, file=sys.stderr)
        sys.exit(1)

    print("access_token (store in .streamlit/secrets.toml):\n")
    print(access)


if __name__ == "__main__":
    main()
