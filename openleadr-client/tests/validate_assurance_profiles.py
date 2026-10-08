#!/usr/bin/env python3
"""Fail-closed validator for protocol assurance profiles."""

import json
import sys
from pathlib import Path

REQUIRED_TOP = {"profile_version", "purpose", "protocol", "applicability", "evidence_surface", "negative_oracles"}
REQUIRED_EVIDENCE = {"id", "observation", "supports", "does_not_establish"}


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text())
    except Exception as exc:
        return [f"{path}: invalid JSON: {exc}"]

    missing = REQUIRED_TOP - data.keys()
    if missing:
        errors.append(f"{path}: missing top-level keys: {sorted(missing)}")

    app = data.get("applicability", {})
    if not app.get("conformance_system"):
        errors.append(f"{path}: applicability.conformance_system is required")
    if not app.get("report_visibility_requirement"):
        errors.append(f"{path}: applicability.report_visibility_requirement is required")

    for i, item in enumerate(data.get("evidence_surface", [])):
        missing = REQUIRED_EVIDENCE - item.keys()
        if missing:
            errors.append(f"{path}: evidence_surface[{i}] missing {sorted(missing)}")
        if not item.get("does_not_establish"):
            errors.append(f"{path}: evidence_surface[{i}] must bound at least one stronger claim")

    for i, oracle in enumerate(data.get("negative_oracles", [])):
        if not oracle.get("id"):
            errors.append(f"{path}: negative_oracles[{i}].id is required")
        if not any(k in oracle for k in ("must_not_claim", "must_reject")):
            errors.append(f"{path}: negative_oracles[{i}] needs must_not_claim or must_reject")
        readiness = oracle.get("conformance_readiness", "ready")
        if readiness != "ready":
            if not oracle.get("blocking_decision"):
                errors.append(f"{path}: negative_oracles[{i}] blocked oracle needs blocking_decision")
            if not oracle.get("ready_invariant"):
                errors.append(f"{path}: negative_oracles[{i}] blocked oracle needs ready_invariant")

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
