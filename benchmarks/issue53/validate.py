#!/usr/bin/env python3
"""Validate Issue #53 benchmark metadata without claiming VTN execution."""
import copy
import json
from pathlib import Path

MANIFEST = Path(__file__).with_name("cases.json")
STORIES = {f"US53-{n:02d}" for n in range(1, 8)}
EXECUTORS = {"unit", "external_vtn", "fault_injection", "concurrency", "regression"}
EXPECTATIONS = {"pass", "reject", "reconcile", "serialize", "isolate"}
STATUSES = {"not_executed", "pass", "fail", "blocked"}


def validate(doc):
    errors = []
    if doc.get("schema_version") != "1.0.0":
        errors.append("unsupported schema_version")
    cases = doc.get("cases")
    if not isinstance(cases, list) or not cases:
        return errors + ["cases must be a nonempty array"]
    ids = set()
    for i, case in enumerate(cases):
        key = f"cases[{i}]"
        if not isinstance(case, dict):
            errors.append(f"{key}: expected object")
            continue
        ident = case.get("id")
        if not isinstance(ident, str) or not ident.startswith("B") or not ident[1:].isdigit():
            errors.append(f"{key}: invalid id")
        elif ident in ids:
            errors.append(f"{key}: duplicate id {ident}")
        ids.add(ident)
        if case.get("story") not in STORIES:
            errors.append(f"{key}: story not traced to issue 53")
        if case.get("polarity") not in {"positive", "negative"}:
            errors.append(f"{key}: invalid polarity")
        if case.get("executor") not in EXECUTORS:
            errors.append(f"{key}: invalid executor")
        if case.get("expected") not in EXPECTATIONS:
            errors.append(f"{key}: invalid expected outcome")
        if not isinstance(case.get("scenario"), str) or not case["scenario"].strip():
            errors.append(f"{key}: missing scenario")
        if not isinstance(case.get("axis"), str) or not case["axis"].strip():
            errors.append(f"{key}: missing axis")
        if type(case.get("requires_mutation")) is not bool:
            errors.append(f"{key}: missing mutation risk annotation")
        if case.get("status") not in STATUSES:
            errors.append(f"{key}: invalid status")
        if case.get("status") in {"pass", "fail"}:
            ev = case.get("evidence")
            if not isinstance(ev, dict) or not ev.get("run_url") or not ev.get("commit_sha"):
                errors.append(f"{key}: executed outcome without run URL and commit")
        elif case.get("evidence") is not None:
            errors.append(f"{key}: unexecuted/blocked case must not claim evidence")
    for story in sorted(STORIES):
        members = [c for c in cases if isinstance(c, dict) and c.get("story") == story]
        if not members:
            errors.append(f"missing user story {story}")
    if not any(c.get("polarity") == "negative" for c in cases if isinstance(c, dict)):
        errors.append("at least one counterexample required")
    return errors


def selftest(doc):
    assert not validate(doc), validate(doc)
    duplicate = copy.deepcopy(doc)
    duplicate["cases"][1]["id"] = duplicate["cases"][0]["id"]
    assert any("duplicate id" in e for e in validate(duplicate))
    false_pass = copy.deepcopy(doc)
    false_pass["cases"][0]["status"] = "pass"
    assert any("without run URL" in e for e in validate(false_pass))
    invalid_story = copy.deepcopy(doc)
    invalid_story["cases"][0]["story"] = "US53-99"
    assert any("not traced" in e for e in validate(invalid_story))
    print("benchmark-validator selftest PASS (duplicate, false pass, untraced story)")


if __name__ == "__main__":
    document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    failures = validate(document)
    if failures:
        raise SystemExit("\n".join(failures))
    total = len(document["cases"])
    statuses = {s: sum(c["status"] == s for c in document["cases"]) for s in STATUSES}
    print(f"BENCHMARK MANIFEST VALID: {total} cases; {statuses}")
    selftest(document)
