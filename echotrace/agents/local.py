"""Pinned local Transformers agent for the frozen open-weight study."""
from __future__ import annotations

import time
from dataclasses import dataclass

from ..echo_graph import EchoGraph
from ..schemas import AgentResponse, BenchmarkCase
from .api import OpenAICompatibleAgent, _extract_json
from .base import ResearchAgent


@dataclass(frozen=True)
class LocalModelConfig:
    model_id: str = "Qwen/Qwen2.5-7B-Instruct"
    revision: str = "REPLACE_WITH_COMMIT_HASH"
    max_output_tokens: int = 1200
    max_input_tokens: int = 20_000
    load_in_4bit: bool = True


class LocalTransformersAgent(ResearchAgent):
    """Lazy-loaded deterministic local model; dependencies are optional."""

    def __init__(self, config: LocalModelConfig):
        self.config = config
        self._model = None
        self._tokenizer = None

    def _load(self) -> None:
        if self._model is not None:
            return
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        except ImportError as exc:
            raise RuntimeError("local inference requires `pip install .[local]`") from exc
        if not torch.cuda.is_available():
            raise RuntimeError("the frozen local study requires a CUDA-capable GPU")
        kwargs: dict[str, object] = {"revision": self.config.revision, "device_map": "auto"}
        if self.config.load_in_4bit:
            kwargs["quantization_config"] = BitsAndBytesConfig(load_in_4bit=True)
        self._tokenizer = AutoTokenizer.from_pretrained(self.config.model_id, revision=self.config.revision)
        self._model = AutoModelForCausalLM.from_pretrained(self.config.model_id, **kwargs)

    def answer(self, case: BenchmarkCase, method: str = "standard", echo_graph: EchoGraph | None = None, track: str = "naturalistic") -> AgentResponse:
        self._load()
        assert self._model is not None and self._tokenizer is not None
        # Reuse the shared prompt construction without making a network call.
        prompt = OpenAICompatibleAgent._prompt(self, case, method, echo_graph, track)
        messages = [{"role": "user", "content": prompt}]
        rendered = self._tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self._tokenizer(rendered, return_tensors="pt").to(self._model.device)
        started = time.monotonic()
        output = self._model.generate(**inputs, do_sample=False, max_new_tokens=self.config.max_output_tokens)
        latency = time.monotonic() - started
        completion = output[0][inputs.input_ids.shape[-1] :]
        parsed = _extract_json(self._tokenizer.decode(completion, skip_special_tokens=True))
        parsed.update({
            "case_id": case.case_id,
            "trace": [{"provider_model": self.config.model_id, "revision": self.config.revision, "track": track, "method": method, "quantization": "4bit" if self.config.load_in_4bit else "none"}],
            "usage": {"input_tokens": int(inputs.input_ids.shape[-1]), "output_tokens": int(completion.shape[-1]), "cost_usd": 0.0, "latency_seconds": latency},
        })
        return AgentResponse.from_dict(parsed)
