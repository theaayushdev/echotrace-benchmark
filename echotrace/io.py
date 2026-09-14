from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable

from .schemas import AgentResponse, BenchmarkCase


def load_cases(path: str | Path) -> list[BenchmarkCase]:
    with Path(path).open(encoding="utf-8") as handle:
        return [BenchmarkCase.from_dict(json.loads(line)) for line in handle if line.strip()]


def load_v1_cases(
    public_path: str | Path, gold_path: str | Path, manifest_path: str | Path
) -> list[BenchmarkCase]:
    """Join EchoBench v1's public and gold projections for trusted evaluation.

    Agents are given only public rows by the runner/prompt layer.  This loader is
    intentionally an evaluator-side operation: the public JSONL alone is not a
    runnable benchmark because it omits splits and labels.
    """
    with Path(public_path).open(encoding="utf-8") as handle:
        public_rows = [json.loads(line) for line in handle if line.strip()]
    with Path(gold_path).open(encoding="utf-8") as handle:
        gold_rows = [json.loads(line) for line in handle if line.strip()]
    manifest_document = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    if manifest_document.get("version") not in {"1.1", "1.2-candidate", "1.3-candidate"}:
        raise ValueError("unsupported EchoBench manifest version")
    manifest = manifest_document["cases"]
    public_by_id = {row["case_id"]: row for row in public_rows}
    gold_by_id = {row["case_id"]: row for row in gold_rows}
    manifest_by_id = {row["case_id"]: row for row in manifest}
    ids = set(public_by_id)
    if not ids or ids != set(gold_by_id) or ids != set(manifest_by_id):
        raise ValueError("v1 public, gold, and manifest case IDs must match exactly")
    if len(public_by_id) != len(public_rows) or len(gold_by_id) != len(gold_rows):
        raise ValueError("v1 case IDs must be unique")
    cases: list[BenchmarkCase] = []
    for case_id in sorted(ids):
        public, gold, manifest_row = public_by_id[case_id], gold_by_id[case_id], manifest_by_id[case_id]
        for field in ("condition", "split"):
            if gold[field] != manifest_row[field]:
                raise ValueError(f"{case_id}: gold and manifest disagree on {field}")
        claim = gold["gold_claim"]
        combined = {
            "case_id": case_id,
            "micro_world_id": gold["micro_world_id"],
            "query": public["query"],
            "documents": public["documents"],
            "condition": gold["condition"],
            "gold_claims": [claim],
            "gold_lineage_edges": gold.get("gold_lineage_edges", []),
            "gold_root_count": gold["gold_root_count"],
            "gold_families": gold["gold_families"],
            "split": gold["split"],
            "review_status": gold.get("review_status", "generated"),
        }
        cases.append(BenchmarkCase.from_dict(combined))
    return cases


def write_cases(path: str | Path, cases: Iterable[BenchmarkCase]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        for case in cases:
            handle.write(json.dumps(case.to_dict(), sort_keys=True) + "\n")


def load_responses(path: str | Path) -> list[AgentResponse]:
    with Path(path).open(encoding="utf-8") as handle:
        return [AgentResponse.from_dict(json.loads(line)) for line in handle if line.strip()]


def append_response(path: str | Path, response: AgentResponse) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(response.to_dict(), sort_keys=True) + "\n")


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
