from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from itertools import combinations

import numpy as np

from .schemas import DependencyEdge, DependencyGraph, Document
from .search import tokenize

NUMBER_RE = re.compile(r"\b\d+(?:\.\d+)?\b")
ATTRIBUTION_RE = re.compile(r"\b(according to|based on|earlier report|previously published)\b", re.I)


def _ngrams(tokens: list[str], size: int = 5) -> set[tuple[str, ...]]:
    return {tuple(tokens[index : index + size]) for index in range(max(0, len(tokens) - size + 1))}


def _jaccard(left: set[object], right: set[object]) -> float:
    return len(left & right) / len(left | right) if left or right else 0.0


def _cosine_bow(left: list[str], right: list[str]) -> float:
    a, b = Counter(left), Counter(right)
    common = set(a) & set(b)
    numerator = sum(a[item] * b[item] for item in common)
    denominator = math.sqrt(sum(v * v for v in a.values()) * sum(v * v for v in b.values()))
    return numerator / denominator if denominator else 0.0


def pair_features(older: Document, newer: Document) -> dict[str, float]:
    older_tokens, newer_tokens = tokenize(older.text), tokenize(newer.text)
    direct_link = float(older.url in newer.outbound_links)
    return {
        "bias": 1.0,
        "direct_link": direct_link,
        "attribution": float(bool(ATTRIBUTION_RE.search(newer.text))),
        "token_jaccard": _jaccard(set(older_tokens), set(newer_tokens)),
        "fivegram_jaccard": _jaccard(_ngrams(older_tokens), _ngrams(newer_tokens)),
        "bow_cosine": _cosine_bow(older_tokens, newer_tokens),
        "numeric_overlap": _jaccard(set(NUMBER_RE.findall(older.text)), set(NUMBER_RE.findall(newer.text))),
        "same_domain": float(older.domain == newer.domain),
        "days_apart": min(
            abs(
                (
                    datetime.fromisoformat(newer.published_at.replace("Z", "+00:00"))
                    - datetime.fromisoformat(older.published_at.replace("Z", "+00:00"))
                ).days
            )
            / 30.0,
            1.0,
        ),
    }


FEATURE_ORDER = (
    "bias",
    "direct_link",
    "attribution",
    "token_jaccard",
    "fivegram_jaccard",
    "bow_cosine",
    "numeric_overlap",
    "same_domain",
    "days_apart",
)


@dataclass
class LogisticDependencyClassifier:
    weights: np.ndarray

    @classmethod
    def default(cls) -> "LogisticDependencyClassifier":
        # Conservative interpretable prior; benchmark training replaces these weights.
        return cls(np.array([-4.2, 4.5, 1.1, 1.4, 2.4, 2.0, 0.8, 0.2, -0.1], dtype=float))

    def predict_proba(self, features: dict[str, float]) -> float:
        vector = np.array([features[name] for name in FEATURE_ORDER], dtype=float)
        logit = float(np.clip(np.dot(self.weights, vector), -30, 30))
        return 1.0 / (1.0 + math.exp(-logit))

    @classmethod
    def fit(
        cls,
        rows: list[dict[str, float]],
        labels: list[int],
        learning_rate: float = 0.15,
        steps: int = 1500,
        l2: float = 0.01,
        disabled_features: set[str] | None = None,
    ) -> "LogisticDependencyClassifier":
        if not rows or len(rows) != len(labels):
            raise ValueError("training rows and labels must be non-empty and aligned")
        x = np.array([[row[name] for name in FEATURE_ORDER] for row in rows], dtype=float)
        for feature in disabled_features or set():
            if feature != "bias":
                x[:, FEATURE_ORDER.index(feature)] = 0.0
        y = np.array(labels, dtype=float)
        weights = np.zeros(x.shape[1], dtype=float)
        for _ in range(steps):
            logits = np.clip(x @ weights, -30, 30)
            predictions = 1.0 / (1.0 + np.exp(-logits))
            gradient = (x.T @ (predictions - y)) / len(y)
            penalty = l2 * weights
            penalty[0] = 0.0
            weights -= learning_rate * (gradient + penalty)
        return cls(weights)


