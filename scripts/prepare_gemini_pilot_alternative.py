#!/usr/bin/env python3
"""Archive an explicit Gemini availability amendment without changing the original plan."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from echotrace.llm_pilot import digest, now, read_plan
from echotrace.io import sha256_file


def main():
    original = ROOT / "artifacts/llm-pilot-v1.2"
    target = ROOT / "artifacts/llm-pilot-v1.2-gemini37"
    plan = read_plan(ROOT, original)
    previous = plan.pop("plan_sha256")
    plan["original_plan_sha256"] = previous
    plan["created_at"] = now()
    plan["models"] = {"gemini": {**plan["models"]["gemini"], "model": "gemini-3.7-flash"}}
    plan["amendment"] = "Availability-only replacement after two HTTP 503 responses; no Gemini answers observed"
    for path in ("experiments/llm_pilot_gemini_amendment.md", "scripts/prepare_gemini_pilot_alternative.py"):
        plan["sha256"][path] = sha256_file(ROOT / path)
    plan["plan_sha256"] = digest(plan)
    target.mkdir()
    (target / "plan.json").write_text(json.dumps(plan, indent=2) + "\n")
    print("Prepared Gemini 3.7 Flash alternative; original errors retained")


if __name__ == "__main__":
    main()
