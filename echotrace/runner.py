from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .agents.base import ResearchAgent
from .echo_graph import EchoGraph, LogisticDependencyClassifier, training_pairs
from .io import append_response, load_responses
from .metrics import dependency_edge_f1, family_pair_f1
from .schemas import BenchmarkCase, validate_response


def _case_fingerprint(cases: list[BenchmarkCase]) -> str:
    payload = "\n".join(json.dumps(case.to_dict(), sort_keys=True) for case in cases)
    return hashlib.sha256(payload.encode()).hexdigest()


def _agent_identity(agent: ResearchAgent) -> dict[str, object]:
    identity: dict[str, object] = {"class": type(agent).__name__}
    config = getattr(agent, "config", None)
    if config is not None:
        for field in ("model_id", "revision", "endpoint", "max_output_tokens", "max_input_tokens", "load_in_4bit"):
            if hasattr(config, field):
                identity[field] = getattr(config, field)
    return identity


def trained_echo_graph(cases: list[BenchmarkCase], threshold: float = 0.60) -> EchoGraph:
    train_cases = [case for case in cases if case.split == "train"]
    rows, labels = training_pairs(train_cases)
    return EchoGraph(LogisticDependencyClassifier.fit(rows, labels), threshold=threshold)


def evaluate_echo_graph(
    cases: list[BenchmarkCase], split: str, threshold: float = 0.60
) -> dict[str, object]:
    graph = trained_echo_graph(cases, threshold)
    selected = [case for case in cases if case.split == split]
    rows = []
    for case in selected:
        inferred = graph.infer(case.documents)
        rows.append(
            {
                "edge_f1": dependency_edge_f1(case, inferred),
                "family_pair_f1": family_pair_f1(case.gold_families, inferred.evidence_families),
                "root_count_mae": abs(len(inferred.inferred_roots) - case.gold_root_count),
            }
        )
    return {
        "split": split,
        "threshold": threshold,
        "n": len(rows),
        "metrics": {
            name: sum(row[name] for row in rows) / len(rows)
            for name in ("edge_f1", "family_pair_f1", "root_count_mae")
        },
    }


def run_experiment(
    cases: list[BenchmarkCase],
    agent: ResearchAgent,
    output_path: str | Path,
    method: str,
    track: str,
    budget_usd: float,
    threshold: float = 0.60,
    training_cases: list[BenchmarkCase] | None = None,
) -> dict[str, object]:
    output = Path(output_path)
    training = training_cases or cases
    manifest_path = output.with_suffix(output.suffix + ".manifest.json")
    manifest = {
        "case_fingerprint": _case_fingerprint(cases),
        "training_fingerprint": _case_fingerprint(training) if method == "echograph" else None,
        "case_count": len(cases),
        "method": method,
        "track": track,
        "threshold": threshold,
        "agent": _agent_identity(agent),
    }
    if output.exists():
        if not manifest_path.exists():
            raise RuntimeError(f"refusing to resume {output}: run manifest is missing")
        existing_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if existing_manifest != manifest:
            raise RuntimeError(f"refusing to resume {output}: run manifest does not match")
    else:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    completed: dict[str, object] = {}
    if output.exists():
        completed = {response.case_id: response for response in load_responses(output)}
    graph = trained_echo_graph(training, threshold) if method == "echograph" else None
    spent = sum(float(response.usage.get("cost_usd", 0.0)) for response in completed.values())
    attempted, errors = 0, 0
    for case in cases:
        if case.case_id in completed:
            continue
        if spent + agent.max_request_cost_usd() > budget_usd:
            break
        attempted += 1
        try:
            response = agent.answer(case, method=method, echo_graph=graph, track=track)
            validate_response(case, response)
        except Exception as exc:  # Preserve failure as data and continue the batch.
            from .schemas import AgentResponse

            errors += 1
            response = AgentResponse(
                case_id=case.case_id,
                answer="",
                claims=(),
                confidence=0.0,
                citations=(),
                predicted_evidence_groups=(),
                error=f"{type(exc).__name__}: {exc}",
            )
        append_response(output, response)
        spent += float(response.usage.get("cost_usd", 0.0))
    return {
        "attempted": attempted,
        "errors": errors,
        "completed_total": len(completed) + attempted,
        "cost_usd": spent,
        "output": str(output),
    }


def write_freeze_manifest(
    output: str | Path,
    dataset_path: str | Path,
    config_paths: list[str | Path],
) -> dict[str, object]:
    from datetime import datetime, timezone

    from .io import sha256_file

    files = [Path(dataset_path), *(Path(item) for item in config_paths)]
    manifest = {
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "files": {str(path): sha256_file(path) for path in files},
        "statement": "Test labels, prompts, model IDs, and thresholds are frozen before final runs.",
    }
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest
