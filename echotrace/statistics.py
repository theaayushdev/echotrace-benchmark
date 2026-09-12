from __future__ import annotations

import math
from collections import defaultdict

import numpy as np

from .metrics import score_response
from .schemas import AgentResponse, BenchmarkCase


def _world_metric(cases: list[BenchmarkCase], responses: list[AgentResponse], metric: str) -> dict[str, float]:
    case_by_id = {case.case_id: case for case in cases}
    values: dict[str, list[float]] = defaultdict(list)
    for response in responses:
        if response.error is not None:
            continue
        case = case_by_id.get(response.case_id)
        if case is not None:
            values[case.micro_world_id].append(score_response(case, response)[metric])
    return {world: float(np.mean(items)) for world, items in values.items()}


def paired_comparison(
    cases: list[BenchmarkCase],
    baseline: list[AgentResponse],
    candidate: list[AgentResponse],
    metric: str,
    samples: int = 10_000,
    seed: int = 20260911,
) -> dict[str, float | int]:
    left, right = _world_metric(cases, baseline, metric), _world_metric(cases, candidate, metric)
    worlds = sorted(set(left) & set(right))
    if not worlds:
        raise ValueError("runs have no matched micro-worlds")
    differences = np.asarray([right[world] - left[world] for world in worlds])
    rng = np.random.default_rng(seed)
    boot = np.mean(rng.choice(differences, size=(samples, len(differences)), replace=True), axis=1)
    signs = rng.choice((-1.0, 1.0), size=(samples, len(differences)))
    null_means = np.abs(np.mean(signs * differences, axis=1))
    observed = abs(float(np.mean(differences)))
    p_value = (float(np.sum(null_means >= observed)) + 1.0) / (samples + 1.0)
    return {
        "n_worlds": len(worlds),
        "candidate_minus_baseline": float(np.mean(differences)),
        "ci_low": float(np.quantile(boot, 0.025)),
        "ci_high": float(np.quantile(boot, 0.975)),
        "p_value": p_value,
    }


def holm_adjust(p_values: dict[str, float]) -> dict[str, float]:
    ordered = sorted(p_values, key=p_values.get)
    adjusted: dict[str, float] = {}
    running = 0.0
    total = len(ordered)
    for rank, name in enumerate(ordered):
        running = max(running, (total - rank) * p_values[name])
        adjusted[name] = min(1.0, running)
    return adjusted


def mixed_effects_note() -> str:
    try:
        import statsmodels  # noqa: F401
    except ImportError:
        return "not run: install the research extra to fit mixed-effects models"
    return "available: fit the prespecified model after frozen real-model runs"
