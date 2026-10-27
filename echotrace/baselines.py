from __future__ import annotations

import math
from collections import Counter, defaultdict

from .echo_graph import pair_features
from .schemas import Document
from .search import tokenize


def group_by_domain(documents: list[Document]) -> tuple[tuple[str, ...], ...]:
    groups: dict[str, list[str]] = defaultdict(list)
    for doc in documents:
        groups[doc.domain].append(doc.doc_id)
    return tuple(tuple(ids) for _, ids in sorted(groups.items()))


def group_by_similarity(
    documents: list[Document], threshold: float = 0.82
) -> tuple[tuple[str, ...], ...]:
    parent = {doc.doc_id: doc.doc_id for doc in documents}

    def find(item: str) -> str:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    def union(left: str, right: str) -> None:
        a, b = find(left), find(right)
        if a != b:
            parent[b] = a

    for index, left in enumerate(documents):
        for right in documents[index + 1 :]:
            older, newer = (left, right) if left.published_at <= right.published_at else (right, left)
            if pair_features(older, newer)["bow_cosine"] >= threshold:
                union(left.doc_id, right.doc_id)
    groups: dict[str, list[str]] = defaultdict(list)
    for doc in documents:
        groups[find(doc.doc_id)].append(doc.doc_id)
    return tuple(tuple(sorted(value)) for value in groups.values())


def _cluster_scores(
    documents: list[Document], scores: dict[tuple[str, str], float], threshold: float
) -> tuple[tuple[str, ...], ...]:
    parent = {doc.doc_id: doc.doc_id for doc in documents}

    def find(item: str) -> str:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    for (left, right), score in scores.items():
        if score >= threshold:
            a, b = find(left), find(right)
            if a != b:
                parent[b] = a
    groups: dict[str, list[str]] = defaultdict(list)
    for doc in documents:
        groups[find(doc.doc_id)].append(doc.doc_id)
    return tuple(tuple(sorted(value)) for value in groups.values())


def group_by_tfidf(
    documents: list[Document], threshold: float = 0.72
) -> tuple[tuple[str, ...], ...]:
    """Cluster documents by within-case TF-IDF cosine similarity."""
    token_counts = {doc.doc_id: Counter(tokenize(doc.text)) for doc in documents}
    document_frequency = Counter(token for counts in token_counts.values() for token in counts)
    total = len(documents)
    vectors: dict[str, dict[str, float]] = {}
    for doc_id, counts in token_counts.items():
        vectors[doc_id] = {
            token: count * (math.log((1 + total) / (1 + document_frequency[token])) + 1.0)
            for token, count in counts.items()
        }

    def cosine(left: dict[str, float], right: dict[str, float]) -> float:
        numerator = sum(value * right.get(token, 0.0) for token, value in left.items())
        denominator = math.sqrt(sum(value * value for value in left.values()) * sum(value * value for value in right.values()))
        return numerator / denominator if denominator else 0.0

    scores = {}
    for index, left in enumerate(documents):
        for right in documents[index + 1 :]:
            scores[left.doc_id, right.doc_id] = cosine(vectors[left.doc_id], vectors[right.doc_id])
    return _cluster_scores(documents, scores, threshold)


def group_by_dense_vectors(
    documents: list[Document], vectors: list[list[float]], threshold: float
) -> tuple[tuple[str, ...], ...]:
    """Cluster precomputed normalized semantic vectors without coupling the core to ML packages."""
    if len(documents) != len(vectors):
        raise ValueError("documents and vectors must align")
    scores = {}
    for index, left in enumerate(documents):
        for offset, right in enumerate(documents[index + 1 :], start=index + 1):
            scores[left.doc_id, right.doc_id] = sum(a * b for a, b in zip(vectors[index], vectors[offset]))
    return _cluster_scores(documents, scores, threshold)


def mmr_select(query: str, documents: list[Document], top_k: int = 6, diversity: float = 0.35) -> list[Document]:
    query_terms = set(tokenize(query))

    def similarity(left: set[str], right: set[str]) -> float:
        return len(left & right) / len(left | right) if left or right else 0.0

    doc_terms = {doc.doc_id: set(tokenize(f"{doc.title} {doc.text}")) for doc in documents}
    selected: list[Document] = []
    remaining = list(documents)
    while remaining and len(selected) < top_k:
        def score(doc: Document) -> tuple[float, str]:
            relevance = similarity(query_terms, doc_terms[doc.doc_id])
            redundancy = max(
                (similarity(doc_terms[doc.doc_id], doc_terms[item.doc_id]) for item in selected),
                default=0.0,
            )
            return relevance - diversity * redundancy, doc.doc_id

        chosen = max(remaining, key=score)
        selected.append(chosen)
        remaining.remove(chosen)
    return selected
