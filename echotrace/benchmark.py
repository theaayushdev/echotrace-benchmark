from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from .io import load_cases
from .schemas import BenchmarkCase

CONDITIONS = {
    "exact_echo": 1,
    "paraphrase_echo": 1,
    "cross_domain_echo": 1,
    "two_roots": 2,
    "four_roots": 4,
}


def validate_case(case: BenchmarkCase) -> list[str]:
    errors: list[str] = []
    doc_ids = [doc.doc_id for doc in case.documents]
    doc_set = set(doc_ids)
    if len(doc_ids) != 8:
        errors.append(f"{case.case_id}: expected 8 documents, got {len(doc_ids)}")
    if len(doc_set) != len(doc_ids):
        errors.append(f"{case.case_id}: duplicate document ids")
    if case.condition not in CONDITIONS:
        errors.append(f"{case.case_id}: unknown condition {case.condition}")
    elif case.gold_root_count != CONDITIONS[case.condition]:
        errors.append(f"{case.case_id}: wrong root count for condition")
    family_docs = {item for group in case.gold_families for item in group}
    supporter_ids = {item for claim in case.gold_claims for item in claim.supporting_doc_ids}
    if family_docs != supporter_ids:
        errors.append(f"{case.case_id}: family membership differs from supporting documents")
    for edge in case.gold_lineage_edges:
        if edge.source_id not in doc_set or edge.derivative_id not in doc_set:
            errors.append(f"{case.case_id}: lineage edge references missing document")
    for claim in case.gold_claims:
        unknown = (set(claim.supporting_doc_ids) | set(claim.contradicting_doc_ids)) - doc_set
        if unknown:
            errors.append(f"{case.case_id}: claim references missing documents {sorted(unknown)}")
    # Agent-visible text must not contain generator-only labels.
    forbidden = re.compile(
        r"gold_root|micro_world|lineage|echo condition|exact_echo|paraphrase_echo|"
        r"cross_domain_echo|two_roots|four_roots",
        re.I,
    )
    if forbidden.search(case.query):
        errors.append(f"{case.case_id}: hidden-label leakage in query")
    for doc in case.documents:
        public_text = " ".join((doc.doc_id, doc.url, doc.title, doc.text))
        if forbidden.search(public_text):
            errors.append(f"{case.case_id}: hidden-label leakage in {doc.doc_id}")
    return errors


def validate_dataset(path: str | Path) -> dict[str, object]:
    cases = load_cases(path)
    errors = [error for case in cases for error in validate_case(case)]
    counts = Counter(case.split for case in cases)
    condition_counts = Counter(case.condition for case in cases)
    world_splits: dict[str, set[str]] = {}
    for case in cases:
        world_splits.setdefault(case.micro_world_id, set()).add(case.split)
    leaking = sorted(world for world, splits in world_splits.items() if len(splits) != 1)
    if leaking:
        errors.append(f"micro-world split leakage: {leaking}")
    if len(cases) != 400:
        errors.append(f"expected 400 cases, got {len(cases)}")
    expected_splits = {"train": 240, "validation": 60, "test": 100}
    if dict(counts) != expected_splits:
        errors.append(f"expected split counts {expected_splits}, got {dict(counts)}")
    if any(condition_counts[name] != 80 for name in CONDITIONS):
        errors.append(f"unexpected condition counts: {dict(condition_counts)}")
    return {
        "valid": not errors,
        "case_count": len(cases),
        "world_count": len(world_splits),
        "split_counts": dict(counts),
        "condition_counts": dict(condition_counts),
        "review_counts": dict(Counter(case.review_status for case in cases)),
        "errors": errors,
    }
