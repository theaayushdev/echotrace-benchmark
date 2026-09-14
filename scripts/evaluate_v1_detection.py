#!/usr/bin/env python3
"""Tune or evaluate CPU-only source-family detection on EchoBench v1.1."""

from __future__ import annotations

import argparse
import json
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
from echotrace.metrics import family_pair_f1

SEED = 20260911
GRID = [round(value, 2) for value in np.arange(0.30, 0.96, 0.05)]
ABLATIONS = {
    "echograph_no_links": {"direct_link"},
    "echograph_no_attribution": {"attribution"},
    "echograph_no_lexical": {"token_jaccard", "fivegram_jaccard", "bow_cosine"},
    "echograph_no_numeric": {"numeric_overlap"},
    "echograph_no_chronology": {"days_apart"},
    "echograph_no_domain": {"same_domain"},
}


def relevant(case):
    ids = {doc_id for family in case.gold_families for doc_id in family}
    return tuple(doc for doc in case.documents if doc.doc_id in ids)


def dense_vectors(cases, model_id: str, revision: str):
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError("semantic baseline requires `pip install .[cpu-research]`") from exc
    model = SentenceTransformer(model_id, revision=revision, device="cpu")
    texts, locations = [], []
    for case in cases:
        for doc in relevant(case):
            locations.append((case.case_id, doc.doc_id))
            texts.append(doc.text)
    encoded = model.encode(texts, batch_size=64, normalize_embeddings=True, show_progress_bar=False)
    return {location: vector.tolist() for location, vector in zip(locations, encoded)}


def rows_for(cases, infer):
    rows = []
    for case in cases:
        predicted = infer(case, relevant(case))
        rows.append(
            {
                "world": case.micro_world_id,
                "condition": case.condition,
                "f1": family_pair_f1(case.gold_families, predicted),
                "mae": abs(len(predicted) - case.gold_root_count),
            }
        )
    return rows


def summarize(rows):
    rng = np.random.default_rng(SEED)
    worlds = sorted({row["world"] for row in rows})
    by_world = {world: [row for row in rows if row["world"] == world] for world in worlds}

    def metric(name):
        values = np.array([np.mean([row[name] for row in by_world[world]]) for world in worlds])
        boot = np.mean(rng.choice(values, size=(10_000, len(values)), replace=True), axis=1)
        return {
            "mean": float(np.mean(values)),
            "median": float(np.median(values)),
            "ci_low": float(np.quantile(boot, 0.025)),
            "ci_high": float(np.quantile(boot, 0.975)),
        }

    conditions = defaultdict(list)
    for row in rows:
        conditions[row["condition"]].append(row)
    return {
        "exclusive_family_pair_f1": metric("f1"),
        "root_count_mae": metric("mae"),
        "by_condition": {
            name: {
                "f1": float(np.mean([row["f1"] for row in values])),
                "mae": float(np.mean([row["mae"] for row in values])),
            }
            for name, values in sorted(conditions.items())
        },
    }


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


