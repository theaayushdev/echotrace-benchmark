#!/usr/bin/env python3
"""Validate the structural, split, and chronology invariants of EchoBench candidates."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from echotrace.chronology import reversed_edges
from echotrace.io import load_v1_cases


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=ROOT / "data" / "echobench_synthetic_v1_2")
    args = parser.parse_args()
    manifest_path = args.data / "manifest.json"
    public_path, gold_path = args.data / "public.jsonl", args.data / "gold.jsonl"
    manifest_document = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest_document.get("version") not in {"1.2-candidate", "1.3-candidate"}:
        raise SystemExit("expected an EchoBench candidate manifest")
    cases = load_v1_cases(public_path, gold_path, manifest_path)
    public = {row["case_id"]: row for row in map(json.loads, public_path.read_text().splitlines())}
    gold = {row["case_id"]: row for row in map(json.loads, gold_path.read_text().splitlines())}
    errors = []
    worlds: dict[str, set[str]] = {}
    for case in cases:
        worlds.setdefault(case.micro_world_id, set()).add(case.split)
        reversed_count = len(reversed_edges(public[case.case_id], gold[case.case_id]))
        if reversed_count:
            errors.append(f"{case.case_id}: {reversed_count} reversed lineage edges")
        if len(public[case.case_id]["documents"]) != 12:
            errors.append(f"{case.case_id}: expected 12 documents")
    leaked = [world for world, splits in worlds.items() if len(splits) != 1]
    if leaked:
        errors.append(f"world split leakage: {sorted(leaked)}")
    split_counts = Counter(case.split for case in cases)
    verdict_counts = Counter((case.split, case.gold_claims[0].verdict) for case in cases)
    expected_splits = {"train": 2376, "validation": 792, "test": 792}
    if dict(split_counts) != expected_splits:
        errors.append(f"unexpected split counts: {dict(split_counts)}")
    for split, count in (("train", 792), ("validation", 264), ("test", 264)):
        for verdict in ("supported", "contradicted", "insufficient"):
            if verdict_counts[split, verdict] != count:
                errors.append(f"unexpected {split}/{verdict} count")
    report = {"valid": not errors, "cases": len(cases), "worlds": len(worlds),
              "split_counts": dict(split_counts), "errors": errors}
    print(json.dumps(report, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
