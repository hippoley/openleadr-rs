#!/usr/bin/env python3
"""Regression tests for assurance-profile validation and compilation boundaries."""
import json
import tempfile
import unittest
from pathlib import Path

from compile_assurance_probes import compile_profile
from validate_assurance_profiles import validate

HERE = Path(__file__).parent


class AssuranceProfileBoundaryTests(unittest.TestCase):
    def test_repository_profiles_validate(self):
        for name in ("protocol-assurance-profile.json", "gateway-api-assurance-profile.json"):
            self.assertEqual([], validate(HERE / name))

    def test_gateway_mixed_scope_never_emits_ready_normative_probe(self):
        compiled = compile_profile(HERE / "gateway-api-assurance-profile.json")
        self.assertTrue(compiled["probe_plans"])
        self.assertTrue(all(plan.get("status") in {"blocked", "implementation-regression-only"} for plan in compiled["probe_plans"]))

    def test_mixed_scope_ready_oracle_fails_closed(self):
        source = json.loads((HERE / "gateway-api-assurance-profile.json").read_text())
        source["negative_oracles"][0]["conformance_readiness"] = "ready"
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            json.dump(source, handle)
            path = Path(handle.name)
        try:
            self.assertTrue(validate(path))
            with self.assertRaises(ValueError):
                compile_profile(path)
        finally:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
