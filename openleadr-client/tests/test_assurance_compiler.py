#!/usr/bin/env python3
"""Ensure compiler cannot bypass assurance profile validation."""
import json
import tempfile
import unittest
from pathlib import Path

from compile_assurance_probes import compile_profile


PROFILE = Path(__file__).with_name("protocol-assurance-profile.json")


class CompilerContractTests(unittest.TestCase):
    def compile_mutation(self, mutate):
        profile = json.loads(PROFILE.read_text())
        mutate(profile)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "profile.json"
            path.write_text(json.dumps(profile))
            return compile_profile(path)

    def test_real_openadr_profile_compiles(self):
        compiled = compile_profile(PROFILE)
        self.assertEqual(compiled["protocol"]["name"], "OpenADR")
        self.assertTrue(compiled["probe_plans"])

    def test_unknown_readiness_fails_closed(self):
        def mutate(profile):
            profile["negative_oracles"][0]["conformance_readiness"] = "invented"
        with self.assertRaisesRegex(ValueError, "unknown conformance_readiness"):
            self.compile_mutation(mutate)

    def test_empty_oracles_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "non-empty list"):
            self.compile_mutation(lambda p: p.update(negative_oracles=[]))

    def test_mixed_scope_ready_fails_closed(self):
        def mutate(profile):
            profile["applicability"]["profile"] = "mixed-scope-not-reportable"
        with self.assertRaisesRegex(ValueError, "mixed-scope profile cannot"):
            self.compile_mutation(mutate)

    def test_missing_rejection_boundary_fails_closed(self):
        def mutate(profile):
            del profile["negative_oracles"][0]["must_not_claim"]
        with self.assertRaisesRegex(ValueError, "must_not_claim or must_reject"):
            self.compile_mutation(mutate)


if __name__ == "__main__":
    unittest.main()
