#!/usr/bin/env python3
"""Audit only the v1.1 training split; do not recompute held-out model outcomes."""
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from echotrace.chronology import reversed_edges
from echotrace.io import sha256_file


def main():
    public_path = ROOT / "data/echobench_synthetic_v1_public.jsonl"
    gold_path = ROOT / "data/echobench_synthetic_v1_gold.jsonl"
    public = {r["case_id"]: r for r in map(json.loads, public_path.read_text().splitlines())}
    counts = defaultdict(lambda: {"edges": 0, "source_after_derivative": 0})
    examples = []
    for gold in map(json.loads, gold_path.read_text().splitlines()):
        if gold["split"] != "train":
            continue
        bad = reversed_edges(public[gold["case_id"]], gold)
        if gold["gold_lineage_edges"]:
            counts[gold["condition"]]["edges"] += len(gold["gold_lineage_edges"])
            counts[gold["condition"]]["source_after_derivative"] += len(bad)
        if bad and len(examples) < 10:
            examples.append({"case_id": gold["case_id"], "reversed_edges": bad})
    report = {"scope": "post-freeze training-only construction audit", "by_condition": dict(counts),
              "edges": sum(c["edges"] for c in counts.values()),
              "source_after_derivative": sum(c["source_after_derivative"] for c in counts.values()),
              "examples": examples, "sha256": {str(p.relative_to(ROOT)): sha256_file(p)
                                                  for p in (public_path, gold_path)}}
    (ROOT / "artifacts/chronology-audit-train-v1.1.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k not in ("examples", "sha256")}))


if __name__ == "__main__":
    main()
