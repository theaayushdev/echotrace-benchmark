#!/usr/bin/env python3
"""Execute the frozen v1 local-model method matrix (never runs by default)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from echotrace.agents import LocalModelConfig, LocalTransformersAgent  # noqa: E402
from echotrace.io import load_v1_cases  # noqa: E402
from echotrace.review_v1 import review_v1_report  # noqa: E402
from echotrace.runner import run_experiment  # noqa: E402


def resolve(base: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else base / path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    config_path = Path(args.config).resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    public = resolve(ROOT, config["public_data"])
    gold = resolve(ROOT, config["gold_data"])
    manifest = resolve(ROOT, config["manifest"])
    review_sample = resolve(ROOT, config["review_sample"])
    review_ledger = resolve(ROOT, config["review_ledger"])
    freeze = resolve(ROOT, config["freeze_manifest"])
    jobs = [(track, method) for track in config["tracks"] for method in config["methods"]]
    plan = {"execute": args.execute, "model_id": config["model_id"], "model_revision": config["model_revision"], "jobs": jobs, "split": config["split"]}
    if not args.execute:
        print(json.dumps(plan, indent=2))
        return
    if not freeze.exists():
        raise SystemExit("refusing execution: v1 freeze manifest is missing")
    review = review_v1_report(public, review_sample, review_ledger)
    if not review["valid"]:
        raise SystemExit("refusing execution: blinded v1 review gate is incomplete")
    if config["model_revision"].startswith("REPLACE_"):
        raise SystemExit("refusing execution: model revision is not pinned")
    cases = load_v1_cases(public, gold, manifest)
    selected = [case for case in cases if case.split == config["split"]]
    agent = LocalTransformersAgent(LocalModelConfig(config["model_id"], config["model_revision"]))
    output_dir = resolve(ROOT, config["output_dir"])
    summaries = []
    for track, method in jobs:
        target = output_dir / f"qwen2.5-7b-{track}-{method}.jsonl"
        summaries.append({"track": track, "method": method, **run_experiment(selected, agent, target, method, track, 0.0, float(config["threshold"]), cases)})
    print(json.dumps({**plan, "summaries": summaries}, indent=2))


if __name__ == "__main__":
    main()
