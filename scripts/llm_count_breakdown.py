#!/usr/bin/env python3
"""Tabulate reported independent-source counts by model, arm, and condition.

Writes count-breakdown.json next to the run's analysis.json. Keys of each count table are the
reported value ("null" for an abstention).
"""
import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from echotrace.llm_study import ARMS, CONDITIONS, latest_events


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", default="artifacts/llm-study-v1.4/dev-r2")
    args = parser.parse_args()
    directory = ROOT / args.directory
    plan = json.loads((directory / "plan.json").read_text())
    cases = plan["cases"]
    output = {"split": plan["split"], "plan_sha256": plan["plan_sha256"], "models": {}}
    for model in plan["models"]:
        log = directory / (model + ".jsonl")
        if not log.exists():
            continue
        _, latest = latest_events(log)
        valid = [e for e in latest.values() if e["status"] == "valid"]
        table = {arm: {c: Counter() for c in CONDITIONS} for arm in ARMS}
        per_world = defaultdict(int)
        for event in valid:
            case = cases[event["case_id"]]
            count = event["answer"].get("independent_sources")
            table[event["arm"]][case["condition"]]["null" if count is None else str(count)] += 1
            per_world[case["world"]] += 1
        output["models"][model] = {
            "worlds_with_responses": len(per_world),
            "complete_worlds": sum(n == len(ARMS) * len(CONDITIONS) for n in per_world.values()),
            "counts": {arm: {c: dict(sorted(t.items())) for c, t in conds.items()}
                       for arm, conds in table.items()},
        }
    (directory / "count-breakdown.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({m: {k: v for k, v in r.items() if k != "counts"}
                      for m, r in output["models"].items()}))


if __name__ == "__main__":
    main()
