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


if __name__ == "__main__":
    unittest.main()
