#!/usr/bin/env python3
"""Independent JUnit oracle: require both real HTTP smoke cases, no skipped or failed tests."""
import argparse
import hashlib
import json
import pathlib
import xml.etree.ElementTree as ET

REQUIRED = {
    "external_vtn_can_list_programs_without_local_database",
    "external_vtn_can_list_events_without_local_database",
}

def audit(xml_path: pathlib.Path) -> dict:
    tree = ET.parse(xml_path)
    cases = tree.getroot().findall(".//testcase")
    if not cases:
        raise ValueError("JUnit report has zero executed tests")
    unexpected = []
    for case in cases:
        name = case.get("name", "").split("::")[-1]
        if name not in REQUIRED:
            unexpected.append(name)
    if unexpected:
        raise ValueError(f"unexpected tests in dedicated E2E receipt: {sorted(unexpected)}")
    seen = {}
    for case in cases:
        name = case.get("name", "").split("::")[-1]
        if name not in REQUIRED:
            continue
        if name in seen:
            raise ValueError(f"duplicate executed test: {name}")
        seen[name] = case
    missing = REQUIRED - seen.keys()
    if missing:
        raise ValueError(f"required executable tests missing: {sorted(missing)}")
    for name, case in seen.items():
        for tag in ("failure", "error", "skipped"):
            if case.find(tag) is not None:
                raise ValueError(f"{name}: {tag}, not PASS")
        if float(case.get("time", "0")) < 0:
            raise ValueError(f"{name}: impossible duration")
    data = xml_path.read_bytes()
    return {
        "oracle": "issue53-junit-v1",
        "cases_passed": sorted(seen),
        "case_count": len(seen),
        "junit_sha256": hashlib.sha256(data).hexdigest(),
        "source": str(xml_path),
        "verified_closed": False,
        "independent_vtn_verified": False,
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("junit", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()
    receipt = audit(args.junit)
    content = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(content, encoding="utf-8")
    print(content, end="")

if __name__ == "__main__":
    main()
