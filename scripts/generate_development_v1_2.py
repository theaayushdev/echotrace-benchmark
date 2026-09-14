#!/usr/bin/env python3
"""Create a small chronology-corrected development sample, not a new held-out benchmark."""
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from echotrace.chronology import repair_development_dates, reversed_edges
from echotrace.io import sha256_file
from scripts.generate_benchmark_v1 import CONDITIONS, make_case


def main():
    target = ROOT / "data/development-v1.2"
    if target.exists():
        raise FileExistsError("Development sample already exists; do not overwrite reviews")
    rng = random.Random(20260913)
    public, gold = [], []
    changed = 0
    for index, verdict in enumerate(("supported", "contradicted", "insufficient")):
        for condition in CONDITIONS:
            visible, hidden = make_case(rng, 10000 + index, condition, verdict, "train")
            repaired = repair_development_dates(visible, hidden)
            changed += sum(a["published_at"] != b["published_at"]
                           for a, b in zip(visible["documents"], repaired["documents"]))
            assert not reversed_edges(repaired, hidden)
            public.append(repaired)
            gold.append({"case_id": repaired["case_id"], **hidden})
    target.mkdir()
    for filename, rows in (("public.jsonl", public), ("gold.jsonl", gold)):
        (target / filename).write_text("".join(json.dumps(r) + "\n" for r in rows))
    manifest = {"version": "1.2-development-only", "seed": 20260913, "worlds": 3, "cases": 33,
                "split": "train only", "changed_dates": changed, "remaining_reversed_edges": 0,
                "limitations": "Same prose templates; no human validation; not a confirmatory evaluation set",
                "sha256": {str(p.relative_to(ROOT)): sha256_file(p) for p in
                           (Path(__file__), ROOT / "scripts/generate_benchmark_v1.py",
                            ROOT / "echotrace/chronology.py", target / "public.jsonl", target / "gold.jsonl")}}
    (target / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({k: v for k, v in manifest.items() if k != "sha256"}))


if __name__ == "__main__":
    main()
