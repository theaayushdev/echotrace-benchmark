from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass

from .schemas import Document

TOKEN_RE = re.compile(r"[a-zA-Z0-9]+")


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


@dataclass(frozen=True)
class SearchResult:
    doc_id: str
    title: str
    url: str
    snippet: str
    score: float


class CorpusSearch:
    """Small deterministic BM25 index used as the controlled web."""

    def __init__(self, documents: tuple[Document, ...]):
        self.documents = {doc.doc_id: doc for doc in documents}
        self.term_frequencies = {
            doc.doc_id: Counter(tokenize(f"{doc.title} {doc.text}")) for doc in documents
        }
        self.lengths = {doc_id: sum(tf.values()) for doc_id, tf in self.term_frequencies.items()}
        self.average_length = sum(self.lengths.values()) / max(1, len(self.lengths))
        document_frequency: dict[str, int] = defaultdict(int)
        for frequencies in self.term_frequencies.values():
            for term in frequencies:
                document_frequency[term] += 1
        total = len(documents)
        self.idf = {
            term: math.log(1 + (total - count + 0.5) / (count + 0.5))
            for term, count in document_frequency.items()
        }

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        k1, b = 1.5, 0.75
        terms = tokenize(query)
        scored: list[tuple[float, Document]] = []
        for doc_id, frequencies in self.term_frequencies.items():
            score = 0.0
            length = self.lengths[doc_id]
            for term in terms:
                tf = frequencies.get(term, 0)
                if tf:
                    denominator = tf + k1 * (1 - b + b * length / self.average_length)
                    score += self.idf.get(term, 0.0) * tf * (k1 + 1) / denominator
            scored.append((score, self.documents[doc_id]))
        scored.sort(key=lambda item: (-item[0], item[1].doc_id))
        return [
            SearchResult(
                doc_id=doc.doc_id,
                title=doc.title,
                url=doc.url,
                snippet=doc.text[:220],
                score=round(score, 6),
            )
            for score, doc in scored[:top_k]
        ]

    def open_document(self, doc_id: str) -> Document:
        try:
            return self.documents[doc_id]
        except KeyError as exc:
            raise KeyError(f"unknown document: {doc_id}") from exc

