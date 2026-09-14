import unittest
from pathlib import Path

from echotrace.agents.mock import MockResearchAgent
from echotrace.io import load_cases
from echotrace.metrics import aggregate_scores, score_response
from echotrace.search import CorpusSearch

ROOT = Path(__file__).resolve().parents[1]
CASES = load_cases(ROOT / "data" / "echobench.jsonl")


class SearchAndMetricTests(unittest.TestCase):
    def test_search_returns_known_documents(self):
        case = CASES[0]
        search = CorpusSearch(case.documents)
        results = search.search(case.query, top_k=4)
        self.assertEqual(len(results), 4)
        self.assertTrue(all(item.doc_id in {doc.doc_id for doc in case.documents} for item in results))

    def test_standard_mock_exhibits_false_corroboration(self):
        case = next(case for case in CASES if case.condition == "exact_echo")
        response = MockResearchAgent().answer(case, method="standard")
        score = score_response(case, response)
        self.assertEqual(score["false_corroboration"], 1.0)
        self.assertEqual(score["verdict_accuracy"], 1.0)

    def test_aggregate_handles_empty_input(self):
        self.assertEqual(
            aggregate_scores(CASES, []),
            {"n": 0, "attempted": 0, "coverage": 0.0, "metrics": {"error": 0.0}},
        )


if __name__ == "__main__":
    unittest.main()
