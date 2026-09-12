import unittest
from pathlib import Path

from echotrace.io import load_cases
from echotrace.metrics import family_pair_f1
from echotrace.runner import trained_echo_graph

ROOT = Path(__file__).resolve().parents[1]
CASES = load_cases(ROOT / "data" / "echobench.jsonl")


class EchoGraphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = trained_echo_graph(CASES)

    def case(self, condition: str):
        return next(case for case in CASES if case.split == "test" and case.condition == condition)

    def test_exact_echo_forms_one_support_family(self):
        case = self.case("exact_echo")
        supporters = set(case.gold_claims[0].supporting_doc_ids)
        docs = [doc for doc in case.documents if doc.doc_id in supporters]
        inferred = self.graph.infer(docs)
        self.assertEqual(len(inferred.evidence_families), 1)

    def test_independent_sources_stay_separate(self):
        case = self.case("four_roots")
        supporters = set(case.gold_claims[0].supporting_doc_ids)
        docs = [doc for doc in case.documents if doc.doc_id in supporters]
        inferred = self.graph.infer(docs)
        self.assertEqual(len(inferred.evidence_families), 4)

    def test_family_metric(self):
        gold = (("a", "b", "c"), ("d",))
        self.assertEqual(family_pair_f1(gold, gold), 1.0)
        self.assertEqual(family_pair_f1(gold, (("a",), ("b",), ("c",), ("d",))), 0.0)


if __name__ == "__main__":
    unittest.main()