class _UnionFind:
    def __init__(self, nodes: list[str]):
        self.parent = {node: node for node in nodes}

    def find(self, node: str) -> str:
        while self.parent[node] != node:
            self.parent[node] = self.parent[self.parent[node]]
            node = self.parent[node]
        return node

    def union(self, left: str, right: str) -> None:
        left_root, right_root = self.find(left), self.find(right)
        if left_root != right_root:
            self.parent[right_root] = left_root


class EchoGraph:
    def __init__(self, classifier: LogisticDependencyClassifier | None = None, threshold: float = 0.60):
        self.classifier = classifier or LogisticDependencyClassifier.default()
        self.threshold = threshold

    def infer(self, documents: list[Document] | tuple[Document, ...]) -> DependencyGraph:
        ordered = sorted(documents, key=lambda doc: (doc.published_at, doc.doc_id))
        edges: list[DependencyEdge] = []
        union = _UnionFind([doc.doc_id for doc in ordered])
        incoming: set[str] = set()
        for first, second in combinations(ordered, 2):
            older, newer = (first, second) if first.published_at <= second.published_at else (second, first)
            features = pair_features(older, newer)
            probability = self.classifier.predict_proba(features)
            if probability >= self.threshold:
                edges.append(DependencyEdge(older.doc_id, newer.doc_id, probability, features))
                union.union(older.doc_id, newer.doc_id)
                incoming.add(newer.doc_id)
        grouped: dict[str, list[str]] = {}
        for doc in ordered:
            grouped.setdefault(union.find(doc.doc_id), []).append(doc.doc_id)
        families = tuple(tuple(sorted(group)) for group in grouped.values())
        roots = tuple(
            min(group, key=lambda doc_id: next(doc.published_at for doc in ordered if doc.doc_id == doc_id))
            for group in families
        )
        return DependencyGraph(
            nodes=tuple(doc.doc_id for doc in ordered),
            edges=tuple(edges),
            evidence_families=families,
            inferred_roots=roots,
        )

    def rerank(self, query: str, documents: list[Document], top_k: int = 6) -> list[Document]:
        graph = self.infer(documents)
        family_by_doc = {
            doc_id: family_index
            for family_index, family in enumerate(graph.evidence_families)
            for doc_id in family
        }
        query_tokens = set(tokenize(query))
        scored = sorted(
            documents,
            key=lambda doc: (
                -_jaccard(query_tokens, set(tokenize(f"{doc.title} {doc.text}"))),
                doc.published_at,
                doc.doc_id,
            ),
        )
        selected: list[Document] = []
        used_families: set[int] = set()
        for doc in scored:
            family = family_by_doc[doc.doc_id]
            if family not in used_families:
                selected.append(doc)
                used_families.add(family)
                if len(selected) == top_k:
                    return selected
        for doc in scored:
            if doc not in selected:
                selected.append(doc)
                if len(selected) == top_k:
                    break
        return selected


def training_pairs(cases: list[object]) -> tuple[list[dict[str, float]], list[int]]:
    rows: list[dict[str, float]] = []
    labels: list[int] = []
    for case in cases:
        documents = {doc.doc_id: doc for doc in case.documents}
        same_family = {
            tuple(sorted((left, right)))
            for family in case.gold_families
            for index, left in enumerate(family)
            for right in family[index + 1 :]
        }
        supporters = {item for family in case.gold_families for item in family}
        for left_id, right_id in combinations(sorted(supporters), 2):
            left, right = documents[left_id], documents[right_id]
            older, newer = (left, right) if left.published_at <= right.published_at else (right, left)
            rows.append(pair_features(older, newer))
            labels.append(int(tuple(sorted((older.doc_id, newer.doc_id))) in same_family))
    return rows, labels
