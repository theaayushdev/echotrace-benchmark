#!/usr/bin/env python3
"""Generate a chronology-valid EchoBench-Synthetic v1.2 candidate release.

This intentionally writes new files and never modifies the frozen v1.1 release.
The candidate remains synthetic and gold-by-construction until human review and
a new protocol freeze are complete.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from echotrace.chronology import repair_dates, reversed_edges
from scripts.generate_benchmark_v1 import CONDITIONS, make_case

VERSION = "1.2-candidate"
WORLD_COUNT = 360


def assignments(seed: int) -> dict[int, tuple[str, str]]:
    """Allocate world-disjoint, verdict-balanced fresh splits."""
    result: dict[int, tuple[str, str]] = {}
    for verdict_index, verdict in enumerate(("supported", "contradicted", "insufficient")):
        worlds = list(range(verdict_index, WORLD_COUNT, 3))
        random.Random(seed + verdict_index + 1).shuffle(worlds)
        for world in worlds[:72]:
            result[world] = ("train", verdict)
        for world in worlds[72:96]:
            result[world] = ("validation", verdict)
        for world in worlds[96:]:
            result[world] = ("test", verdict)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=20260914)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "data" / "echobench_synthetic_v1_2")
    args = parser.parse_args()
    if args.out_dir.exists() and any(args.out_dir.iterdir()):
        raise SystemExit(f"refusing to overwrite non-empty output directory: {args.out_dir}")
    args.out_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(args.seed)
    public, gold, manifest = [], [], []
    changed_dates = 0
    split_assignments = assignments(args.seed)
    for world in range(WORLD_COUNT):
        split, verdict = split_assignments[world]
        for condition in CONDITIONS:
            visible, hidden = make_case(rng, world, condition, verdict, split)
            repaired = repair_dates(visible, hidden)
            changed_dates += sum(
                before["published_at"] != after["published_at"]
                for before, after in zip(visible["documents"], repaired["documents"])
            )
            if reversed_edges(repaired, hidden):
                raise AssertionError("chronology repair left a reversed lineage edge")
            public.append(repaired)
            gold.append({"case_id": repaired["case_id"], **hidden})
            manifest.append({"case_id": repaired["case_id"], "world": world,
                             "condition": condition, "split": split})

    for filename, rows in (("public.jsonl", public), ("gold.jsonl", gold)):
        with (args.out_dir / filename).open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    (args.out_dir / "manifest.json").write_text(json.dumps({
        "version": VERSION, "seed": args.seed, "world_count": WORLD_COUNT,
        "cases": manifest, "chronology": {"reversed_edges": 0, "changed_dates": changed_dates},
        "status": "candidate; synthetic and gold-by-construction; not a frozen confirmatory release",
    }, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"version": VERSION, "cases": len(public), "worlds": WORLD_COUNT,
                      "changed_dates": changed_dates, "output": str(args.out_dir)}))


if __name__ == "__main__":
    main()
