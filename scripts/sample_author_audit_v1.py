#!/usr/bin/env python3
"""Create a gold-blind 66-case sole-author audit packet from training worlds."""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    root = Path(__file__).resolve().parents[1]
    parser.add_argument(
        "--public", type=Path, default=root / "data" / "echobench_synthetic_v1_public.jsonl"
    )
    parser.add_argument(
        "--gold", type=Path, default=root / "data" / "echobench_synthetic_v1_gold.jsonl"
    )
    parser.add_argument("--seed", type=int, default=20260912)
    parser.add_argument(
        "--sample", type=Path, default=root / "annotations" / "v1" / "author_audit_sample.json"
    )
    parser.add_argument(
        "--packet", type=Path, default=root / "annotations" / "v1" / "author_audit_packet.jsonl"
    )
    args = parser.parse_args()
    public = {
        row["case_id"]: row
        for row in map(json.loads, args.public.read_text(encoding="utf-8").splitlines())
    }
    gold = list(map(json.loads, args.gold.read_text(encoding="utf-8").splitlines()))
    cells: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in gold:
        if row["split"] == "train":
            cells[row["condition"], row["gold_claim"]["verdict"]].append(row)
    selected = []
    for cell in sorted(cells):
        rng = random.Random(f"{args.seed}:{cell[0]}:{cell[1]}")
        selected.extend(rng.sample(cells[cell], 2))
    args.sample.parent.mkdir(parents=True, exist_ok=True)
    args.sample.write_text(
        json.dumps(
            {
                "version": "1.1",
                "seed": args.seed,
                "case_ids": sorted(row["case_id"] for row in selected),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    with args.packet.open("w", encoding="utf-8") as handle:
        for hidden in sorted(selected, key=lambda row: row["case_id"]):
            visible = public[hidden["case_id"]]
            packet = {
                "case_id": hidden["case_id"],
                "query": visible["query"],
                "focal_claim": hidden["gold_claim"]["text"],
                "documents": visible["documents"],
            }
            handle.write(json.dumps(packet, ensure_ascii=False) + "\n")
    print(
        json.dumps(
            {
                "sample": str(args.sample),
                "packet": str(args.packet),
                "cases": len(selected),
                "cells": len(cells),
                "gold_fields_exposed": ["focal_claim"],
            }
        )
    )


if __name__ == "__main__":
    main()
