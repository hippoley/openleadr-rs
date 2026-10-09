#!/usr/bin/env python3
"""Read-only OpenADR 3.1 external VTN discovery preflight; sends no credentials."""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


def check_base(raw):
    parsed = urllib.parse.urlsplit(raw)
    if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.username or parsed.password:
        raise ValueError("VTN URL must be an HTTP(S) origin without embedded credentials")
    if parsed.query or parsed.fragment:
        raise ValueError("VTN URL must not contain query or fragment")
    if parsed.scheme == "http" and parsed.hostname not in ("localhost", "127.0.0.1", "::1"):
        raise ValueError("plaintext HTTP is permitted only for loopback testing")
    return raw.rstrip("/")


def get_json(url):
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=8) as response:
        if response.status != 200:
            raise ValueError(f"GET {url}: unexpected status {response.status}")
        if "json" not in response.headers.get("Content-Type", "").lower():
            raise ValueError(f"GET {url}: not JSON")
        return json.load(response)


def preflight(base, fetch=get_json, require_openapi=False):
    base = check_base(base)
    auth = fetch(base + "/auth/server")
    if not isinstance(auth, dict) or not isinstance(auth.get("tokenURL"), str):
        raise ValueError("auth/server must advertise tokenURL")

    token = urllib.parse.urlsplit(auth["tokenURL"])
    target = urllib.parse.urlsplit(base)
    if token.scheme not in ("http", "https") or not token.netloc:
        raise ValueError("invalid tokenURL")
    if target.scheme == "https" and token.scheme != "https":
        raise ValueError("HTTPS VTN advertises insecure token endpoint")
    if target.hostname in ("localhost", "127.0.0.1", "::1") and token.hostname not in (
        "localhost",
        "127.0.0.1",
        "::1",
    ):
        raise ValueError("loopback VTN advertises non-loopback token endpoint")

    if require_openapi:
        # Vendor capability used by the documented candidate, not a normative requirement.
        spec = fetch(base + "/openapi.json")
        paths = spec.get("paths") if isinstance(spec, dict) else None
        if not isinstance(paths, dict):
            raise ValueError("openapi.json must contain paths")
        if not any(item.endswith("/programs") for item in paths):
            raise ValueError("OpenAPI document lacks Program collection")
        if not any(item.endswith("/events") for item in paths):
            raise ValueError("OpenAPI document lacks Event collection")

    return {
        "target": base,
        "token_endpoint": auth["tokenURL"],
        "token_endpoint_discovered": True,
        "openapi_checked": require_openapi,
        "note": "Read-only discovery only; not interoperability or certification.",
    }


if __name__ == "__main__":
    try:
        url = os.environ.get("OPENLEADR_RS_VTN_URL") or os.environ.get("OPENADR_VTN_URL")
        if not url:
            raise ValueError("OPENLEADR_RS_VTN_URL or OPENADR_VTN_URL required")
        print(
            json.dumps(
                preflight(
                    url,
                    require_openapi=os.environ.get("OPENLEADR_RS_REQUIRE_OPENAPI") == "1",
                ),
                indent=2,
            )
        )
    except (ValueError, urllib.error.URLError, TimeoutError, KeyError, TypeError) as exc:
        print(f"external VTN preflight failed: {exc}", file=sys.stderr)
        sys.exit(1)
