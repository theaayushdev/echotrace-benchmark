#!/usr/bin/env python3
"""Probe whether public metadata predicts hidden benchmark conditions."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path


def vector(case: dict) -> list[float]:
    docs = case["documents"]
    years = [int(d["published_at"][:4]) for d in docs]
    domains = [d["domain"] for d in docs]
    return [
        sum(years) / len(years),
        len(set(domains)),
        sum("/item/" in d["url"] for d in docs),
        sum(len(d["doc_id"]) for d in docs) / len(docs),
    ]


def distance(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def main() -> None:
    ap = argparse.ArgumentParser()
    root = Path(__file__).parents[1]
    ap.add_argument("--data", type=Path, default=root / "data")
    args = ap.parse_args()
    pub = {
        x["case_id"]: x
        for x in map(
            json.loads, (args.data / "echobench_synthetic_v1_public.jsonl").read_text().splitlines()
        )
    }
    rows = json.loads((args.data / "echobench_synthetic_v1_manifest.json").read_text())["cases"]
    labels = sorted({r["condition"] for r in rows})
    train = [r for r in rows if r["split"] == "train"]
    test = [r for r in rows if r["split"] != "train"]
    centroids = {}
    for label in labels:
        xs = [vector(pub[r["case_id"]]) for r in train if r["condition"] == label]
        centroids[label] = [sum(col) / len(col) for col in zip(*xs)]
    correct = sum(
        min(labels, key=lambda c: distance(vector(pub[r["case_id"]]), centroids[c]))
        == r["condition"]
        for r in test
    )
    test_counts = Counter(r["condition"] for r in test)
    majority = max(test_counts.values()) / len(test)
    accuracy = correct / len(test)
    if accuracy > 0.55:
        raise SystemExit(f"metadata leakage probe failed: {accuracy:.3f} exceeds 0.55")
    print(
        json.dumps(
            {
                "metadata_nearest_centroid_accuracy": accuracy,
                "chance": 1 / len(labels),
                "majority_baseline": majority,
                "preregistered_failure_threshold": 0.55,
                "features": [
                    "mean_year",
                    "unique_domain_count",
                    "url_path_shape",
                    "mean_id_length",
                ],
                "interpretation": "The probe is below the preregistered failure threshold. It tests only these coarse metadata features and is not proof that all shortcuts are absent.",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
