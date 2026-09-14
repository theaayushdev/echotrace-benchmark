#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from echotrace.io import load_cases  # noqa: E402
from echotrace.runner import evaluate_echo_graph  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Tune EchoGraph on validation only")
    parser.add_argument("--data", default=str(ROOT / "data" / "echobench.jsonl"))
    parser.add_argument("--start", type=float, default=0.30)
    parser.add_argument("--stop", type=float, default=0.90)
    parser.add_argument("--step", type=float, default=0.05)
    parser.add_argument("--output")
    args = parser.parse_args()
    if not 0 < args.start <= args.stop < 1 or args.step <= 0:
        parser.error("require 0 < start <= stop < 1 and step > 0")
    cases = load_cases(args.data)
    thresholds = []
    value = args.start
    while value <= args.stop + 1e-9:
        thresholds.append(round(value, 10))
        value += args.step
    reports = [evaluate_echo_graph(cases, "validation", threshold) for threshold in thresholds]
    best = min(
        reports,
        key=lambda report: (
            report["metrics"]["root_count_mae"],
            -report["metrics"]["family_pair_f1"],
            abs(report["threshold"] - 0.5),
        ),
    )
    result = {"selection_split": "validation", "objective": "root_count_mae", "best": best, "grid": reports}
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
