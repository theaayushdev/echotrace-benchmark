from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

from ..baselines import group_by_domain, group_by_similarity, mmr_select
from ..echo_graph import EchoGraph
from ..schemas import AgentResponse, BenchmarkCase
from ..search import CorpusSearch
from .base import ResearchAgent


@dataclass(frozen=True)
class ModelConfig:
    model_id: str
    endpoint: str
    key_env: str
    input_cost_per_million: float = 0.0
    output_cost_per_million: float = 0.0
    max_output_tokens: int = 1200
    max_input_tokens: int = 20_000
    retry_attempts: int = 3

    @classmethod
    def from_file(cls, path: str, name: str) -> "ModelConfig":
        with open(path, encoding="utf-8") as handle:
            configs = json.load(handle)
        if name not in configs:
            raise KeyError(f"model config not found: {name}")
        return cls(**configs[name])


def _extract_json(text: str) -> dict[str, object]:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        if text.lstrip().startswith("json"):
            text = text.lstrip()[4:].lstrip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("model response contained no JSON object")
    return json.loads(text[start : end + 1])


class OpenAICompatibleAgent(ResearchAgent):
    def __init__(self, config: ModelConfig, timeout_seconds: int = 120):
        self.config = config
        self.timeout_seconds = timeout_seconds

    def max_request_cost_usd(self) -> float:
        return (
            self.config.max_input_tokens * self.config.input_cost_per_million
            + self.config.max_output_tokens * self.config.output_cost_per_million
        ) / 1_000_000

    def _prompt(self, case: BenchmarkCase, method: str, graph: EchoGraph | None, track: str) -> str:
        search = CorpusSearch(case.documents)
        candidates = [
            search.open_document(result.doc_id) for result in search.search(case.query, top_k=8)
        ]
        if method == "mmr":
            documents = mmr_select(case.query, candidates, top_k=6)
        elif method == "domain_dedup":
            seen: set[str] = set()
            documents = []
            for doc in candidates:
                if doc.domain not in seen:
                    documents.append(doc)
                    seen.add(doc.domain)
                if len(documents) == 6:
                    break
        elif method == "echograph":
            documents = (graph or EchoGraph()).rerank(case.query, candidates, top_k=6)
        elif method == "gold_graph":
            family_by_doc = {
                doc_id: index for index, family in enumerate(case.gold_families) for doc_id in family
            }
            documents, used = [], set()
            for doc in candidates:
                family = family_by_doc.get(doc.doc_id, f"other:{doc.doc_id}")
                if family not in used:
                    documents.append(doc)
                    used.add(family)
                if len(documents) == 6:
                    break
            for doc in candidates:
                if len(documents) == 6:
                    break
                if doc not in documents:
                    documents.append(doc)
        else:
            documents = candidates[:6]
        family_note = ""
        if method == "echograph":
            inferred = (graph or EchoGraph()).infer(documents)
            family_note = (
                "\nA source-dependence detector proposed these evidence families. Treat the grouping as "
                f"uncertain metadata, not truth: {json.dumps(inferred.evidence_families)}\n"
            )
        elif method == "domain_dedup":
            family_note = (
                "\nA domain-only baseline proposed these groups. A shared domain is only a "
                f"heuristic: {json.dumps(group_by_domain(documents))}\n"
            )
        elif method == "embedding_dedup":
            family_note = (
                "\nA lexical-similarity baseline proposed these groups. Treat them as uncertain: "
                f"{json.dumps(group_by_similarity(documents))}\n"
            )
        elif method == "gold_graph":
            visible = {doc.doc_id for doc in documents}
            visible_families = tuple(
                tuple(doc_id for doc_id in family if doc_id in visible)
                for family in case.gold_families
                if any(doc_id in visible for doc_id in family)
            )
            family_note = (
                "\nFor this diagnostic upper bound only, the known evidence families are: "
                f"{json.dumps(visible_families)}\n"
            )
        document_text = "\n\n".join(
            f"[{doc.doc_id}] {doc.title}\nURL: {doc.url}\nPublished: {doc.published_at}\n"
            f"Links: {list(doc.outbound_links)}\n{doc.text}"
            for doc in documents
        )
        audit_instruction = (
            "Explicitly audit which cited documents have independent origins; abstain from a provenance judgment when needed."
            if track == "diagnostic"
            else "Answer as a normal careful research assistant using only the documents shown."
        )
        return f"""You are evaluating evidence in a closed document collection.
{audit_instruction}
{family_note}
Question: {case.query}

Documents:
{document_text}

Return JSON only with this shape:
{{
  "answer": "concise answer",
  "claims": [{{"text": "claim", "verdict": "supported|contradicted|insufficient",
               "confidence": 0.0, "citations": ["document ids"]}}],
  "confidence": 0.0,
  "citations": ["document ids"],
  "predicted_evidence_groups": [["ids sharing one origin"], ["another origin"]]
}}
Use only document IDs that appear above."""

    def answer(
        self,
        case: BenchmarkCase,
        method: str = "standard",
        echo_graph: EchoGraph | None = None,
        track: str = "naturalistic",
    ) -> AgentResponse:
        key = os.environ.get(self.config.key_env)
        if not key:
            raise RuntimeError(f"missing API credential in {self.config.key_env}")
        prompt = self._prompt(case, method, echo_graph, track)
        payload = {
            "model": self.config.model_id,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "max_tokens": self.config.max_output_tokens,
        }
        request = urllib.request.Request(
            self.config.endpoint,
            data=json.dumps(payload).encode(),
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            method="POST",
        )
        started = time.monotonic()
        raw = None
        for attempt in range(self.config.retry_attempts):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                    raw = json.loads(response.read())
                break
            except urllib.error.HTTPError as exc:
                body = exc.read().decode(errors="replace")[:500]
                if exc.code not in {429, 500, 502, 503, 504} or attempt + 1 == self.config.retry_attempts:
                    raise RuntimeError(f"model endpoint returned HTTP {exc.code}: {body}") from exc
            except urllib.error.URLError as exc:
                if attempt + 1 == self.config.retry_attempts:
                    raise RuntimeError(f"model endpoint unavailable: {exc.reason}") from exc
            time.sleep(min(2**attempt, 8))
        if raw is None:
            raise RuntimeError("model endpoint returned no response")
        latency = time.monotonic() - started
        content = raw["choices"][0]["message"]["content"]
        parsed = _extract_json(content)
        usage = raw.get("usage", {})
        input_tokens = int(usage.get("prompt_tokens", 0))
        output_tokens = int(usage.get("completion_tokens", 0))
        cost = (
            input_tokens * self.config.input_cost_per_million
            + output_tokens * self.config.output_cost_per_million
        ) / 1_000_000
        parsed["case_id"] = case.case_id
        parsed["trace"] = [{"provider_model": self.config.model_id, "track": track, "method": method}]
        parsed["usage"] = {
            **usage,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "latency_seconds": latency,
            "cost_usd": cost,
        }
        return AgentResponse.from_dict(parsed)
