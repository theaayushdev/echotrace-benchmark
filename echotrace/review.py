from __future__ import annotations

import csv
from collections import Counter, defaultdict
from dataclasses import replace
from pathlib import Path

from .io import load_cases, write_cases

CHECKS = ("claim_correct", "lineage_correct", "condition_correct", "no_label_leakage", "fluent")
TRUE_VALUES = {"1", "true", "yes", "y"}
FALSE_VALUES = {"0", "false", "no", "n"}


def _decision(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    raise ValueError(f"invalid review decision {value!r}; use yes/no")


def review_report(dataset_path: str | Path, review_path: str | Path) -> dict[str, object]:
    cases = load_cases(dataset_path)
    case_ids = {case.case_id for case in cases}
    rows: list[dict[str, str]] = []
    errors: list[str] = []
    with Path(review_path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"case_id", "reviewer_id", "round", *CHECKS}
        missing = required - set(reader.fieldnames or ())
        if missing:
            return {"valid": False, "errors": [f"missing columns: {sorted(missing)}"]}
        rows = list(reader)

    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    seen: set[tuple[str, str, str]] = set()
    for line, row in enumerate(rows, start=2):
        case_id, reviewer, round_name = row["case_id"], row["reviewer_id"], row["round"]
        if case_id not in case_ids:
            errors.append(f"line {line}: unknown case_id {case_id}")
        if round_name not in {"independent", "adjudication"}:
            errors.append(f"line {line}: round must be independent or adjudication")
        key = (case_id, reviewer, round_name)
        if key in seen:
            errors.append(f"line {line}: duplicate review {key}")
        seen.add(key)
        try:
            for check in CHECKS:
                _decision(row[check])
        except ValueError as exc:
            errors.append(f"line {line}: {exc}")
        grouped[case_id].append(row)

    if errors:
        return {
            "valid": False,
            "rows": len(rows),
            "case_count": len(cases),
            "status_counts": {"generated": len(cases)},
            "disagreements": 0,
            "statuses": {case_id: "generated" for case_id in case_ids},
            "errors": errors,
        }

    statuses: dict[str, str] = {}
    disagreements = 0
    for case_id in case_ids:
        independent = [row for row in grouped[case_id] if row["round"] == "independent"]
        adjudication = [row for row in grouped[case_id] if row["round"] == "adjudication"]
        if len(independent) > 2:
            errors.append(f"{case_id}: expected exactly two independent reviews")
        if len(adjudication) > 1:
            errors.append(f"{case_id}: expected at most one adjudication")
        distinct_reviewers = {row["reviewer_id"] for row in independent}
        if len(independent) < 2 or len(distinct_reviewers) < 2:
            statuses[case_id] = "generated"
            continue
        values = [tuple(_decision(row[item]) for item in CHECKS) for row in independent]
        agrees = values[0] == values[1]
        disagreements += int(not agrees)
        if agrees and all(values[0]):
            statuses[case_id] = "double_reviewed"
        elif len(adjudication) == 1 and all(_decision(adjudication[0][item]) for item in CHECKS):
            statuses[case_id] = "adjudicated"
        else:
            statuses[case_id] = "generated"
    return {
        "valid": not errors,
        "rows": len(rows),
        "case_count": len(cases),
        "status_counts": dict(Counter(statuses.values())),
        "disagreements": disagreements,
        "statuses": statuses,
        "errors": errors,
    }


def apply_reviews(dataset_path: str | Path, review_path: str | Path, output_path: str | Path) -> dict[str, object]:
    report = review_report(dataset_path, review_path)
    if not report["valid"]:
        raise ValueError("review ledger is invalid: " + "; ".join(report["errors"]))
    statuses = report["statuses"]
    cases = load_cases(dataset_path)
    write_cases(output_path, (replace(case, review_status=statuses[case.case_id]) for case in cases))
    return {key: value for key, value in report.items() if key != "statuses"} | {"output": str(output_path)}
