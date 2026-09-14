#!/usr/bin/env python3
"""Resume the gold-blind, sole-author EchoBench v1.1 audit in a terminal."""

from __future__ import annotations

import argparse
import csv
import json
from itertools import combinations
from pathlib import Path

RELATIONSHIPS = (
    "independent",
    "direct_derivative",
    "indirect_derivative",
    "common_dependency",
    "partial_overlap",
    "unrelated",
    "unknown",
)
OBSERVABILITY = ("explicit", "inferable", "indeterminate")
ACTIONS = ("same_family", "distinct_families", "partial_overlap", "abstain")
VERDICTS = ("supported", "contradicted", "insufficient")
YES_NO = ("yes", "no")
FIELDS = (
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
)


def choose(prompt: str, values: tuple[str, ...]) -> str:
    while True:
        print(f"{prompt}: " + ", ".join(f"{i + 1}={value}" for i, value in enumerate(values)))
        answer = input("> ").strip()
        if answer in values:
            return answer
        if answer.isdigit() and 1 <= int(answer) <= len(values):
            return values[int(answer) - 1]
        print("Please enter a listed number or exact label.")


def nonempty(prompt: str) -> str:
    while True:
        answer = input(f"{prompt}: ").strip()
        if answer:
            return answer
        print("A response is required.")


def select_four(documents: list[dict]) -> list[dict]:
    while True:
        answer = input("Enter the four claim-relevant document numbers, comma-separated: ").strip()
        try:
            indexes = [int(item.strip()) - 1 for item in answer.split(",")]
        except ValueError:
            indexes = []
        if len(set(indexes)) == 4 and all(0 <= index < len(documents) for index in indexes):
            return [documents[index] for index in sorted(indexes)]
        print("Select exactly four distinct document numbers.")


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--packet", type=Path, default=root / "annotations/v1/author_audit_packet.jsonl"
    )
    parser.add_argument("--ledger", type=Path, default=root / "annotations/v1/author_audit.csv")
    parser.add_argument("--author-id", default="Ayush Dev")
    args = parser.parse_args()
    cases = [
        json.loads(line) for line in args.packet.read_text(encoding="utf-8").splitlines() if line
    ]
    with args.ledger.open(newline="", encoding="utf-8") as handle:
        existing = list(csv.DictReader(handle))
    completed = {
        row["case_id"]
        for row in existing
        if sum(item["case_id"] == row["case_id"] for item in existing) == 6
    }
    remaining = [case for case in cases if case["case_id"] not in completed]
    print(
        f"Completed {len(completed)}/{len(cases)} cases; {len(remaining)} remain. Gold labels are not loaded."
    )
    for position, case in enumerate(remaining, start=len(completed) + 1):
        print(f"\nCASE {position}/{len(cases)} — {case['case_id']}")
        print(f"Question: {case['query']}\nClaim: {case['focal_claim']}")
        for index, doc in enumerate(case["documents"], start=1):
            print(f"\n[{index}] {doc['doc_id']} | {doc['published_at']} | {doc['domain']}")
            print(doc["text"])
            if doc["outbound_links"]:
                print("Links: " + ", ".join(doc["outbound_links"]))
        relevant = select_four(case["documents"])
        verdict = choose("Observed verdict", VERDICTS)
        quality = choose("Is the language grammatical and natural enough for the study?", YES_NO)
        shortcut = choose("Is the case free of an unintended label/condition shortcut?", YES_NO)
        new_rows = []
        for left, right in combinations(sorted(relevant, key=lambda item: item["doc_id"]), 2):
            print(f"\nPAIR {left['doc_id']} <> {right['doc_id']}")
            relationship = choose("Relationship", RELATIONSHIPS)
            basis = nonempty(
                "Dependency basis (e.g. upstream_document, dataset, distinct_observation, unknown)"
            )
            observability = choose("Observability", OBSERVABILITY)
            action = choose("Evaluation action", ACTIONS)
            rationale = nonempty("Short rationale")
            span_left = nonempty("Smallest supporting span from left document, or NONE")
            span_right = nonempty("Smallest supporting span from right document, or NONE")
            new_rows.append(
                {
                    "case_id": case["case_id"],
                    "author_id": args.author_id,
                    "left_doc_id": left["doc_id"],
                    "right_doc_id": right["doc_id"],
                    "relationship": relationship,
                    "dependency_bases": basis,
                    "observability": observability,
                    "action": action,
                    "observed_verdict": verdict,
                    "linguistic_quality": quality,
                    "shortcut_free": shortcut,
                    "rationale": rationale,
                    "span_left": span_left,
                    "span_right": span_right,
                }
            )
        with args.ledger.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writerows(new_rows)
        print("Saved this case. Press Ctrl+C safely at any time; the next run resumes.")


if __name__ == "__main__":
    main()
