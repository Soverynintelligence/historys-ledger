#!/usr/bin/env python3
"""Enable Cloudflare Email Routing: family@historysledger.com → Gmail.

Requires a Cloudflare API token with:
  Account → Email Routing Addresses: Edit
  Zone → Email Routing Rules: Edit
  Zone → Email Routing Settings: Edit
  Zone → Zone: Read

Create token: https://dash.cloudflare.com/profile/api-tokens
  (use template “Edit zone DNS” is NOT enough — pick custom and add Email Routing)

Usage:
  export CLOUDFLARE_API_TOKEN='…'
  python3 scripts/setup-family-email-routing.py

After a new destination is created, Cloudflare emails Gmail a verification link —
you must click it, then re-run this script to attach the rule.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

ZONE_NAME = "historysledger.com"
DEST = "jon.deoliveira@gmail.com"
CUSTOM = "family@historysledger.com"
API = "https://api.cloudflare.com/client/v4"


def cf(token: str, path: str, method: str = "GET", body: dict | None = None) -> dict:
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        API + path,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {"raw": raw}
        print(f"HTTP {e.code} {method} {path}", file=sys.stderr)
        print(json.dumps(parsed, indent=2)[:1200], file=sys.stderr)
        sys.exit(1)


def main() -> int:
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
    if not token:
        print("Set CLOUDFLARE_API_TOKEN first.", file=sys.stderr)
        return 2

    z = cf(token, f"/zones?name={ZONE_NAME}")
    if not z.get("result"):
        print(f"Zone {ZONE_NAME} not found", file=sys.stderr)
        return 1
    zone = z["result"][0]
    zid = zone["id"]
    acct = zone["account"]["id"]
    print(f"Zone {ZONE_NAME} ({zid}) account {acct}")

    # Destination (Gmail) — may need verification email
    dests = cf(token, f"/accounts/{acct}/email/routing/addresses")
    dest_row = next(
        (d for d in (dests.get("result") or []) if d.get("email") == DEST),
        None,
    )
    if not dest_row:
        print(f"Creating destination {DEST} …")
        created = cf(
            token,
            f"/accounts/{acct}/email/routing/addresses",
            "POST",
            {"email": DEST},
        )
        dest_row = created.get("result") or {}
        print(
            f"→ Check Gmail for Cloudflare verification mail for {DEST}, "
            "click the link, then re-run this script."
        )
        if not dest_row.get("verified"):
            return 0
    else:
        print(f"Destination exists: {DEST} verified={dest_row.get('verified')}")

    if not dest_row.get("verified"):
        print(
            f"{DEST} is not verified yet. Open the Cloudflare email in Gmail, "
            "confirm, re-run."
        )
        return 0

    # Enable routing + DNS (MX/SPF)
    settings = cf(token, f"/zones/{zid}/email/routing")
    enabled = (settings.get("result") or {}).get("enabled")
    print(f"Email Routing enabled={enabled}")
    if not enabled:
        print("Enabling Email Routing + DNS records …")
        # enable endpoint
        r = cf(token, f"/zones/{zid}/email/routing/enable", "POST", {})
        print("enable →", r.get("success"), (r.get("result") or {}).get("enabled"))
        # DNS records for routing
        dns = cf(token, f"/zones/{zid}/email/routing/dns", "POST", {})
        print("dns →", dns.get("success"))

    # Rule: family@ → gmail
    rules = cf(token, f"/zones/{zid}/email/routing/rules")
    existing = None
    for rule in rules.get("result") or []:
        matchers = rule.get("matchers") or []
        for m in matchers:
            if m.get("type") == "literal" and m.get("value") == CUSTOM:
                existing = rule
                break
    if existing:
        print(f"Rule already present for {CUSTOM} (id={existing.get('id')})")
    else:
        print(f"Creating rule {CUSTOM} → {DEST}")
        body = {
            "name": "Family year public address",
            "enabled": True,
            "matchers": [{"type": "literal", "field": "to", "value": CUSTOM}],
            "actions": [{"type": "forward", "value": [DEST]}],
        }
        created = cf(token, f"/zones/{zid}/email/routing/rules", "POST", body)
        print("rule →", created.get("success"), (created.get("result") or {}).get("id"))

    print()
    print(f"Done. Mail to {CUSTOM} should forward to {DEST}.")
    print("Test: send yourself a note from another account.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
