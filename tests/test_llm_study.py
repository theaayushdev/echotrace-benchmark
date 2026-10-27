import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from echotrace.llm_study import (ARMS, _metrics, _sensitivity, acquire_lock, build_prompt,
                                 completed_ids, validate_answer)


class StudyTests(unittest.TestCase):
    def answer(self, count=1):
        return {"answer": "The evidence supports it.", "verdict": "supported",
                "probabilities": {"supported": 0.8, "contradicted": 0.1, "insufficient": 0.1},
                "citations": ["d1"], "independent_sources": count}

    def test_accepts_count_and_null(self):
        for count in (0, 1, None):
            self.assertEqual(validate_answer(json.dumps(self.answer(count)), ["d1"])["independent_sources"], count)

    def test_rejects_missing_bool_or_excess_count(self):
        bad = [self.answer(True), self.answer(2), self.answer("1"), self.answer(-1)]
        missing = self.answer()
        del missing["independent_sources"]
        for answer in bad + [missing]:
            with self.assertRaises(ValueError):
                validate_answer(json.dumps(answer), ["d1"])

    def test_strips_reasoning_block(self):
        content = "<think>count them</think>" + json.dumps(self.answer())
        self.assertEqual(validate_answer(content, ["d1"])["independent_sources"], 1)

    def test_arms_share_evidence_and_oracle_matches_echograph_wording(self):
        doc = SimpleNamespace(doc_id="d1", title="A", url="https://a.example", published_at="2020",
                              outbound_links=[], text="A measurement found improvement.")
        prompts = {arm: build_prompt("Query", "Claim", [doc], arm, [["d1"]]) for arm in ARMS}
        evidence = "Documents:\n[d1]"
        self.assertTrue(all(evidence in p for p in prompts.values()))
        self.assertNotIn("source families", prompts["standard"])
        self.assertNotIn("source families", prompts["reminder"])
        self.assertEqual(prompts["echograph"], prompts["oracle"])

    def test_oracle_without_families_states_undetermined(self):
        doc = SimpleNamespace(doc_id="d1", title="A", url="u", published_at="2020",
                              outbound_links=[], text="t")
        self.assertIn("could not be determined", build_prompt("Q", "C", [doc], "oracle", []))

    def test_metrics_count_overcount_and_null(self):
        rows = [
            {"condition": "single_origin", "gold_root_count": 1, "count": 4, "correct": 1, "brier": 0.1,
             "gold_verdict": "supported", "p_gold": 1.0},
            {"condition": "single_origin", "gold_root_count": 1, "count": None, "correct": 1, "brier": 0.1,
             "gold_verdict": "supported", "p_gold": 0.8},
            {"condition": "four_independent", "gold_root_count": 4, "count": 2, "correct": 0, "brier": 0.5,
             "gold_verdict": "contradicted", "p_gold": 0.995},
            {"condition": "ambiguous_provenance", "gold_root_count": 0, "count": None, "correct": 1, "brier": 0.0,
             "gold_verdict": "insufficient", "p_gold": 1.0},
        ]
        m = _metrics(rows)
        self.assertEqual(m["false_corroboration_rate"], 0.5)
        self.assertEqual(m["undercount_rate_independent"], 1.0)
        self.assertEqual(m["ambiguous_abstention_rate"], 1.0)
        self.assertEqual(m["count_abs_error"], 2.5)
        self.assertAlmostEqual(m["confidence_ceiling_rate"], 2 / 3)
        self.assertAlmostEqual(m["determinate_abstention_rate"], 1 / 3)

    def test_sensitivity_is_within_world(self):
        rows = [
            {"world": "w1", "condition": "four_independent", "gold_verdict": "supported", "p_gold": 0.9},
            {"world": "w1", "condition": "single_origin", "gold_verdict": "supported", "p_gold": 0.6},
            {"world": "w2", "condition": "four_independent", "gold_verdict": "insufficient", "p_gold": 0.9},
            {"world": "w2", "condition": "single_origin", "gold_verdict": "insufficient", "p_gold": 0.1},
        ]
        self.assertAlmostEqual(_sensitivity(rows), 0.3)


    def test_only_observed_outcomes_block_resend(self):
        latest = {"a": {"status": "valid"}, "b": {"status": "invalid"},
                  "c": {"status": "started"}, "d": {"status": "rejected_retryable"},
                  "e": {"status": "transport_or_provider_error"}}
        self.assertEqual(completed_ids(latest), {"a", "b", "e"})

    def test_stale_lock_is_cleared_but_live_lock_is_kept(self):
        with tempfile.TemporaryDirectory() as tmp:
            lock = Path(tmp) / "m.lock"
            lock.write_text("999999999")
            acquire_lock(lock)
            self.assertEqual(lock.read_text(), str(os.getpid()))
            with self.assertRaises(FileExistsError):
                acquire_lock(lock)


if __name__ == "__main__":
    unittest.main()
