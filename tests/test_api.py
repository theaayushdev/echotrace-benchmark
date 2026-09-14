import unittest
from pathlib import Path

from echotrace.agents.api import _extract_json
from echotrace.agents.api import ModelConfig, OpenAICompatibleAgent
from echotrace.io import load_cases

ROOT = Path(__file__).resolve().parents[1]


class ApiParsingTests(unittest.TestCase):
    def test_extract_plain_json(self):
        self.assertEqual(_extract_json('{"answer":"ok"}')["answer"], "ok")

    def test_extract_fenced_json(self):
        value = _extract_json('```json\n{"answer":"ok"}\n```')
        self.assertEqual(value["answer"], "ok")

    def test_missing_json_fails(self):
        with self.assertRaises(ValueError):
            _extract_json("not structured")

    def test_naturalistic_prompt_does_not_prime_source_independence(self):
        case = load_cases(ROOT / "data" / "echobench.jsonl")[0]
        agent = OpenAICompatibleAgent(ModelConfig("test", "https://example.invalid", "UNUSED"))
        prompt = agent._prompt(case, "standard", None, "naturalistic").lower()
        self.assertNotIn("do not count a derivative", prompt)
        self.assertNotIn("audit which cited documents", prompt)


if __name__ == "__main__":
    unittest.main()
