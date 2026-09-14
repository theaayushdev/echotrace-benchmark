import unittest

from echotrace.chronology import repair_dates, reversed_edges
from scripts.generate_benchmark_v1_2 import WORLD_COUNT, assignments


class V12BenchmarkTests(unittest.TestCase):
    def test_assignments_are_world_disjoint_and_balanced(self):
        assigned = assignments(20260914)
        self.assertEqual(len(assigned), WORLD_COUNT)
        for split, expected in (("train", 216), ("validation", 72), ("test", 72)):
            self.assertEqual(sum(value[0] == split for value in assigned.values()), expected)

    def test_repair_removes_reversed_edges(self):
        public = {"documents": [
            {"doc_id": "a", "published_at": "2022-01-01T00:00:00+00:00", "text": "a"},
            {"doc_id": "b", "published_at": "2020-01-01T00:00:00+00:00", "text": "b"},
        ]}
        gold = {"gold_lineage_edges": [{"source_id": "a", "derivative_id": "b"}]}
        self.assertTrue(reversed_edges(public, gold))
        self.assertFalse(reversed_edges(repair_dates(public, gold), gold))


if __name__ == "__main__":
    unittest.main()
