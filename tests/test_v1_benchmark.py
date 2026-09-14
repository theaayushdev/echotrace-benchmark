import json
import unittest
from collections import Counter
from pathlib import Path

from echotrace.benchmark_v1 import validate_v1_dataset
from echotrace.io import load_v1_cases
from echotrace.review_v1 import author_audit_report

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "data" / "echobench_synthetic_v1_public.jsonl"
GOLD = ROOT / "data" / "echobench_synthetic_v1_gold.jsonl"
MANIFEST = ROOT / "data" / "echobench_synthetic_v1_manifest.json"
SAMPLE = ROOT / "annotations" / "v1" / "author_audit_sample.json"
LEDGER = ROOT / "annotations" / "v1" / "author_audit.csv"


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

    def test_author_audit_has_two_cases_per_condition_verdict_cell(self):
        sample = set(json.loads(SAMPLE.read_text())["case_ids"])
        gold = [json.loads(line) for line in GOLD.read_text().splitlines()]
        cells = Counter(
            (row["condition"], row["gold_claim"]["verdict"])
            for row in gold
            if row["case_id"] in sample
        )
        self.assertEqual(len(sample), 66)
        self.assertEqual(len(cells), 33)
        self.assertTrue(all(count == 2 for count in cells.values()))

    def test_empty_pair_ledger_is_not_a_completed_review(self):
        report = author_audit_report(GOLD, SAMPLE, LEDGER)
        self.assertFalse(report["valid"])
        self.assertFalse(report["release_ready"])
        self.assertEqual(report["rows"], 0)


if __name__ == "__main__":
    unittest.main()
