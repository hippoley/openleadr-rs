#!/usr/bin/env python3
"""Fail CI if the two historical manifests silently diverge.

Crosswalk relations are traceability hints, NEVER duplicate execution credit.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def audit():
    a = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))
    b = [json.loads(s) for s in (ROOT / "cases.jsonl").read_text(encoding="utf-8").splitlines() if s.strip()]
    c = json.loads((ROOT / "crosswalk.json").read_text(encoding="utf-8"))
    ids_a = [r["id"] for r in a["cases"]]
    ids_b = [r["id"] for r in b]
    mapping = c["mapping"]
    assert len(ids_a) == len(set(ids_a)) and len(ids_b) == len(set(ids_b)), "duplicate manifest IDs"
    assert len(mapping) == len(ids_a), "crosswalk must account for every canonical case"
    assert {m["json_id"] for m in mapping} == set(ids_a), "crosswalk source missing or unknown"
    assert all(m["jsonl_id"] is None or m["jsonl_id"] in ids_b for m in mapping), "unknown secondary ID"
    assert all(m["relation"] in ("unmapped", "partial", "related") for m in mapping), "unsupported relation"
    assert all((m["jsonl_id"] is None) == (m["relation"] == "unmapped") for m in mapping), "invalid unmapped relation"
    references = {}
    for row in mapping:
        if row["jsonl_id"] is not None:
            references.setdefault(row["jsonl_id"], []).append(row["json_id"])
    overlaps = {k: v for k, v in references.items() if len(v) > 1}
    unmatched = sorted(set(ids_b) - set(references))
    return {"canonical_cases": len(ids_a), "secondary_cases": len(ids_b),
            "unmapped_canonical": [x["json_id"] for x in mapping if x["jsonl_id"] is None],
            "unmapped_secondary": unmatched, "many_to_one": overlaps,
            "joint_pass_count": None, "joint_verified_closed": False}

if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
