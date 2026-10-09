#!/usr/bin/env python3
"""Validate explicit case-to-Rust-test bindings, without executing live endpoints."""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parents[1]
def check():
    manifest = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))
    doc = json.loads((ROOT / "execution_bindings.json").read_text(encoding="utf-8"))
    expected = {case["id"] for case in manifest["cases"]}
    records = doc["bindings"]
    ids = [row["id"] for row in records]
    assert len(ids) == len(set(ids)) and set(ids) == expected, "bindings must cover every canonical case once"
    totals = {"exact": 0, "partial": 0, "absent": 0}
    for row in records:
        kind = row["coverage"]
        assert kind in totals, f"invalid coverage {kind}"
        totals[kind] += 1
        if kind == "absent":
            assert row["path"] is None and row["test"] is None, f"{row['id']} has invalid absent mapping"
            continue
        assert row["path"] and row["test"], f"{row['id']} must name an executable test"
        file = REPO / row["path"]
        assert file.is_file(), f"{row['id']}: file not found: {file}"
        source = file.read_text(encoding="utf-8")
        pattern = r"(?m)^\s*(?:async\s+)?fn\s+" + re.escape(row["test"]) + r"\s*\("
        assert re.search(pattern, source), f"{row['id']}: Rust test function missing"
        # Verify this really has a test attribute, not only a helper function.
        test_pattern = r"(?s)#\[(?:tokio::)?test\](?:\s*#\[[^\]]+\])*\s*(?:async\s+)?fn\s+" + re.escape(row["test"]) + r"\s*\("
        assert re.search(test_pattern, source), f"{row['id']}: function not marked as a test"
    return {"canonical_cases": len(ids), "source_binding_counts": totals,
            "live_execution_proven": False, "verified_closed": False}
if __name__ == "__main__":
    print(json.dumps(check(), sort_keys=True))
