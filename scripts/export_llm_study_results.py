#!/usr/bin/env python3
"""Export v1.4 benchmark and LLM-study results as LaTeX commands.

Held-out test results use unprefixed commands. Validation-split development results use the
``Dev`` prefix so they can never be mistaken for held-out results. Anything missing is written as
\\pending so the manuscript can never show a number that has not been measured.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "artifacts/llm-study-v1.4/test/analysis.json"
STUDY_DEV = ROOT / "artifacts/llm-study-v1.4/dev-r2/analysis.json"
DETECTION_VALIDATION = ROOT / "artifacts/v1.4-dev/detection-validation-v1.4.json"
DETECTION_TEST = ROOT / "artifacts/v1.4-dev/detection-test-v1.4.json"
PROBE = ROOT / "artifacts/v1.4-dev/leakage-probe-v1.4.json"
OUTPUT = ROOT / "paper/generated/llm-study-results.tex"
MODELS = {"Qwen": "qwen", "Gptoss": "gptoss", "Gemini": "gemini"}
ARMS = {"Standard": "standard", "Reminder": "reminder", "Echograph": "echograph", "Oracle": "oracle"}
DETECTORS = {"Url": "url_count", "One": "all_one_family", "Domain": "domain_grouping",
             "Bow": "lexical_bow", "Tfidf": "tfidf", "Minilm": "minilm",
             "Echo": "echograph_classic", "NoLinks": "echograph_no_links"}
PENDING = r"\pending"


def command(name: str, value: str) -> str:
    return f"\\newcommand{{\\{name}}}{{{value}}}"


def number(value, digits=3) -> str:
    return PENDING if value is None else f"{value:.{digits}f}"


def interval(result) -> str:
    if not result or result.get("estimate") is None:
        return PENDING
    return f"[{result['ci_low']:.3f}, {result['ci_high']:.3f}]"


def load(path: Path, split: str | None = None):
    if not path.exists():
        return None
    document = json.loads(path.read_text(encoding="utf-8"))
    if split and document.get("split") != split:
        raise SystemExit(f"{path} is not a {split} artifact")
    return document


def study_lines(study, prefix="") -> list[str]:
    lines = [command(prefix + "StudyStatus", "complete" if study else PENDING)]
    for model_tag, model in MODELS.items():
        tag = prefix + model_tag
        result = (study or {}).get("models", {}).get(model)
        coverage = (result or {}).get("coverage", {})
        lines.append(command(f"{tag}Coverage", number(min(coverage.values()) if coverage else None)))
        for arm_tag, arm in ARMS.items():
            metrics = (result or {}).get("arms", {}).get(arm, {})
            ci = metrics.get("ci", {})
            cell = tag + arm_tag
            lines += [
                command(cell + "Fcr", number(metrics.get("false_corroboration_rate"))),
                command(cell + "FcrCI", interval(ci.get("false_corroboration_rate"))),
                command(cell + "Sens", number(metrics.get("confidence_sensitivity"))),
                command(cell + "SensCI", interval(ci.get("confidence_sensitivity"))),
                command(cell + "Acc", number(metrics.get("verdict_accuracy"))),
                command(cell + "Under", number(metrics.get("undercount_rate_independent"))),
                command(cell + "DetAbst", number(metrics.get("determinate_abstention_rate"))),
                command(cell + "Ceil", number(metrics.get("confidence_ceiling_rate"))),
                command(cell + "N", str(metrics["n"]) if "n" in metrics else PENDING),
                command(cell + "Abst", number(metrics.get("ambiguous_abstention_rate"))),
                command(cell + "CountErr", number(metrics.get("count_abs_error"))),
            ]
        contrasts = (result or {}).get("contrasts", {})
        for name, key in (("EchoStd", "echograph_minus_standard"), ("RemStd", "reminder_minus_standard"),
                          ("EchoRem", "echograph_minus_reminder"), ("OracleEcho", "oracle_minus_echograph")):
            for metric_tag, metric in (("Fcr", "false_corroboration_rate"), ("Acc", "verdict_accuracy"),
                                       ("Under", "undercount_rate_independent")):
                value = contrasts.get(key, {}).get(metric, {})
                lines += [command(f"{tag}{name}{metric_tag}", number(value.get("estimate"))),
                          command(f"{tag}{name}{metric_tag}CI", interval(value))]
        holm = (result or {}).get("h3_holm_p")
        lines.append(command(f"{tag}HolmP", number(holm)))
    return lines


def detection_lines(document, suffix) -> list[str]:
    lines = []
    for tag, method in DETECTORS.items():
        result = (document or {}).get("methods", {}).get(method, {})
        lines += [
            command(f"{tag}FOne{suffix}", number(result.get("exclusive_family_pair_f1", {}).get("mean"))),
            command(f"{tag}MAE{suffix}", number(result.get("root_count_mae", {}).get("mean"))),
        ]
    shared = (document or {}).get("methods", {}).get("echograph_classic", {}).get(
        "by_condition", {}).get("shared_dataset", {})
    lines.append(command(f"EchoSharedFOne{suffix}", number(shared.get("f1"))))
    echo = (document or {}).get("methods", {}).get("echograph_classic", {}).get(
        "exclusive_family_pair_f1", {})
    lines.append(command(f"EchoFOne{suffix}CI", interval(
        {"estimate": echo.get("mean"), "ci_low": echo.get("ci_low"), "ci_high": echo.get("ci_high")})))
    return lines


def main() -> None:
    study = load(STUDY, "test")
    probe = load(PROBE)
    lines = ["% Generated by scripts/export_llm_study_results.py; do not edit manually."]
    lines += study_lines(study)
    lines += study_lines(load(STUDY_DEV, "validation"), "Dev")
    lines += detection_lines(load(DETECTION_VALIDATION, "validation"), "Val")
    lines += detection_lines(load(DETECTION_TEST, "test"), "Test")
    lines.append(command("ProbeAccFour", number((probe or {}).get("metadata_nearest_centroid_accuracy"))))
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "study_complete": study is not None,
                      "pending": sum(PENDING in line for line in lines)}))


if __name__ == "__main__":
    main()
