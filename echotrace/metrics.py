from __future__ import annotations

import math
from collections import defaultdict

import numpy as np

from .schemas import AgentResponse, BenchmarkCase, DependencyGraph


def _pair_set(groups: tuple[tuple[str, ...], ...]) -> set[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    for group in groups:
        for index, left in enumerate(group):
            for right in group[index + 1 :]:
                pairs.add(tuple(sorted((left, right))))
    return pairs


def family_pair_f1(gold: tuple[tuple[str, ...], ...], predicted: tuple[tuple[str, ...], ...]) -> float:
    gold_pairs, predicted_pairs = _pair_set(gold), _pair_set(predicted)
    if not gold_pairs and not predicted_pairs:
        return 1.0
    true_positive = len(gold_pairs & predicted_pairs)
    precision = true_positive / len(predicted_pairs) if predicted_pairs else 0.0
    recall = true_positive / len(gold_pairs) if gold_pairs else 0.0
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def dependency_edge_f1(case: BenchmarkCase, graph: DependencyGraph) -> float:
    gold = {(edge.source_id, edge.derivative_id) for edge in case.gold_lineage_edges}
    predicted = {(edge.source_id, edge.derivative_id) for edge in graph.edges}
    if not gold and not predicted:
        return 1.0
    true_positive = len(gold & predicted)
    precision = true_positive / len(predicted) if predicted else 0.0
    recall = true_positive / len(gold) if gold else 0.0
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def score_response(case: BenchmarkCase, response: AgentResponse) -> dict[str, float]:
    predicted_roots = response.predicted_root_count
    citations = set(response.citations)
    claim = case.gold_claims[0]
    decisive = set(claim.supporting_doc_ids) | set(claim.contradicting_doc_ids)
    cited_decisive = citations & decisive
    represented_families = sum(bool(set(family) & citations) for family in case.gold_families)
    verdict_accuracy = float(bool(response.claims) and response.claims[0].verdict == claim.verdict)
    return {
        "root_count_mae": abs(predicted_roots - case.gold_root_count),
        "false_corroboration": float(case.gold_root_count == 1 and predicted_roots >= 2),
        "citation_precision": len(cited_decisive) / len(citations) if citations else 0.0,
        "citation_recall": len(cited_decisive) / len(decisive) if decisive else 0.0,
        "evidence_family_recall": represented_families / len(case.gold_families) if case.gold_families else math.nan,
        "evidence_family_pair_f1": family_pair_f1(case.gold_families, response.predicted_evidence_groups),
        "verdict_accuracy": verdict_accuracy,
        "confidence_brier": (response.confidence - verdict_accuracy) ** 2,
        "confidence": response.confidence,
        "cost_usd": float(response.usage.get("cost_usd", 0.0)),
        "latency_seconds": float(response.usage.get("latency_seconds", 0.0)),
        "error": float(response.error is not None),
    }


def aggregate_scores(cases: list[BenchmarkCase], responses: list[AgentResponse]) -> dict[str, object]:
    case_by_id = {case.case_id: case for case in cases}
    matched = [response for response in responses if response.case_id in case_by_id]
    valid = [response for response in matched if response.error is None]
    rows = [score_response(case_by_id[r.case_id], r) for r in valid]
    if not rows:
        return {
            "n": 0,
            "attempted": len(matched),
            "coverage": 0.0,
            "metrics": {"error": 1.0 if matched else 0.0},
        }
    keys = rows[0].keys()
    metrics = {key: float(np.nanmean([row[key] for row in rows])) for key in keys}
    by_condition: dict[str, list[float]] = defaultdict(list)
    for response in valid:
        if response.case_id in case_by_id:
            by_condition[case_by_id[response.case_id].condition].append(response.confidence)
    confidence_by_condition = {
        condition: float(np.mean(values)) for condition, values in sorted(by_condition.items())
    }
    independent = confidence_by_condition.get("four_independent", confidence_by_condition.get("four_roots", math.nan))
    one_origin = [confidence_by_condition[name] for name in ("single_origin", "verbatim_derivative", "attributed_paraphrase", "unattributed_multihop") if name in confidence_by_condition]
    metrics["confidence_inflation_gap"] = float(np.mean(one_origin) - independent) if one_origin and not math.isnan(independent) else math.nan
    # Ten equal-width bins; this is reported alongside, not instead of, Brier score.
    confidences = np.asarray([row["confidence"] for row in rows])
    outcomes = np.asarray([row["verdict_accuracy"] for row in rows])
    bins = np.minimum((confidences * 10).astype(int), 9)
    metrics["expected_calibration_error"] = float(sum(abs(confidences[bins == index].mean() - outcomes[bins == index].mean()) * np.mean(bins == index) for index in range(10) if np.any(bins == index)))
    metrics["error"] = 1.0 - len(valid) / len(matched)
    metrics["cost_usd"] = float(sum(float(item.usage.get("cost_usd", 0.0)) for item in matched))
    return {
        "n": len(rows),
        "attempted": len(matched),
        "coverage": len(valid) / len(matched),
        "metrics": metrics,
        "confidence_by_condition": confidence_by_condition,
    }


def bootstrap_mean_ci(values: list[float], seed: int = 20260911, samples: int = 10_000) -> tuple[float, float]:
    if not values:
        return math.nan, math.nan
    rng = np.random.default_rng(seed)
    array = np.asarray(values, dtype=float)
    means = np.mean(rng.choice(array, size=(samples, len(array)), replace=True), axis=1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))
