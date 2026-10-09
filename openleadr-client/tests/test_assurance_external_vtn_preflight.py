#!/usr/bin/env python3
"""Independent negative cases for the external VTN discovery adapter."""
import unittest
from preflight_external_vtn import check_base, preflight

class ExternalVtnPreflightTests(unittest.TestCase):
    def test_rejects_credentials_and_insecure_remote_http(self):
        for url in ("http://user:secret@localhost:3000/openadr3/3.1.0",
                    "http://example.org/openadr3/3.1.0",
                    "file:///tmp/vtn","https://example.org/path?token=secret"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                check_base(url)

    def test_accepts_local_discovery(self):
        base="http://127.0.0.1:3000/openadr3/3.1.0"
        def fetch(url):
            if url.endswith("/auth/server"):
                return {"tokenURL":base+"/auth/token"}
            return {"paths":{"/programs":{"get":{}},"/events":{"get":{}}}}
        self.assertTrue(preflight(base,fetch,require_openapi=True)["token_endpoint_discovered"])

    def test_rejects_missing_event_contract(self):
        base="https://example.org/openadr3/3.1.0"
        def fetch(url):
            if url.endswith("/auth/server"):
                return {"tokenURL":base+"/auth/token"}
            return {"paths":{"/programs":{"get":{}}}}
        with self.assertRaisesRegex(ValueError,"Event collection"):
            preflight(base,fetch,require_openapi=True)

    def test_standard_discovery_does_not_require_vendor_openapi(self):
        base="https://example.org/openadr3/3.1.0"
        def fetch(url):
            if url.endswith("/auth/server"):
                return {"tokenURL":base+"/auth/token"}
            raise AssertionError("non-normative OpenAPI endpoint must not be fetched")
        self.assertFalse(preflight(base,fetch)["openapi_checked"])

    def test_rejects_https_downgrade(self):
        base="https://example.org/openadr3/3.1.0"
        with self.assertRaisesRegex(ValueError,"insecure token"):
            preflight(base,lambda url:{"tokenURL":"http://example.org/auth/token"})

if __name__=="__main__":
    unittest.main()
