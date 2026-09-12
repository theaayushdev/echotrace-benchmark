from __future__ import annotations

from abc import ABC, abstractmethod

from ..echo_graph import EchoGraph
from ..schemas import AgentResponse, BenchmarkCase


class ResearchAgent(ABC):
    def max_request_cost_usd(self) -> float:
        return 0.0

    @abstractmethod
    def answer(
        self,
        case: BenchmarkCase,
        method: str = "standard",
        echo_graph: EchoGraph | None = None,
        track: str = "naturalistic",
    ) -> AgentResponse:
        raise NotImplementedError
