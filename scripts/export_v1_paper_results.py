#!/usr/bin/env python3
"""Export frozen EchoTrace v1.1 test results as LaTeX commands."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DETECTION = ROOT / "artifacts/detection-test-v1.1.json"
SIMULATION = ROOT / "artifacts/confidence-simulation-test-v1.1.json"
FREEZE = ROOT / "artifacts/freeze-cpu-v1.1.json"
OUTPUT = ROOT / "paper/generated/v1-results.tex"


def command(name: str, value: str) -> str:
    return f"\\newcommand{{\\{name}}}{{{value}}}"


def main() -> None:
    detection = json.loads(DETECTION.read_text(encoding="utf-8"))
    simulation = json.loads(SIMULATION.read_text(encoding="utf-8"))
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    if detection["split"] != "test" or simulation["split"] != "test":
        raise SystemExit("paper export requires held-out test artifacts")
    if set(freeze["completed_test_runs"]) != {"detection", "confidence_simulation"}:
        raise SystemExit("both frozen test runs must be complete")
    methods = detection["methods"]
    simulation_methods = simulation["methods"]
    lines = ["% Generated from frozen v1.1 test artifacts; do not edit manually."]
    names = {
        "Url": "url_count",
        "One": "all_one_family",
        "Domain": "domain_grouping",
        "Bow": "lexical_bow",
        "Tfidf": "tfidf",
        "Minilm": "minilm",
        "Echo": "echograph_classic",
        "NoLinks": "echograph_no_links",
        "NoAttr": "echograph_no_attribution",
        "NoLex": "echograph_no_lexical",
        "NoNum": "echograph_no_numeric",
        "NoChron": "echograph_no_chronology",
        "NoDomain": "echograph_no_domain",
    }
    for label, key in names.items():
        row = methods[key]
        lines.append(command(f"{label}FOne", f"{row['exclusive_family_pair_f1']['mean']:.3f}"))
        lines.append(command(f"{label}MAE", f"{row['root_count_mae']['mean']:.3f}"))
    echo = methods["echograph_classic"]
    lines.extend(
        [
            command(
                "EchoFOneCI",
                f"[{echo['exclusive_family_pair_f1']['ci_low']:.3f}, {echo['exclusive_family_pair_f1']['ci_high']:.3f}]",
            ),
            command(
                "EchoMAECI",
                f"[{echo['root_count_mae']['ci_low']:.3f}, {echo['root_count_mae']['ci_high']:.3f}]",
            ),
            command("TestCases", str(detection["n"])),
            command("TestWorlds", str(detection["worlds"])),
        ]
    )
    for label, key in {
        "Doc": "document_count",
        "SimTfidf": "tfidf",
        "SimMinilm": "minilm",
        "SimEcho": "echograph_classic",
    }.items():
        row = simulation_methods[key]
        lines.append(command(f"{label}ProbErr", f"{row['probability_absolute_error']['mean']:.3f}"))
        lines.append(command(f"{label}LogErr", f"{row['excess_absolute_log_odds']['mean']:.3f}"))
    contrast = simulation["echograph_classic_vs_baselines"]["document_count"]
    lines.append(
        command(
            "EchoDocProbDelta",
            f"{contrast['probability_absolute_error']['candidate_minus_reference']:.3f}",
        )
    )
    lines.append(
        command(
            "EchoDocProbDeltaCI",
            f"[{contrast['probability_absolute_error']['ci_low']:.3f}, {contrast['probability_absolute_error']['ci_high']:.3f}]",
        )
    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "commands": len(lines) - 1}))


if __name__ == "__main__":
    main()
