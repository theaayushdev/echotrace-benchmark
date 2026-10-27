import unittest
from copy import deepcopy

from echotrace.chronology import repair_development_dates, reversed_edges


class ChronologyTests(unittest.TestCase):
    def test_chain_repair_preserves_input_and_text(self):
        public = {"documents": [
            {"doc_id": "a", "published_at": "2022-01-01T00:00:00+00:00", "text": "root"},
            {"doc_id": "b", "published_at": "2020-01-01T00:00:00+00:00", "text": "summary"},
            {"doc_id": "c", "published_at": "2021-01-01T00:00:00+00:00", "text": "digest"}]}
        gold = {"gold_lineage_edges": [{"source_id": "b", "derivative_id": "c"},
                                       {"source_id": "a", "derivative_id": "b"}]}
        original = deepcopy(public)
        self.assertEqual(len(reversed_edges(public, gold)), 1)
        repaired = repair_development_dates(public, gold)
        self.assertEqual(reversed_edges(repaired, gold), [])
        self.assertEqual(public, original)
        self.assertEqual([d["text"] for d in repaired["documents"]], ["root", "summary", "digest"])

    def test_cycle_rejected(self):
        public = {"documents": [{"doc_id": "a", "published_at": "2020-01-01"}]}
        with self.assertRaises(ValueError):
            repair_development_dates(public, {"gold_lineage_edges": [{"source_id": "a", "derivative_id": "a"}]})


if __name__ == "__main__":
    unittest.main()
