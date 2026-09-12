#!/usr/bin/env python3
"""RQ2/RQ3 simulation: evidence-count posteriors versus source-family posteriors."""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from echotrace.baselines import (
    group_by_dense_vectors,
    group_by_domain,
    group_by_similarity,
    group_by_tfidf,
)
from echotrace.echo_graph import (
    EchoGraph,
    LogisticDependencyClassifier,
    training_pairs,
)
from echotrace.freeze import mark_test_run_complete, validate_cpu_freeze
from echotrace.io import load_v1_cases

PRIORS = (0.1, 0.25, 0.5, 0.75, 0.9)
LIKELIHOOD_RATIOS = (1.5, 2.0, 3.0, 5.0)
SEED = 20260911


def posterior(prior: float, likelihood_ratio: float, count: int, verdict: str) -> float:
    direction = 1 if verdict == "supported" else -1 if verdict == "contradicted" else 0
    odds = prior / (1.0 - prior) * likelihood_ratio ** (direction * count)
    return odds / (1.0 + odds)


def relevant(case):
    ids = {doc_id for family in case.gold_families for doc_id in family}
    return [doc for doc in case.documents if doc.doc_id in ids]


def summarize(rows):
    by_world = defaultdict(list)
    for row in rows:
        by_world[row["world"]].append(row)
    worlds = sorted(by_world)
    rng = np.random.default_rng(SEED)
    result = {}
    for metric in ("probability_absolute_error", "excess_absolute_log_odds"):
        values = np.array([np.mean([row[metric] for row in by_world[world]]) for world in worlds])
        boot = np.mean(rng.choice(values, size=(10_000, len(values)), replace=True), axis=1)
        result[metric] = {
            "mean": float(np.mean(values)),
            "median": float(np.median(values)),
            "ci_low": float(np.quantile(boot, 0.025)),
            "ci_high": float(np.quantile(boot, 0.975)),
        }
    return result


