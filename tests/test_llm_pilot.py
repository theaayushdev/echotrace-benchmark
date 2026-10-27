import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from echotrace.llm_pilot import build_prompt, load_credentials, redact, validate_answer


class PilotTests(unittest.TestCase):
    def answer(self):
        return {"answer": "The evidence supports it.", "verdict": "supported",
                "probabilities": {"supported": 0.8, "contradicted": 0.1, "insufficient": 0.1},
                "citations": ["d1"]}

    def test_rejects_hallucinated_citation(self):
        with self.assertRaises(ValueError):
            validate_answer(json.dumps(self.answer()), ["d2"])

    def test_rejects_nan_bool_and_unnormalized_probabilities(self):
        for value in (float("nan"), True, 0.7):
            answer = self.answer()
            answer["probabilities"]["supported"] = value
            with self.assertRaises(ValueError):
                validate_answer(json.dumps(answer), ["d1"])

    def test_rejects_conflicting_verdict(self):
        answer = self.answer()
        answer["verdict"] = "contradicted"
        with self.assertRaises(ValueError):
            validate_answer(json.dumps(answer), ["d1"])

    def test_valid_response_and_fenced_json(self):
        self.assertEqual(validate_answer("```json\n" + json.dumps(self.answer()) + "\n```", ["d1"]), self.answer())

    def test_standard_not_primed_and_evidence_identical(self):
        doc = SimpleNamespace(doc_id="d1", title="A", url="https://a.example", published_at="2020",
                              outbound_links=[], text="A measurement found improvement.")
        prompts = [build_prompt("Query", "Claim", [doc], arm, [["d1"]])
                   for arm in ("standard", "instruction", "echograph")]
        self.assertNotIn("source families", prompts[0])
        self.assertNotIn("independen", prompts[0])
        self.assertNotIn("predicted_evidence_groups", prompts[0])
        self.assertEqual(len({p.split("Documents:\n")[1] for p in prompts}), 1)

    def test_credentials_are_data_not_shell(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            path.write_text("KEY='$(do-not-execute)'\nEMPTY=''\n")
            values = load_credentials(path)
            self.assertEqual(values["KEY"], "$(do-not-execute)")
            self.assertEqual(redact("$(do-not-execute)", values), "[REDACTED]")


if __name__ == "__main__":
    unittest.main()
