#!/usr/bin/env python3
"""Fail-closed cross-story completeness and closure gate."""
import json
from pathlib import Path

PATH = Path(__file__).with_name("user-story-horizontal-matrix.json")
DIMENSIONS = {"function", "state", "integration", "security", "performance",
              "maintainability", "observability", "testing", "user_value",
              "external_compatibility"}
ALLOWED = {"VERIFIED", "PARTIAL", "NOT_IMPLEMENTED", "NOT_APPLICABLE", "BLOCKED"}
STORY_STATES = {"VERIFIED_CLOSED", "PARTIAL", "BLOCKED", "HOLD", "OUT_OF_SCOPE"}


def validate(data):
    errors = []
    stories = data.get("stories", [])
    ids = [s.get("id") for s in stories]
    if len(stories) != 15 or set(ids) != {f"US-{i:02d}" for i in range(1, 16)}:
        errors.append("baseline must contain exactly US-01..US-15")
    if len(ids) != len(set(ids)):
        errors.append("duplicate story ID")
    lookup = {s.get("id"): s for s in stories}
    for story in stories:
        sid = story.get("id")
        dims = story.get("dimensions", {})
        if set(dims) != DIMENSIONS:
            errors.append(f"{sid}: exactly ten named dimensions required")
        for key, item in dims.items():
            if not isinstance(item, dict) or item.get("status") not in ALLOWED:
                errors.append(f"{sid}/{key}: unknown dimension status")
            elif item["status"] == "NOT_APPLICABLE" and not item.get("reason", "").strip():
                errors.append(f"{sid}/{key}: N/A needs rationale")
        if story.get("status") not in STORY_STATES:
            errors.append(f"{sid}: invalid story status")
        if story.get("status") == "VERIFIED_CLOSED":
            if any(v.get("status") != "VERIFIED" for v in dims.values()
                   if v.get("status") != "NOT_APPLICABLE"):
                errors.append(f"{sid}: cannot close with unverified applicable dimension")
            if story.get("vertical_acceptance") != "VERIFIED" or story.get("horizontal_acceptance") != "VERIFIED":
                errors.append(f"{sid}: both acceptance layers must be VERIFIED")
            if not story.get("evidence") or story.get("independent_acceptance") in (None, "", "self-asserted"):
                errors.append(f"{sid}: closure requires evidence and independent acceptance")
        for dep in story.get("depends_on", []):
            if dep not in lookup or dep == sid:
                errors.append(f"{sid}: invalid dependency {dep}")
        for impact in story.get("impacts", []):
            if impact not in lookup or impact == sid:
                errors.append(f"{sid}: invalid impact {impact}")
    # Cycles make a purported closure order impossible.
    visiting, visited = set(), set()
    def visit(sid):
        if sid in visiting:
            errors.append(f"dependency cycle at {sid}")
            return
        if sid in visited or sid not in lookup:
            return
        visiting.add(sid)
        for dep in lookup[sid].get("depends_on", []):
            visit(dep)
        visiting.remove(sid)
        visited.add(sid)
    for sid in ids:
        visit(sid)
    return errors


if __name__ == "__main__":
    failures = validate(json.loads(PATH.read_text()))
    if failures:
        raise SystemExit("\n".join(failures))
    print("horizontal completeness matrix: valid (no unproven closures)")