def paired_difference(candidate_rows, reference_rows, metric_name: str):
    candidate_by_world = defaultdict(list)
    reference_by_world = defaultdict(list)
    for row in candidate_rows:
        candidate_by_world[row["world"]].append(row[metric_name])
    for row in reference_rows:
        reference_by_world[row["world"]].append(row[metric_name])
    worlds = sorted(set(candidate_by_world) & set(reference_by_world))
    differences = np.array(
        [
            np.mean(candidate_by_world[world]) - np.mean(reference_by_world[world])
            for world in worlds
        ]
    )
    rng = np.random.default_rng(SEED)
    boot = np.mean(rng.choice(differences, size=(10_000, len(differences)), replace=True), axis=1)
    return {
        "candidate_minus_reference": float(np.mean(differences)),
        "ci_low": float(np.quantile(boot, 0.025)),
        "ci_high": float(np.quantile(boot, 0.975)),
        "paired_unit": "micro_world",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--public", default=str(ROOT / "data" / "echobench_synthetic_v1_public.jsonl")
    )
    parser.add_argument("--gold", default=str(ROOT / "data" / "echobench_synthetic_v1_gold.jsonl"))
    parser.add_argument(
        "--manifest", default=str(ROOT / "data" / "echobench_synthetic_v1_manifest.json")
    )
    parser.add_argument(
        "--settings", default=str(ROOT / "artifacts" / "detection-settings-v1.1.json")
    )
    parser.add_argument("--split", choices=("validation", "test"), default="validation")
    parser.add_argument("--freeze-manifest")
    parser.add_argument("--include-semantic", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()
    freeze_document = None
    if args.split == "test":
        if not args.freeze_manifest or not args.output:
            raise SystemExit("test simulation requires --freeze-manifest and --output")
        if Path(args.output).exists():
            raise SystemExit("refusing to overwrite an existing held-out test artifact")
        freeze_document = validate_cpu_freeze(args.freeze_manifest, ROOT, "confidence_simulation")
    cases = load_v1_cases(args.public, args.gold, args.manifest)
    train = [
        case for case in cases if case.split == "train" and case.condition != "ambiguous_provenance"
    ]
    selected = [
        case
        for case in cases
        if case.split == args.split and case.condition != "ambiguous_provenance"
    ]
    settings = json.loads(Path(args.settings).read_text(encoding="utf-8"))
    rows, labels = training_pairs(train)
    classifier = LogisticDependencyClassifier.fit(rows, labels)
    threshold = float(settings["thresholds"]["echograph_classic"])
    graph = EchoGraph(classifier, threshold)
    semantic = None
    semantic_meta = settings.get("semantic_model")
    if args.include_semantic:
        if not semantic_meta or "minilm" not in settings["thresholds"]:
            raise SystemExit("semantic simulation requires pinned semantic settings")
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise SystemExit("semantic simulation requires `pip install .[cpu-research]`") from exc
        model = SentenceTransformer(
            semantic_meta["model_id"], revision=semantic_meta["revision"], device="cpu"
        )
        locations, texts = [], []
        for case in selected:
            for doc in relevant(case):
                locations.append((case.case_id, doc.doc_id))
                texts.append(doc.text)
        vectors = model.encode(
            texts, batch_size=64, normalize_embeddings=True, show_progress_bar=False
        )
        semantic = {location: vector.tolist() for location, vector in zip(locations, vectors)}
    methods = {
        "document_count": lambda case, docs: len(docs),
        "domain_grouping": lambda case, docs: len(group_by_domain(docs)),
        "lexical_bow": lambda case, docs: len(
            group_by_similarity(docs, float(settings["thresholds"]["lexical_bow"]))
        ),
        "tfidf": lambda case, docs: len(
            group_by_tfidf(docs, float(settings["thresholds"]["tfidf"]))
        ),
        "echograph_classic": lambda case, docs: len(graph.infer(docs).evidence_families),
        "oracle_family_count": lambda case, docs: -1,
    }
    if semantic is not None:
        semantic_threshold = float(settings["thresholds"]["minilm"])
        methods["minilm"] = lambda case, docs, semantic_threshold=semantic_threshold: len(
            group_by_dense_vectors(
                docs,
                [semantic[case.case_id, doc.doc_id] for doc in docs],
                semantic_threshold,
            )
        )
    results = {name: [] for name in methods}
    sensitivity = {name: defaultdict(list) for name in methods}
    for case in selected:
        docs = relevant(case)
        verdict = case.gold_claims[0].verdict
        for prior in PRIORS:
            for likelihood_ratio in LIKELIHOOD_RATIOS:
                oracle = posterior(prior, likelihood_ratio, case.gold_root_count, verdict)
                for name, infer_count in methods.items():
                    count = (
                        case.gold_root_count
                        if name == "oracle_family_count"
                        else infer_count(case, docs)
                    )
                    estimate = posterior(prior, likelihood_ratio, count, verdict)
                    direction = (
                        1 if verdict == "supported" else -1 if verdict == "contradicted" else 0
                    )
                    row = {
                        "world": case.micro_world_id,
                        "condition": case.condition,
                        "verdict": verdict,
                        "prior": prior,
                        "likelihood_ratio": likelihood_ratio,
                        "estimated_count": count,
                        "oracle_count": case.gold_root_count,
                        "probability_absolute_error": abs(estimate - oracle),
                        "excess_absolute_log_odds": abs(
                            direction * (count - case.gold_root_count) * math.log(likelihood_ratio)
                        ),
                    }
                    results[name].append(row)
                    sensitivity[name][str(likelihood_ratio)].append(
                        row["probability_absolute_error"]
                    )
    comparisons = {
        reference: {
            metric: paired_difference(results["echograph_classic"], results[reference], metric)
            for metric in ("probability_absolute_error", "excess_absolute_log_odds")
        }
        for reference in ("document_count", "domain_grouping", "lexical_bow", "tfidf", "minilm")
        if reference in results
    }
    report = {
        "study": "confidence_inflation_simulation",
        "benchmark_version": "1.1",
        "split": args.split,
        "test_access": args.split == "test",
        "assumptions": {
            "priors": PRIORS,
            "likelihood_ratios": LIKELIHOOD_RATIOS,
            "conditional_independence_unit": "source_family",
            "insufficient_evidence_likelihood_ratio": 1.0,
        },
        "methods": {
            name: {
                **summarize(rows),
                "mean_probability_error_by_likelihood_ratio": {
                    lr: float(np.mean(values)) for lr, values in sensitivity[name].items()
                },
            }
            for name, rows in results.items()
        },
        "echograph_classic_vs_baselines": comparisons,
    }
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered, encoding="utf-8")
    if freeze_document is not None:
        mark_test_run_complete(args.freeze_manifest, freeze_document, "confidence_simulation")
    print(rendered, end="")


if __name__ == "__main__":
    main()
