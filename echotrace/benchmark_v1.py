"""Validation for the separated public/gold EchoBench-Synthetic v1 release."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from .io import load_v1_cases


def validate_v1_dataset(
    public_path: str | Path, gold_path: str | Path, manifest_path: str | Path
) -> dict[str, object]:
    manifest_document = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    if manifest_document.get("version") != "1.1":
        return {
            "valid": False,
            "case_count": 0,
            "errors": ["expected benchmark manifest version 1.1"],
        }
    try:
        cases = load_v1_cases(public_path, gold_path, manifest_path)
    except (KeyError, TypeError, ValueError) as exc:
        return {"valid": False, "case_count": 0, "errors": [str(exc)]}
    errors: list[str] = []
    gold_by_id = {
        row["case_id"]: row
        for row in map(json.loads, Path(gold_path).read_text(encoding="utf-8").splitlines())
    }
    manifest_by_id = {row["case_id"]: row for row in manifest_document["cases"]}
    split_counts = Counter(case.split for case in cases)
    verdict_counts = Counter((case.split, case.gold_claims[0].verdict) for case in cases)
    expected_splits = {"train": 1650, "validation": 330, "test": 660}
    if dict(split_counts) != expected_splits:
        errors.append(f"expected split counts {expected_splits}, got {dict(split_counts)}")
    for split, per_verdict in (("train", 550), ("validation", 110), ("test", 220)):
        for verdict in ("supported", "contradicted", "insufficient"):
            if verdict_counts[split, verdict] != per_verdict:
                errors.append(
                    f"{split}/{verdict}: expected {per_verdict}, got {verdict_counts[split, verdict]}"
                )
    worlds: dict[str, set[str]] = {}
    for case in cases:
        worlds.setdefault(case.micro_world_id, set()).add(case.split)
        claim = case.gold_claims[0]
        if claim.verdict == "supported" and not claim.supporting_doc_ids:
            errors.append(f"{case.case_id}: supported case has no supporting documents")
        if claim.verdict == "contradicted" and not claim.contradicting_doc_ids:
            errors.append(f"{case.case_id}: contradicted case has no contradicting documents")
        if claim.verdict == "insufficient" and (
            claim.supporting_doc_ids or claim.contradicting_doc_ids
        ):
            errors.append(f"{case.case_id}: insufficient case has decisive gold evidence")
        relevant = set(gold_by_id[case.case_id]["gold_claim"].get("relevant_doc_ids", []))
        manifest_row = manifest_by_id[case.case_id]
        if manifest_row.get("condition") == "ambiguous_provenance":
            if case.gold_root_count != 0 or case.gold_families:
                errors.append(
                    f"{case.case_id}: ambiguous provenance must abstain from family-count gold"
                )
        elif len(relevant) != 4:
            errors.append(
                f"{case.case_id}: expected four claim-relevant documents, got {len(relevant)}"
            )
    leaking = sorted(world for world, splits in worlds.items() if len(splits) != 1)
    if leaking:
        errors.append(f"micro-world split leakage: {leaking}")
    return {
        "valid": not errors,
        "case_count": len(cases),
        "world_count": len(worlds),
        "split_counts": dict(split_counts),
        "split_verdict_counts": {
            f"{split}:{verdict}": count for (split, verdict), count in verdict_counts.items()
        },
        "errors": errors,
    }
