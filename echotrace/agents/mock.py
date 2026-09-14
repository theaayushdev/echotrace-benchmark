from __future__ import annotations

import re
from collections import Counter

from ..baselines import group_by_domain, group_by_similarity
from ..echo_graph import EchoGraph
from ..schemas import AgentResponse, BenchmarkCase, ClaimResponse
from ..search import CorpusSearch
from .base import ResearchAgent

PERCENT_RE = re.compile(r"\b(\d+) percent\b", re.I)


class MockResearchAgent(ResearchAgent):
    """Deterministic baseline for smoke tests; not a scientific model result."""

    def answer(
        self,
        case: BenchmarkCase,
        method: str = "standard",
        echo_graph: EchoGraph | None = None,
        track: str = "naturalistic",
    ) -> AgentResponse:
        search = CorpusSearch(case.documents)
        retrieved = [search.open_document(item.doc_id) for item in search.search(case.query, top_k=8)]
        values: list[str] = []
        by_value: dict[str, list[object]] = {}
        for doc in retrieved:
            matches = PERCENT_RE.findall(doc.text)
            if matches:
                value = matches[0]
                values.append(value)
                by_value.setdefault(value, []).append(doc)
        chosen = Counter(values).most_common(1)[0][0] if values else "unknown"
        evidence = by_value.get(chosen, [])
        if method == "gold_graph":
            groups = case.gold_families
        elif method == "echograph":
            graph = (echo_graph or EchoGraph()).infer(evidence)
            groups = graph.evidence_families
        elif method == "domain_dedup":
            groups = group_by_domain(evidence)
        elif method in {"embedding_dedup", "mmr"}:
            groups = group_by_similarity(evidence)
        else:
            groups = tuple((doc.doc_id,) for doc in evidence)
        citations = tuple(doc.doc_id for doc in evidence)
        confidence = min(0.95, 0.45 + 0.1 * len(groups))
        answer = f"The reported reduction was {chosen} percent."
        return AgentResponse(
            case_id=case.case_id,
            answer=answer,
            claims=(ClaimResponse(answer, "supported", confidence, citations),),
            confidence=confidence,
            citations=citations,
            predicted_evidence_groups=groups,
            trace=({"tool": "search", "result_count": len(retrieved), "track": track},),
            usage={"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0, "latency_seconds": 0.0},
        )
