#!/usr/bin/env python3
"""Create the blinded 330-case v1 construct-validity review sample."""
from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    root = Path(__file__).resolve().parents[1]
    parser.add_argument("--gold", type=Path, default=root / "data" / "echobench_synthetic_v1_gold.jsonl")
    parser.add_argument("--seed", type=int, default=20260911)
    parser.add_argument("--output", type=Path, default=root / "annotations" / "v1" / "review_sample.json")
    args = parser.parse_args()
    cells: dict[tuple[str, str], list[str]] = defaultdict(list)
    for line in args.gold.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        cells[row["condition"], row["gold_claim"]["verdict"]].append(row["case_id"])
    selected: list[str] = []
    for cell in sorted(cells):
        rows = cells[cell]
        if len(rows) < 10:
            raise SystemExit(f"{cell}: need at least 10 cases")
        rng = random.Random(f"{args.seed}:{cell[0]}:{cell[1]}")
        selected.extend(sorted(rng.sample(rows, 10)))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"seed": args.seed, "case_ids": sorted(selected)}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "cases": len(selected), "cells": len(cells)}))


if __name__ == "__main__":
    main()
