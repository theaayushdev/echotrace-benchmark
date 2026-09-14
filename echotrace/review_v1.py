"""Validation for blinded, pair-level EchoBench v1 reviews."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

RELATIONSHIPS = {
    "independent",
    "direct_derivative",
    "indirect_derivative",
    "common_dependency",
    "partial_overlap",
    "unrelated",
    "unknown",
}
OBSERVABILITY = {"explicit", "inferable", "indeterminate"}
ACTIONS = {"same_family", "distinct_families", "partial_overlap", "abstain"}
ROUNDS = {"independent", "adjudication"}
REQUIRED_COLUMNS = {
    "case_id",
    "reviewer_id",
    "round",
    "left_doc_id",
    "right_doc_id",
    "relationship",
    "dependency_bases",
    "observability",
    "action",
    "rationale",
    "span_left",
    "span_right",
}


def review_v1_report(
    public_path: str | Path, sample_path: str | Path, ledger_path: str | Path
) -> dict[str, object]:
    public = [
        json.loads(line)
        for line in Path(public_path).read_text(encoding="utf-8").splitlines()
        if line
    ]
    docs = {row["case_id"]: {doc["doc_id"] for doc in row["documents"]} for row in public}
    sample = set(json.loads(Path(sample_path).read_text(encoding="utf-8"))["case_ids"])
    errors: list[str] = []
    with Path(ledger_path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or ())
        if not REQUIRED_COLUMNS <= columns:
            return {
                "valid": False,
                "errors": [f"missing columns: {sorted(REQUIRED_COLUMNS - columns)}"],
            }
        rows = list(reader)
    independent: dict[str, set[str]] = defaultdict(set)
    labels: dict[tuple[str, str, str], set[tuple[str, str, str]]] = defaultdict(set)
    adjudicated: set[tuple[str, str, str]] = set()
    seen: set[tuple[str, str, str, str, str]] = set()
    for number, row in enumerate(rows, start=2):
        case_id, reviewer, round_name = row["case_id"], row["reviewer_id"], row["round"]
        pair = tuple(sorted((row["left_doc_id"], row["right_doc_id"])))
        if case_id not in sample:
            errors.append(f"line {number}: case is not in the blinded sample")
        elif not set(pair) <= docs.get(case_id, set()) or pair[0] == pair[1]:
            errors.append(f"line {number}: invalid document pair")
        if not reviewer or round_name not in ROUNDS:
            errors.append(f"line {number}: invalid reviewer or round")
        if (
            row["relationship"] not in RELATIONSHIPS
            or row["observability"] not in OBSERVABILITY
            or row["action"] not in ACTIONS
        ):
            errors.append(f"line {number}: invalid taxonomy label")
        if not row["rationale"].strip():
            errors.append(f"line {number}: rationale is required")
        key = (case_id, reviewer, round_name, *pair)
        if key in seen:
            errors.append(f"line {number}: duplicate review row")
        seen.add(key)
        label_key = (case_id, *pair)
        label = (row["relationship"], row["observability"], row["action"])
        if round_name == "independent":
            independent[case_id].add(reviewer)
            labels[label_key].add(label)
        else:
            adjudicated.add(label_key)
    for case_id in sample:
        if len(independent[case_id]) < 2:
            errors.append(f"{case_id}: requires two independent reviewers")
    disagreements = sum(1 for values in labels.values() if len(values) > 1)
    for pair, values in labels.items():
        if len(values) > 1 and pair not in adjudicated:
            errors.append(f"{pair[0]}:{pair[1]}:{pair[2]} requires adjudication")
    return {
        "valid": not errors,
        "sample_cases": len(sample),
        "rows": len(rows),
        "disagreements": disagreements,
        "errors": errors,
    }


AUTHOR_COLUMNS = {
    "case_id",
    "author_id",
    "left_doc_id",
    "right_doc_id",
    "relationship",
    "dependency_bases",
    "observability",
    "action",
    "observed_verdict",
    "linguistic_quality",
    "shortcut_free",
    "rationale",
    "span_left",
    "span_right",
}
DEPENDENCY_BASES = {
    "upstream_document",
    "primary_study",
    "dataset",
    "measurement_event",
    "sample_cohort",
    "editorial_organizational",
    "distinct_observation",
    "unknown",
}


def author_audit_report(
    gold_path: str | Path, sample_path: str | Path, ledger_path: str | Path
) -> dict[str, object]:
    """Validate and score the explicitly single-author, gold-blind audit."""
    gold = {
        row["case_id"]: row
        for row in map(json.loads, Path(gold_path).read_text(encoding="utf-8").splitlines())
    }
    sample = set(json.loads(Path(sample_path).read_text(encoding="utf-8"))["case_ids"])
    errors: list[str] = []
    with Path(ledger_path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or ())
        if not AUTHOR_COLUMNS <= columns:
            return {
                "valid": False,
                "release_ready": False,
                "errors": [f"missing columns: {sorted(AUTHOR_COLUMNS - columns)}"],
            }
        rows = list(reader)
    by_case: dict[str, list[dict[str, str]]] = defaultdict(list)
    seen: set[tuple[str, str, str]] = set()
    for number, row in enumerate(rows, start=2):
        case_id = row["case_id"]
        pair = tuple(sorted((row["left_doc_id"], row["right_doc_id"])))
        if case_id not in sample:
            errors.append(f"line {number}: case is not in the 66-case audit sample")
        if not row["author_id"].strip() or pair[0] == pair[1]:
            errors.append(f"line {number}: author and distinct document IDs are required")
        if (
            row["relationship"] not in RELATIONSHIPS
            or row["observability"] not in OBSERVABILITY
            or row["action"] not in ACTIONS
        ):
            errors.append(f"line {number}: invalid taxonomy label")
        bases = {item.strip() for item in row["dependency_bases"].split(";") if item.strip()}
        if not bases or not bases <= DEPENDENCY_BASES:
            errors.append(f"line {number}: invalid dependency_bases")
        if row["observed_verdict"] not in {"supported", "contradicted", "insufficient"}:
            errors.append(f"line {number}: invalid observed_verdict")
        if row["linguistic_quality"].lower() not in {"yes", "no"} or row[
            "shortcut_free"
        ].lower() not in {"yes", "no"}:
            errors.append(f"line {number}: quality fields must be yes or no")
        if not row["rationale"].strip():
            errors.append(f"line {number}: rationale is required")
        key = (case_id, *pair)
        if key in seen:
            errors.append(f"line {number}: duplicate pair")
        seen.add(key)
        by_case[case_id].append(row)
    pair_matches = verdict_matches = quality_rows = 0
    for case_id in sample:
        expected_rows = gold.get(case_id, {}).get("gold_relationships", [])
        expected = {(item["left_doc_id"], item["right_doc_id"]): item for item in expected_rows}
        actual = {
            tuple(sorted((row["left_doc_id"], row["right_doc_id"]))): row
            for row in by_case[case_id]
        }
        if set(actual) != set(expected):
            errors.append(f"{case_id}: audit must contain exactly the six claim-relevant pairs")
            continue
        observed_verdicts = {row["observed_verdict"] for row in actual.values()}
        if len(observed_verdicts) != 1:
            errors.append(f"{case_id}: observed verdict must be consistent across pair rows")
        verdict_matches += int(observed_verdicts == {gold[case_id]["gold_claim"]["verdict"]})
        for pair, row in actual.items():
            target = expected[pair]
            pair_matches += int(
                (row["relationship"], row["observability"], row["action"])
                == (target["relationship"], target["observability"], target["action"])
            )
            quality_rows += int(
                row["linguistic_quality"].lower() == "yes" and row["shortcut_free"].lower() == "yes"
            )
    structurally_valid = not errors
    expected_pair_total = len(sample) * 6
    release_ready = (
        structurally_valid
        and verdict_matches == len(sample)
        and pair_matches == expected_pair_total
        and quality_rows == expected_pair_total
    )
    return {
        "valid": structurally_valid,
        "release_ready": release_ready,
        "sample_cases": len(sample),
        "rows": len(rows),
        "verdict_agreement": verdict_matches / len(sample) if sample else 0.0,
        "pair_label_agreement": pair_matches / expected_pair_total if expected_pair_total else 0.0,
        "quality_pass_rate": quality_rows / expected_pair_total if expected_pair_total else 0.0,
        "errors": errors,
    }
