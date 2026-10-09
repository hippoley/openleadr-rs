#!/usr/bin/env python3
"""Strict offline manifest validator and evidence scorer for Issue #53.

A manifest is NOT an execution report. Missing/ignored evidence earns zero.
Run: python3 benchmarks/issue53/score.py [results.jsonl]
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
FIELDS = {"id", "story", "area", "mode", "expected", "gate", "claim",
          "evidence_required", "dataset_version"}
ALLOWED_GATES = {"local", "external", "fault", "concurrency"}

def load_jsonl(path):
    records = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{number}: malformed JSON: {exc}") from exc
        if not isinstance(record, dict):
            raise ValueError(f"{path}:{number}: expected an object")
        records.append(record)
    return records

def validate_dataset(cases):
    if not cases:
        raise ValueError("empty benchmark dataset")
    ids = set()
    for case in cases:
        if set(case) != FIELDS:
            raise ValueError(f"unexpected/missing fields for {case.get('id')}")
        if not isinstance(case["id"], str) or not case["id"]:
            raise ValueError("case id must be nonempty")
        if case["id"] in ids:
            raise ValueError(f"duplicate case id: {case['id']}")
        ids.add(case["id"])
        if case["gate"] not in ALLOWED_GATES:
            raise ValueError(f"unknown gate: {case['gate']}")
        if case["mode"] not in {"readonly", "mutation"}:
            raise ValueError("unknown mode")
        if case["mode"] == "mutation" and case["gate"] == "local":
            raise ValueError("mutating cases must not be labeled local-only")
        if case["evidence_required"] != ["runner", "commit", "exit_code", "trace_uri"]:
            raise ValueError("missing evidence contract")
        if case["dataset_version"] != "1.0.0":
            raise ValueError("unsupported dataset version")
    return ids

def score(cases, evidence):
    ids = validate_dataset(cases)
    seen = set()
    passed = set()
    failures = []
    for row in evidence:
        case_id = row.get("id")
        if case_id not in ids:
            raise ValueError(f"unknown evidence case: {case_id}")
        if case_id in seen:
            raise ValueError(f"duplicate evidence case: {case_id}")
        seen.add(case_id)
        if row.get("status") != "passed":
            continue
        required = ("runner", "commit", "trace_uri")
        if row.get("exit_code") != 0 or any(not isinstance(row.get(key), str)
            or not row[key].strip() for key in required):
            failures.append(case_id)
            continue
        # A self-declared pass is a candidate only. The trace remains externally
        # auditable; this scorer cannot independently attest its truth.
        passed.add(case_id)
    buckets = {}
    for case in cases:
        gate = case["gate"]
        item = buckets.setdefault(gate, {"total": 0, "evidence_claimed_pass": 0})
        item["total"] += 1
        item["evidence_claimed_pass"] += case["id"] in passed
    return {"dataset_size": len(cases), "candidate_pass": len(passed),
            "missing_or_unverified": len(cases) - len(passed),
            "invalid_pass_claims": failures, "by_gate": buckets,
            "verified_closed": False}

def main(argv):
    cases = load_jsonl(ROOT / "cases.jsonl")
    validate_dataset(cases)
    if len(argv) == 1:
        print(json.dumps({"dataset_valid": True, "cases": len(cases)}, sort_keys=True))
        return 0
    evidence = load_jsonl(pathlib.Path(argv[1]))
    result = score(cases, evidence)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 2 if result["invalid_pass_claims"] else 0

if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except (ValueError, OSError) as error:
        print(f"BENCHMARK INVALID: {error}", file=sys.stderr)
        sys.exit(2)
