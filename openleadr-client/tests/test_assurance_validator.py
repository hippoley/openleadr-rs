#!/usr/bin/env python3
"""Regression checks for malformed assurance profile structures."""
import json
import tempfile
import unittest
from pathlib import Path

from validate_assurance_profiles import validate


class FailClosedStructureTests(unittest.TestCase):
    def check_invalid(self, value, expected):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "profile.json"
            path.write_text(json.dumps(value))
            errors = validate(path)
            self.assertTrue(any(expected in error for error in errors), errors)

    def test_mixed_scope_ready_oracle_rejected(self):
        self.check_invalid({"applicability": {"profile": "mixed-scope-not-reportable"}, "negative_oracles": [{"id": "x", "must_reject": ["x"], "conformance_readiness": "ready"}]}, "mixed-scope profile cannot declare ready normative conformance")

    def test_unknown_readiness_rejected(self):
        self.check_invalid({"applicability": {}, "negative_oracles": [{"id": "x", "must_reject": ["x"], "conformance_readiness": "invented"}]}, "unknown conformance_readiness")

    def test_empty_rejection_list_rejected(self):
        self.check_invalid({"applicability": {}, "negative_oracles": [{"id": "x", "must_reject": []}]}, "must_reject must be a non-empty list of strings")

    def test_blank_rejection_string_rejected(self):
        self.check_invalid({"applicability": {}, "negative_oracles": [{"id": "x", "must_not_claim": ["  "]}]}, "must_not_claim must be a non-empty list of strings")

    def test_wrong_rejection_type_rejected(self):
        self.check_invalid({"applicability": {}, "negative_oracles": [{"id": "x", "must_reject": "reject"}]}, "must_reject must be a non-empty list of strings")

    def test_non_object_root(self):
        self.check_invalid([], "profile root must be an object")

    def test_non_object_applicability(self):
        self.check_invalid({"applicability": []}, "applicability must be an object")

    def test_empty_evidence(self):
        self.check_invalid({"applicability": {}, "evidence_surface": []}, "evidence_surface must be a non-empty list")

    def test_empty_oracles(self):
        self.check_invalid({"applicability": {}, "negative_oracles": []}, "negative_oracles must be a non-empty list")

    def test_non_object_oracle(self):
        self.check_invalid({"applicability": {}, "negative_oracles": [None]}, "negative_oracles[0] must be an object")

    def test_non_object_evidence(self):
        self.check_invalid({"applicability": {}, "evidence_surface": [None]}, "evidence_surface[0] must be an object")

    def test_non_list_implementation_evidence(self):
        self.check_invalid({"applicability": {}, "negative_oracles": [{"id": "x", "must_reject": ["x"], "implementation_evidence": {}}]}, "implementation_evidence must be a list")

    def test_non_list_evidence_boundary(self):
        self.check_invalid({"applicability": {}, "evidence_surface": [{"id": "x", "observation": "x", "supports": "x", "does_not_establish": "not a list"}]}, "must bound at least one stronger claim")

    def test_non_string_readiness(self):
        self.check_invalid({"applicability": {}, "negative_oracles": [{"id": "x", "must_reject": ["x"], "conformance_readiness": []}]}, "unknown conformance_readiness")

    def test_non_string_conformance_system(self):
        self.check_invalid({"applicability": {"conformance_system": 42}}, "applicability.conformance_system is required")


if __name__ == "__main__":
    unittest.main()