def choose_threshold(cases, factory):
    candidates = []
    for threshold in GRID:
        rows = rows_for(cases, factory(threshold))
        candidates.append(
            {
                "threshold": threshold,
                "mae": float(np.mean([row["mae"] for row in rows])),
                "f1": float(np.mean([row["f1"] for row in rows])),
            }
        )
    return min(
        candidates, key=lambda row: (row["mae"], -row["f1"], abs(row["threshold"] - 0.5))
    ), candidates


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--public", default=str(ROOT / "data" / "echobench_synthetic_v1_public.jsonl")
    )
    parser.add_argument("--gold", default=str(ROOT / "data" / "echobench_synthetic_v1_gold.jsonl"))
    parser.add_argument(
        "--manifest", default=str(ROOT / "data" / "echobench_synthetic_v1_manifest.json")
    )
    parser.add_argument("--split", choices=("validation", "test"), default="validation")
    parser.add_argument("--settings")
    parser.add_argument("--tune", action="store_true")
    parser.add_argument("--include-semantic", action="store_true")
    parser.add_argument("--freeze-manifest")
    parser.add_argument("--output")
    args = parser.parse_args()
    manifest_document = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    benchmark_version = manifest_document.get("version")
    if benchmark_version not in {"1.1", "1.2-candidate", "1.3-candidate"}:
        raise SystemExit("unsupported EchoBench manifest version")
    if args.settings is None:
        args.settings = str(ROOT / "artifacts" / f"detection-settings-v{benchmark_version}.json")
    freeze_document = None
    if args.split == "test":
        if args.tune or not args.freeze_manifest or not args.output:
            raise SystemExit(
                "test evaluation requires frozen settings, --freeze-manifest, and --output"
            )
        if Path(args.output).exists():
            raise SystemExit("refusing to overwrite an existing held-out test artifact")
        freeze_document = validate_cpu_freeze(args.freeze_manifest, ROOT, "detection")
    cases = load_v1_cases(args.public, args.gold, args.manifest)
    train = [case for case in cases if case.split == "train" and case.gold_root_count > 0]
    selected = [
        case for case in cases if case.split == args.split and case.gold_root_count > 0
    ]
    feature_rows, labels = training_pairs(train)
    classifiers = {"echograph_classic": LogisticDependencyClassifier.fit(feature_rows, labels)}
    classifiers.update(
        {
            name: LogisticDependencyClassifier.fit(feature_rows, labels, disabled_features=disabled)
            for name, disabled in ABLATIONS.items()
        }
    )
    semantic_id = "sentence-transformers/all-MiniLM-L6-v2"
    semantic_revision = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
    # Revision is intentionally pinned; fail rather than silently use a moving model.
    semantic = (
        dense_vectors(selected, semantic_id, semantic_revision) if args.include_semantic else None
    )

    factories = {
        "lexical_bow": lambda threshold: (
            lambda case, docs: group_by_similarity(list(docs), threshold)
        ),
        "tfidf": lambda threshold: lambda case, docs: group_by_tfidf(list(docs), threshold),
    }
    for name, classifier in classifiers.items():
        factories[name] = lambda threshold, classifier=classifier: (
            lambda case, docs: EchoGraph(classifier, threshold).infer(docs).evidence_families
        )
    if semantic is not None:
        factories["minilm"] = lambda threshold: (
            lambda case, docs: group_by_dense_vectors(
                list(docs), [semantic[case.case_id, doc.doc_id] for doc in docs], threshold
            )
        )

    settings_path = Path(args.settings)
    curves = {}
    if args.tune:
        settings = {
            "version": benchmark_version,
            "selection_split": "validation",
            "objective": "root_count_mae_then_pair_f1",
            "thresholds": {},
            "semantic_model": {"model_id": semantic_id, "revision": semantic_revision}
            if args.include_semantic
            else None,
        }
        for name, factory in factories.items():
            best, curves[name] = choose_threshold(selected, factory)
            settings["thresholds"][name] = best["threshold"]
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(
            json.dumps(settings, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    else:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))

    methods = {
        "url_count": lambda case, docs: tuple((doc.doc_id,) for doc in docs),
        "all_one_family": lambda case, docs: (tuple(doc.doc_id for doc in docs),),
        "domain_grouping": lambda case, docs: group_by_domain(list(docs)),
    }
    methods.update(
        {name: factory(float(settings["thresholds"][name])) for name, factory in factories.items()}
    )
    method_rows = {name: rows_for(selected, infer) for name, infer in methods.items()}
    comparisons = {}
    for reference in ("url_count", "domain_grouping", "lexical_bow", "tfidf", "minilm"):
        if reference in method_rows:
            comparisons[reference] = {
                "exclusive_family_pair_f1": paired_difference(
                    method_rows["echograph_classic"], method_rows[reference], "f1"
                ),
                "root_count_mae": paired_difference(
                    method_rows["echograph_classic"], method_rows[reference], "mae"
                ),
            }
    report = {
        "study": "cpu_source_family_detection",
        "benchmark_version": benchmark_version,
        "split": args.split,
        "test_access": args.split == "test",
        "n": len(selected),
        "worlds": len({case.micro_world_id for case in selected}),
        "methods": {name: summarize(rows) for name, rows in method_rows.items()},
        "echograph_classic_vs_baselines": comparisons,
        "thresholds": settings["thresholds"],
        "tuning_curves": curves if args.tune else None,
    }
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered, encoding="utf-8")
    if freeze_document is not None:
        mark_test_run_complete(args.freeze_manifest, freeze_document, "detection")
    print(rendered, end="")


if __name__ == "__main__":
    main()
