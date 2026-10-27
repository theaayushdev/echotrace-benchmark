import json
import unittest
from collections import Counter
from pathlib import Path

from echotrace.benchmark_v1 import validate_v1_dataset
from echotrace.io import load_v1_cases

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "data" / "echobench_synthetic_v1_public.jsonl"
GOLD = ROOT / "data" / "echobench_synthetic_v1_gold.jsonl"
MANIFEST = ROOT / "data" / "echobench_synthetic_v1_manifest.json"


class V1BenchmarkTests(unittest.TestCase):
    def test_v1_release_is_balanced_and_loadable(self):
        report = validate_v1_dataset(PUBLIC, GOLD, MANIFEST)
        self.assertTrue(report["valid"], report["errors"])
        cases = load_v1_cases(PUBLIC, GOLD, MANIFEST)
        counts = Counter((case.split, case.gold_claims[0].verdict) for case in cases)
        self.assertEqual(counts["test", "supported"], 220)
        self.assertEqual(counts["test", "contradicted"], 220)
        self.assertEqual(counts["test", "insufficient"], 220)

    def test_v1_public_rows_do_not_contain_gold_fields(self):
        row = json.loads(PUBLIC.read_text().splitlines()[0])
        self.assertEqual(set(row), {"case_id", "query", "documents"})


if __name__ == "__main__":
    unittest.main()
