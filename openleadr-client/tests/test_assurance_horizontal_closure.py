#!/usr/bin/env python3
"""Independent counterexamples for the story-closure validator."""
import copy
import json
import unittest
from pathlib import Path
from validate_user_story_matrix import validate

DATA = json.loads(Path(__file__).with_name("user-story-horizontal-matrix.json").read_text())


class HorizontalClosureTests(unittest.TestCase):
    def test_baseline_is_structurally_valid(self):
        self.assertEqual([], validate(DATA))

    def test_unverified_story_cannot_be_closed(self):
        data = copy.deepcopy(DATA)
        data["stories"][0]["status"] = "VERIFIED_CLOSED"
        self.assertTrue(validate(data))

    def test_fake_evidence_does_not_bypass_two_layer_gate(self):
        data = copy.deepcopy(DATA)
        story = data["stories"][0]
        story["status"] = "VERIFIED_CLOSED"
        story["evidence"] = ["fake-log"]
        story["independent_acceptance"] = "self-asserted"
        self.assertTrue(validate(data))

    def test_missing_story_is_rejected(self):
        data = copy.deepcopy(DATA)
        data["stories"].pop()
        self.assertTrue(validate(data))

    def test_cycle_is_rejected(self):
        data = copy.deepcopy(DATA)
        data["stories"][0]["depends_on"] = ["US-07"]
        self.assertTrue(any("cycle" in e for e in validate(data)))

    def test_na_without_reason_is_rejected(self):
        data = copy.deepcopy(DATA)
        data["stories"][11]["dimensions"]["performance"]["reason"] = ""
        self.assertTrue(validate(data))


if __name__ == "__main__":
    unittest.main()
