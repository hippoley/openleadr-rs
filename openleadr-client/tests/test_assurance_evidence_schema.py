#!/usr/bin/env python3
"""Regression cases for bounded external-VTN evidence claims."""
import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator


SCHEMA_PATH = Path(__file__).with_name("external-vtn-evidence.schema.json")
SCHEMA = json.loads(SCHEMA_PATH.read_text())
VALIDATOR = Draft202012Validator(SCHEMA)


def base_artifact():
    return {
        "schema_version": "0.6.0",
        "source_commit": "a" * 40,
        "vtn": {"implementation": "independent-example", "version": "1.0", "deployment": "independent"},
        "runner": {"rust_version": "1.91", "os": "linux"},
        "tests": [
            {"name": "program_crud", "command": "cargo test --test program program_crud -- --exact", "exit_code": 0},
            {"name": "event_crud", "command": "cargo test --test event event_crud -- --exact", "exit_code": 0}
        ],
        "cleanup": {"verified": True, "remaining_resources": 0},
        "fault_injection": [
            {"name": "program_post_create_panic", "command": "OPENLEADR_RS_INJECT_FAILURE_AFTER_CREATE=1 cargo test --test program program_crud -- --exact", "expected_nonzero_exit": True, "observed_exit_code": 101, "cleanup_verified": True, "remaining_resources": 0},
            {"name": "event_post_create_panic", "command": "OPENLEADR_RS_INJECT_FAILURE_AFTER_CREATE=1 cargo test --test event event_crud -- --exact", "expected_nonzero_exit": True, "observed_exit_code": 101, "cleanup_verified": True, "remaining_resources": 0}
        ],
        "claim": "independent-vtn-crud",
        "effect_verification": [{
            "operation": "create", "resource_type": "Program", "resource_id": "run-scoped-id",
            "observation": "read-after-write", "verified": True, "verdict": "matched",
            "attribution": "bounded", "pre_action_observation": True, "operation_correlation": "run-123:create:program"
        }]
    }


class EvidenceClaimTests(unittest.TestCase):
    def assert_valid(self, evidence):
        errors = list(VALIDATOR.iter_errors(evidence))
        self.assertEqual([], errors, [e.message for e in errors])

    def assert_invalid(self, evidence):
        self.assertTrue(list(VALIDATOR.iter_errors(evidence)), evidence)

    def test_valid_bounded_claim(self):
        self.assert_valid(base_artifact())

    def test_strong_claim_rejects_missing_event_crud(self):
        evidence = base_artifact()
        evidence["tests"] = [evidence["tests"][0]]
        self.assert_invalid(evidence)

    def test_strong_claim_rejects_missing_event_fault_injection(self):
        evidence = base_artifact()
        evidence["fault_injection"] = [evidence["fault_injection"][0]]
        self.assert_invalid(evidence)

    def test_strong_claim_rejects_duplicate_program_instead_of_event(self):
        evidence = base_artifact()
        evidence["tests"][1] = copy.deepcopy(evidence["tests"][0])
        self.assert_invalid(evidence)

    def test_strong_claim_rejects_failed_test(self):
        evidence = base_artifact()
        evidence["tests"][0]["exit_code"] = 1
        self.assert_invalid(evidence)

    def test_strong_claim_rejects_second_failed_test(self):
        evidence = base_artifact()
        evidence["tests"].append({"name": "event_crud", "command": "cargo test", "exit_code": 101})
        self.assert_invalid(evidence)

    def test_strong_claim_rejects_in_tree_vtn(self):
        evidence = base_artifact()
        evidence["vtn"]["deployment"] = "in-tree"
        self.assert_invalid(evidence)

    def test_strong_claim_rejects_unverified_cleanup(self):
        evidence = base_artifact()
        evidence["cleanup"]["verified"] = False
        self.assert_invalid(evidence)

    def test_strong_claim_rejects_unattributed_effect(self):
        evidence = base_artifact()
        evidence["effect_verification"][0]["attribution"] = "unattributed"
        self.assert_invalid(evidence)

    def test_strong_claim_rejects_missing_operation_correlation(self):
        evidence = base_artifact()
        del evidence["effect_verification"][0]["operation_correlation"]
        self.assert_invalid(evidence)

    def test_strong_claim_rejects_empty_operation_correlation(self):
        evidence = base_artifact()
        evidence["effect_verification"][0]["operation_correlation"] = ""
        self.assert_invalid(evidence)

    def test_strong_claim_rejects_missing_fault_injection(self):
        evidence = base_artifact()
        del evidence["fault_injection"]
        self.assert_invalid(evidence)

    def test_strong_claim_rejects_fault_injection_cleanup_failure(self):
        evidence = base_artifact()
        evidence["fault_injection"][0]["cleanup_verified"] = False
        self.assert_invalid(evidence)

    def test_strong_claim_rejects_fault_injection_residue(self):
        evidence = base_artifact()
        evidence["fault_injection"][0]["remaining_resources"] = 1
        self.assert_invalid(evidence)

    def test_fault_injection_must_observe_nonzero_exit(self):
        evidence = base_artifact()
        evidence["fault_injection"][0]["observed_exit_code"] = 0
        self.assert_invalid(evidence)

    def test_execution_only_may_record_failed_test(self):
        evidence = base_artifact()
        evidence["claim"] = "execution-only"
        evidence["tests"][0]["exit_code"] = 1
        self.assert_valid(evidence)


if __name__ == "__main__":
    unittest.main()
