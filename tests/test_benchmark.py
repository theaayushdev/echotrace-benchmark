import unittest
from pathlib import Path

from echotrace.benchmark import validate_dataset
from echotrace.io import load_cases

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "echobench.jsonl"


class BenchmarkTests(unittest.TestCase):
    def test_checked_in_dataset_is_structurally_valid(self):
        report = validate_dataset(DATA)
        self.assertTrue(report["valid"], report["errors"])
        self.assertEqual(report["case_count"], 400)
        self.assertEqual(report["world_count"], 80)

    def test_micro_worlds_do_not_cross_splits(self):
        splits = {}
        for case in load_cases(DATA):
            splits.setdefault(case.micro_world_id, set()).add(case.split)
        self.assertTrue(all(len(value) == 1 for value in splits.values()))

    def test_gold_labels_are_not_in_public_projection(self):
        case = load_cases(DATA)[0]
        public = case.to_dict(include_gold=False)
        self.assertNotIn("gold_root_count", public)
        self.assertNotIn("gold_lineage_edges", public)
        self.assertNotIn("condition", public)
        self.assertNotIn("micro_world_id", public)
        self.assertNotIn("split", public)


if __name__ == "__main__":
    unittest.main()
