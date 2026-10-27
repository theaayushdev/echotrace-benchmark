from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Literal

Verdict = Literal["supported", "contradicted", "insufficient"]


@dataclass(frozen=True)
class Document:
    doc_id: str
    url: str
    title: str
    text: str
    published_at: str
    domain: str
    author: str = ""
    outbound_links: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.doc_id or not self.text.strip():
            raise ValueError("document requires doc_id and non-empty text")
        datetime.fromisoformat(self.published_at.replace("Z", "+00:00"))

    def public_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["outbound_links"] = list(self.outbound_links)
        return value

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Document":
        return cls(**{**value, "outbound_links": tuple(value.get("outbound_links", []))})


@dataclass(frozen=True)
class LineageEdge:
    source_id: str
    derivative_id: str
    transformation: str


@dataclass(frozen=True)
class GoldClaim:
    text: str
    verdict: Verdict
    supporting_doc_ids: tuple[str, ...]
    contradicting_doc_ids: tuple[str, ...]


@dataclass(frozen=True)
class BenchmarkCase:
    case_id: str
    micro_world_id: str
    query: str
    documents: tuple[Document, ...]
    condition: str
    gold_claims: tuple[GoldClaim, ...]
    gold_lineage_edges: tuple[LineageEdge, ...]
    gold_root_count: int
    gold_families: tuple[tuple[str, ...], ...]
    split: Literal["train", "validation", "test"]
    review_status: Literal["generated", "double_reviewed", "adjudicated"] = "generated"

    def to_dict(self, include_gold: bool = True) -> dict[str, Any]:
        result = asdict(self)
        if not include_gold:
            for key in ("gold_claims", "gold_lineage_edges", "gold_root_count", "gold_families"):
                result.pop(key, None)
            result.pop("review_status", None)
            result.pop("condition", None)
            result.pop("micro_world_id", None)
            result.pop("split", None)
        return result

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "BenchmarkCase":
        return cls(
            case_id=value["case_id"],
            micro_world_id=value["micro_world_id"],
            query=value["query"],
            documents=tuple(Document.from_dict(v) for v in value["documents"]),
            condition=value["condition"],
            gold_claims=tuple(
                GoldClaim(
                    text=v["text"],
                    verdict=v["verdict"],
                    supporting_doc_ids=tuple(v["supporting_doc_ids"]),
                    contradicting_doc_ids=tuple(v["contradicting_doc_ids"]),
                )
                for v in value["gold_claims"]
            ),
            gold_lineage_edges=tuple(LineageEdge(**v) for v in value["gold_lineage_edges"]),
            gold_root_count=int(value["gold_root_count"]),
            gold_families=tuple(tuple(v) for v in value["gold_families"]),
            split=value["split"],
            review_status=value.get("review_status", "generated"),
        )


@dataclass(frozen=True)
class ClaimResponse:
    text: str
    verdict: Verdict
    confidence: float
    citations: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.verdict not in {"supported", "contradicted", "insufficient"}:
            raise ValueError(f"invalid verdict: {self.verdict}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("claim confidence must be between zero and one")


@dataclass(frozen=True)
class AgentResponse:
    case_id: str
    answer: str
    claims: tuple[ClaimResponse, ...]
    confidence: float
    citations: tuple[str, ...]
    predicted_evidence_groups: tuple[tuple[str, ...], ...]
    trace: tuple[dict[str, Any], ...] = ()
    usage: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between zero and one")

    @property
    def predicted_root_count(self) -> int:
        return len(self.predicted_evidence_groups)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "AgentResponse":
        return cls(
            case_id=value["case_id"],
            answer=value.get("answer", ""),
            claims=tuple(
                ClaimResponse(
                    text=v["text"],
                    verdict=v["verdict"],
                    confidence=float(v["confidence"]),
                    citations=tuple(v.get("citations", [])),
                )
                for v in value.get("claims", [])
            ),
            confidence=float(value.get("confidence", 0.0)),
            citations=tuple(value.get("citations", [])),
            predicted_evidence_groups=tuple(
                tuple(group) for group in value.get("predicted_evidence_groups", [])
            ),
            trace=tuple(value.get("trace", [])),
            usage=value.get("usage", {}),
            error=value.get("error"),
        )


@dataclass(frozen=True)
class DependencyEdge:
    source_id: str
    derivative_id: str
    probability: float
    features: dict[str, float]


@dataclass(frozen=True)
class DependencyGraph:
    nodes: tuple[str, ...]
    edges: tuple[DependencyEdge, ...]
    evidence_families: tuple[tuple[str, ...], ...]
    inferred_roots: tuple[str, ...]


def validate_response(case: BenchmarkCase, response: AgentResponse) -> None:
    if response.case_id != case.case_id:
        raise ValueError(f"response case_id {response.case_id!r} does not match {case.case_id!r}")
    known = {document.doc_id for document in case.documents}
    referenced = set(response.citations)
    referenced.update(item for claim in response.claims for item in claim.citations)
    grouped = [item for group in response.predicted_evidence_groups for item in group]
    referenced.update(grouped)
    unknown = referenced - known
    if unknown:
        raise ValueError(f"response referenced unknown document IDs: {sorted(unknown)}")
    if len(grouped) != len(set(grouped)):
        raise ValueError("a document appears in more than one predicted evidence group")
