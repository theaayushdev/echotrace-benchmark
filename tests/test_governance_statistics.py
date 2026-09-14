import tempfile
import unittest
from pathlib import Path

from echotrace.agents.mock import MockResearchAgent
from echotrace.io import load_cases
from echotrace.live_audit import validate_live_audit
from echotrace.review import review_report
from echotrace.runner import run_experiment
from echotrace.schemas import AgentResponse, ClaimResponse, validate_response
from echotrace.statistics import holm_adjust, paired_comparison

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "echobench.jsonl"
CASES = load_cases(DATA)


class GovernanceTests(unittest.TestCase):
    def test_empty_review_ledger_keeps_cases_generated(self):
        report = review_report(DATA, ROOT / "annotations" / "reviews.csv")
        self.assertTrue(report["valid"])
        self.assertEqual(report["status_counts"], {"generated": 400})

    def test_empty_live_audit_is_valid_work_in_progress_but_not_release(self):
        path = ROOT / "data" / "live_audit.csv"
        self.assertTrue(validate_live_audit(path)["valid"])
        self.assertFalse(validate_live_audit(path, require_complete=True)["valid"])

    def test_response_rejects_unknown_document(self):
        case = CASES[0]
        response = AgentResponse(
            case.case_id,
            "answer",
            (ClaimResponse("claim", "supported", 0.5, ("invented",)),),
            0.5,
            ("invented",),
            (("invented",),),
        )
        with self.assertRaises(ValueError):
            validate_response(case, response)

    def test_run_manifest_prevents_incompatible_resume(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "run.jsonl"
            run_experiment(CASES[:1], MockResearchAgent(), output, "standard", "naturalistic", 1.0)
            self.assertTrue(Path(str(output) + ".manifest.json").exists())
            with self.assertRaises(RuntimeError):
                run_experiment(CASES[:1], MockResearchAgent(), output, "standard", "diagnostic", 1.0)


class StatisticsTests(unittest.TestCase):
    def test_identical_runs_have_zero_paired_difference(self):
        subset = [case for case in CASES if case.split == "test"]
        responses = [MockResearchAgent().answer(case) for case in subset]
        result = paired_comparison(subset, responses, responses, "root_count_mae", samples=200)
        self.assertEqual(result["candidate_minus_baseline"], 0.0)
        self.assertEqual(result["ci_low"], 0.0)
        self.assertEqual(result["p_value"], 1.0)

    def test_holm_adjustment_is_monotone_and_bounded(self):
        adjusted = holm_adjust({"a": 0.01, "b": 0.03, "c": 0.5})
        self.assertEqual(adjusted["a"], 0.03)
        self.assertLessEqual(adjusted["b"], adjusted["c"])
        self.assertTrue(all(0.0 <= item <= 1.0 for item in adjusted.values()))


if __name__ == "__main__":
    unittest.main()
