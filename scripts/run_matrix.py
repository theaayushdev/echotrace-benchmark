#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from echotrace.agents import OpenAICompatibleAgent  # noqa: E402
from echotrace.agents.api import ModelConfig  # noqa: E402
from echotrace.io import load_cases, load_responses  # noqa: E402
from echotrace.runner import run_experiment  # noqa: E402


def _cost(path: Path) -> float:
    if not path.exists():
        return 0.0
    return sum(float(item.usage.get("cost_usd", 0.0)) for item in load_responses(path))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the frozen model-by-method matrix")
    parser.add_argument("--config", required=True)
    parser.add_argument("--execute", action="store_true", help="make billable API calls")
    parser.add_argument("--confirm-budget", type=float, help="must exactly equal configured USD cap")
    args = parser.parse_args()
    config_path = Path(args.config).resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    base = config_path.parent.parent
    resolve = lambda value: Path(value) if Path(value).is_absolute() else base / value
    dataset = resolve(config["dataset"])
    model_file = resolve(config["models_file"])
    output_dir = resolve(config["output_dir"])
    jobs = [(model, method) for model in config["models"] for method in config["methods"]]
    plan = {
        "execute": args.execute,
        "jobs": len(jobs),
        "models": len(config["models"]),
        "methods": len(config["methods"]),
        "budget_usd": float(config["budget_usd"]),
        "dataset": str(dataset),
        "outputs": [str(output_dir / f"{model}-{method}.jsonl") for model, method in jobs],
    }
    if not args.execute:
        print(json.dumps(plan, indent=2))
        return
    budget = float(config["budget_usd"])
    if args.confirm_budget != budget:
        raise SystemExit(f"refusing billable run: pass --confirm-budget {budget:g}")
    cases = load_cases(dataset)
    if not cases or any(case.review_status == "generated" for case in cases):
        raise SystemExit("refusing final matrix: every case must be double_reviewed or adjudicated")
    selected = [case for case in cases if case.split == config["split"]]
    model_configs = {name: ModelConfig.from_file(str(model_file), name) for name in config["models"]}
    unpriced = [
        name
        for name, item in model_configs.items()
        if item.input_cost_per_million <= 0 and item.output_cost_per_million <= 0
    ]
    if unpriced:
        raise SystemExit("refusing frozen run with unpriced model configs: " + ", ".join(unpriced))
    missing = [item.key_env for item in model_configs.values() if not os.environ.get(item.key_env)]
    if missing:
        raise SystemExit("missing API credentials: " + ", ".join(sorted(set(missing))))
    spent = sum(_cost(Path(item)) for item in plan["outputs"])
    summaries = []
    for model, method in jobs:
        if spent >= budget:
            break
        target = output_dir / f"{model}-{method}.jsonl"
        before = _cost(target)
        summary = run_experiment(
            selected,
            OpenAICompatibleAgent(model_configs[model]),
            target,
            method,
            config["track"],
            budget - spent + before,
            float(config["threshold"]),
            cases,
        )
        spent += float(summary["cost_usd"]) - before
        summaries.append({"model": model, "method": method, **summary})
    print(json.dumps({**plan, "spent_usd": spent, "summaries": summaries}, indent=2))


if __name__ == "__main__":
    main()
