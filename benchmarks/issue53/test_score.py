import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from score import load_jsonl, score, validate_dataset

class BenchmarkContractTests(unittest.TestCase):
    def setUp(self):
        self.cases = load_jsonl(pathlib.Path(__file__).with_name("cases.jsonl"))

    def test_dataset_is_unique_and_complete(self):
        self.assertEqual(len(validate_dataset(self.cases)), len(self.cases))
        self.assertGreaterEqual(len(self.cases), 10)

    def test_empty_evidence_is_zero_not_success(self):
        result = score(self.cases, [])
        self.assertEqual(result["candidate_pass"], 0)
        self.assertFalse(result["verified_closed"])

    def test_ignored_result_cannot_pass(self):
        self.assertEqual(score(self.cases, [{"id": self.cases[0]["id"],
            "status": "ignored", "runner": "cargo", "commit": "sha",
            "exit_code": 0, "trace_uri": "local://trace"}])["candidate_pass"], 0)

    def test_claim_without_trace_is_not_pass(self):
        result = score(self.cases, [{"id": self.cases[0]["id"],
            "status": "passed", "runner": "cargo", "commit": "sha", "exit_code": 0}])
        self.assertEqual(result["candidate_pass"], 0)
        self.assertEqual(len(result["invalid_pass_claims"]), 1)

    def test_unknown_and_duplicate_evidence_rejected(self):
        with self.assertRaises(ValueError):
            score(self.cases, [{"id": "fake", "status": "passed"}])
        row = {"id": self.cases[0]["id"], "status": "failed"}
        with self.assertRaises(ValueError):
            score(self.cases, [row, row])

    def test_duplicate_dataset_ids_rejected(self):
        with self.assertRaises(ValueError):
            validate_dataset(self.cases + [self.cases[0]])

if __name__ == "__main__":
    unittest.main()
