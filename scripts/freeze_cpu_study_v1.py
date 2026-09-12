#!/usr/bin/env python3
"""Create the CPU-study freeze manifest only after every pre-test gate passes."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from echotrace.benchmark_v1 import validate_v1_dataset
from echotrace.io import sha256_file

REQUIRED_THRESHOLDS = {
    "lexical_bow",
    "tfidf",
    "minilm",
    "echograph_classic",
    "echograph_no_links",
    "echograph_no_attribution",
    "echograph_no_lexical",
    "echograph_no_numeric",
    "echograph_no_chronology",
    "echograph_no_domain",
}
FROZEN_FILES = (
    "data/echobench_synthetic_v1_public.jsonl",
    "data/echobench_synthetic_v1_gold.jsonl",
    "data/echobench_synthetic_v1_manifest.json",
    "experiments/protocol_v1.md",
    "artifacts/detection-settings-v1.1.json",
    "scripts/generate_benchmark_v1.py",
    "scripts/evaluate_v1_detection.py",
    "scripts/simulate_confidence_v1.py",
    "scripts/validate_benchmark_v1.py",
    "echotrace/baselines.py",
    "echotrace/echo_graph.py",
    "echotrace/freeze.py",
    "echotrace/metrics.py",
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/freeze-cpu-v1.1.json")
    args = parser.parse_args()
    public = ROOT / "data/echobench_synthetic_v1_public.jsonl"
    gold = ROOT / "data/echobench_synthetic_v1_gold.jsonl"
    manifest = ROOT / "data/echobench_synthetic_v1_manifest.json"
    benchmark = validate_v1_dataset(public, gold, manifest)
    settings = json.loads(
        (ROOT / "artifacts/detection-settings-v1.1.json").read_text(encoding="utf-8")
    )
    settings_errors = []
    if settings.get("version") != "1.1" or settings.get("selection_split") != "validation":
        settings_errors.append("settings must be v1.1 and selected only on validation")
    missing = REQUIRED_THRESHOLDS - set(settings.get("thresholds", {}))
    if missing:
        settings_errors.append(f"missing thresholds: {sorted(missing)}")
    semantic = settings.get("semantic_model") or {}
    if not semantic.get("model_id") or len(semantic.get("revision", "")) != 40:
        settings_errors.append("semantic model ID and 40-character pinned revision are required")
    gate_errors = []
    if not benchmark["valid"]:
        gate_errors.extend(f"benchmark: {error}" for error in benchmark["errors"])
    gate_errors.extend(settings_errors)
    if gate_errors:
        print(
            json.dumps(
                {
                    "frozen": False,
                    "errors": gate_errors,
                    "scope": "synthetic gold-by-construction; no human-validation claim",
                },
                indent=2,
                sort_keys=True,
            )
        )
        raise SystemExit(1)
    missing_files = [relative for relative in FROZEN_FILES if not (ROOT / relative).is_file()]
    if missing_files:
        raise SystemExit(f"cannot freeze; missing files: {missing_files}")
    document = {
        "frozen": True,
        "study": "EchoTrace CPU study",
        "version": "1.1",
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "completed_test_runs": [],
        "gates": {
            "benchmark": benchmark,
            "scope": "synthetic gold-by-construction; no human-validation claim",
        },
        "settings": settings,
        "sha256": {relative: sha256_file(ROOT / relative) for relative in FROZEN_FILES},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {"frozen": True, "output": str(args.output), "files": len(FROZEN_FILES)}, indent=2
        )
    )


if __name__ == "__main__":
    main()
