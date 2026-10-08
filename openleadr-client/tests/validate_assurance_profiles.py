#!/usr/bin/env python3
"""Fail-closed validator for protocol assurance profiles."""

import json
import sys
from pathlib import Path

REQUIRED_TOP = {"profile_version", "purpose", "protocol", "applicability", "evidence_surface", "negative_oracles"}
REQUIRED_EVIDENCE = {"id", "observation", "supports", "does_not_establish"}
ALLOWED_READINESS = {"ready", "spec-decision-required", "implementation-regression-only"}


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text())
    except Exception as exc:
        return [f"{path}: invalid JSON: {exc}"]

    if not isinstance(data, dict):
        return [f"{path}: profile root must be an object"]

    missing = REQUIRED_TOP - data.keys()
    if missing:
        errors.append(f"{path}: missing top-level keys: {sorted(missing)}")

    app = data.get("applicability", {})
    if not isinstance(app, dict):
        return [f"{path}: applicability must be an object"]
    if not app.get("conformance_system"):
        errors.append(f"{path}: applicability.conformance_system is required")
    if not app.get("report_visibility_requirement"):
        errors.append(f"{path}: applicability.report_visibility_requirement is required")

    surfaces = data.get("evidence_surface")
    if not isinstance(surfaces, list) or not surfaces:
        errors.append(f"{path}: evidence_surface must be a non-empty list")
        surfaces = []
    for i, item in enumerate(surfaces):
        if not isinstance(item, dict):
            errors.append(f"{path}: evidence_surface[{i}] must be an object")
            continue
        missing = REQUIRED_EVIDENCE - item.keys()
        if missing:
            errors.append(f"{path}: evidence_surface[{i}] missing {sorted(missing)}")
        if not item.get("does_not_establish"):
            errors.append(f"{path}: evidence_surface[{i}] must bound at least one stronger claim")

    oracles = data.get("negative_oracles")
    if not isinstance(oracles, list) or not oracles:
        errors.append(f"{path}: negative_oracles must be a non-empty list")
        oracles = []
    for i, oracle in enumerate(oracles):
        if not isinstance(oracle, dict):
            errors.append(f"{path}: negative_oracles[{i}] must be an object")
            continue
        if not oracle.get("id"):
            errors.append(f"{path}: negative_oracles[{i}].id is required")
        boundaries = [oracle.get(k) for k in ("must_not_claim", "must_reject") if k in oracle]
        if not boundaries or not any(isinstance(b, list) and b and all(isinstance(x, str) and x.strip() for x in b) for b in boundaries):
            errors.append(f"{path}: negative_oracles[{i}] needs non-empty must_not_claim or must_reject list")
        for key in ("must_not_claim", "must_reject"):
            if key in oracle and (not isinstance(oracle[key], list) or not oracle[key] or not all(isinstance(x, str) and x.strip() for x in oracle[key])):
                errors.append(f"{path}: negative_oracles[{i}].{key} must be a non-empty list of strings")
        readiness = oracle.get("conformance_readiness", "ready")
        if app.get("profile") == "mixed-scope-not-reportable" and readiness == "ready":
            errors.append(f"{path}: negative_oracles[{i}] mixed-scope profile cannot declare ready normative conformance")
        if readiness not in ALLOWED_READINESS:
            errors.append(f"{path}: negative_oracles[{i}] has unknown conformance_readiness {readiness!r}")
        if readiness != "ready":
            if not oracle.get("blocking_decision"):
                errors.append(f"{path}: negative_oracles[{i}] blocked oracle needs blocking_decision")
            if not oracle.get("ready_invariant"):
                errors.append(f"{path}: negative_oracles[{i}] blocked oracle needs ready_invariant")
        implementation_evidence = oracle.get("implementation_evidence", [])
        if not isinstance(implementation_evidence, list):
            errors.append(f"{path}: negative_oracles[{i}].implementation_evidence must be a list")
            continue
        for j, evidence in enumerate(implementation_evidence):
            if not isinstance(evidence, dict):
                errors.append(f"{path}: negative_oracles[{i}].implementation_evidence[{j}] must be an object")
                continue
            if not evidence.get("observation"):
                errors.append(f"{path}: negative_oracles[{i}].implementation_evidence[{j}] needs observation")
            if not evidence.get("does_not_establish"):
                errors.append(f"{path}: negative_oracles[{i}].implementation_evidence[{j}] needs does_not_establish")

    return errors


def main() -> int:
    paths = [Path(p) for p in sys.argv[1:]]
    if not paths:
        paths = sorted(Path(__file__).parent.glob("*assurance-profile.json"))
    errors = [e for p in paths for e in validate(p)]
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    for p in paths:
        print(f"valid: {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
