#!/usr/bin/env python3
"""Compile an assurance profile into a minimal, reviewable probe plan.

This intentionally does not generate protocol-specific test source. It fails closed
unless the profile states both what evidence is observable and what a negative oracle
must reject, then emits the protocol-neutral contract a native conformance harness
must implement.
"""

import json
import sys
from pathlib import Path


def compile_profile(path: Path) -> dict:
    data = json.loads(path.read_text())
    app = data["applicability"]
    probes = []

    for oracle in data["negative_oracles"]:
        readiness = oracle.get("conformance_readiness", "ready")
        if readiness != "ready":
            probes.append(
                {
                    "oracle_id": oracle["id"],
                    "status": "blocked",
                    "conformance_readiness": readiness,
                    "blocking_decision": oracle.get("blocking_decision"),
                    "ready_invariant": oracle.get("ready_invariant"),
                }
            )
            continue

        reject = oracle.get("must_reject") or oracle.get("must_not_claim")
        if not reject:
            raise ValueError(f"{oracle.get('id', '<unknown>')}: oracle has no rejection boundary")

        probes.append(
            {
                "oracle_id": oracle["id"],
                "conformance_system": app["conformance_system"],
                "profile": app.get("profile"),
                "feature_scope": app.get("feature_scope", []),
                "setup": oracle.get("given", []),
                "required_observation": oracle.get("must_observe", []),
                "reject_if": reject,
                "report_visibility_requirement": app["report_visibility_requirement"],
                "protocol_decision_left_open": oracle.get("protocol_decision_left_open"),
            }
        )

    return {
        "source_profile": path.name,
        "profile_version": data["profile_version"],
        "protocol": data["protocol"],
        "probe_plans": probes,
    }


def main() -> int:
    if len(sys.argv) < 2:
        print(f"usage: {Path(sys.argv[0]).name} PROFILE.json [PROFILE.json ...]", file=sys.stderr)
        return 2

    compiled = []
    try:
        for arg in sys.argv[1:]:
            compiled.append(compile_profile(Path(arg)))
    except (KeyError, ValueError, json.JSONDecodeError) as exc:
        print(f"compile failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(compiled, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
