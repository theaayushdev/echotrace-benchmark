#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from echotrace.io import load_cases, load_responses  # noqa: E402
from echotrace.statistics import holm_adjust, mixed_effects_note, paired_comparison  # noqa: E402

METRICS = (
    "root_count_mae",
    "false_corroboration",
    "citation_precision",
    "evidence_family_recall",
    "evidence_family_pair_f1",
    "verdict_accuracy",
    "confidence_brier",
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Matched-world inference for two frozen runs")
    parser.add_argument("--data", default=str(ROOT / "data" / "echobench.jsonl"))
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--split", choices=("train", "validation", "test"), default="test")
    parser.add_argument("--samples", type=int, default=10_000)
    parser.add_argument("--output")
    args = parser.parse_args()
    cases = [case for case in load_cases(args.data) if case.split == args.split]
    baseline, candidate = load_responses(args.baseline), load_responses(args.candidate)
    case_ids = {case.case_id for case in cases}
    coverage = {
        "baseline": sum(item.error is None and item.case_id in case_ids for item in baseline) / len(case_ids),
        "candidate": sum(item.error is None and item.case_id in case_ids for item in candidate) / len(case_ids),
    }
    comparisons = {
        metric: paired_comparison(cases, baseline, candidate, metric, args.samples)
        for metric in METRICS
    }
    adjusted = holm_adjust({name: float(value["p_value"]) for name, value in comparisons.items()})
    for metric, value in comparisons.items():
        value["holm_p_value"] = adjusted[metric]
    report = {
        "estimand": "candidate minus baseline; negative favors candidate for MAE/FCR",
        "coverage": coverage,
        "mitigation_coverage_gate": min(coverage.values()) >= 0.95,
        "comparisons": comparisons,
        "mixed_effects": mixed_effects_note(),
    }
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
