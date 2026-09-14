#!/usr/bin/env python3
"""Generate EchoBench-Synthetic v1.3 with auditable provenance observability.

This candidate repairs the two failures found in the AI diagnostic audit of
v1.2. It remains synthetic and must receive blinded human review before any
confirmatory freeze or test access.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from echotrace.chronology import repair_dates, reversed_edges
from scripts.generate_benchmark_v1 import CONDITIONS, make_case
from scripts.generate_benchmark_v1_2 import WORLD_COUNT, assignments

VERSION = "1.3-candidate"
TAIL = " The report describes the setting, method, and observations available to its authors."
REPUBLICATION_FORMS = (
    "An editorial note identifies this as a republication of the field report at {url}; it states that {result}.",
    "This archived copy attributes its text to the earlier field report at {url}: {result}.",
    "The outlet says it reproduced the findings from the report at {url}: {result}.",
)
INDEPENDENT_FORMS = (
    "Team {team} collected a distinct sample {sample}; its evaluation found that {result}.",
    "A separately collected dataset, {sample}, was evaluated by Team {team}; it found that {result}.",
    "Team {team} reports a new observation from sample {sample}: {result}.",
)


def _unknown_relationships(ids: list[str]) -> list[dict[str, str]]:
    return [
        {"left_doc_id": left, "right_doc_id": right, "relationship": "unknown",
         "dependency_basis": "unknown", "observability": "indeterminate", "action": "abstain"}
        for left, right in combinations(ids, 2)
    ]


def redesign_case(visible: dict, hidden: dict, rng: random.Random, world: int) -> None:
    """Make public provenance cues defensible without exposing hidden labels."""
    documents = {doc["doc_id"]: doc for doc in visible["documents"]}
    relevant = hidden["gold_claim"]["relevant_doc_ids"]
    if hidden["condition"] == "verbatim_derivative":
        root_id = next(edge["source_id"] for edge in hidden["gold_lineage_edges"])
        root = documents[root_id]
        claim_text = root["text"].split("reports that ", 1)[1].split(".", 1)[0]
        for edge in hidden["gold_lineage_edges"]:
            derivative = documents[edge["derivative_id"]]
            derivative["text"] = rng.choice(REPUBLICATION_FORMS).format(
                url=root["url"], result=claim_text
            ) + TAIL
            derivative["outbound_links"] = [root["url"]]
            edge["transformation"] = "attributed_republication"
    elif hidden["condition"] == "unattributed_multihop":
        # The public text provides repeated claims but no defensible ancestry.
        # Gold therefore requires abstention instead of asserting a hidden chain.
        hidden["gold_root_count"] = 0
        hidden["gold_families"] = []
        hidden["gold_lineage_edges"] = []
        hidden["gold_relationships"] = _unknown_relationships(relevant)
    elif hidden["condition"] in {"four_independent", "same_wording_independent"}:
        for index, doc_id in enumerate(relevant):
            doc = documents[doc_id]
            original = doc["text"]
            if "; " in original:
                statement = original.split("; ", 1)[1].split(".", 1)[0]
            else:
                statement = original.split("reports that ", 1)[-1].split(".", 1)[0]
            doc["text"] = rng.choice(INDEPENDENT_FORMS).format(
                team="ABCD"[index], sample=f"{world:03d}-{index + 1}", result=statement
            ) + TAIL


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=20260915)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "data" / "echobench_synthetic_v1_3")
    args = parser.parse_args()
    if args.out_dir.exists() and any(args.out_dir.iterdir()):
        raise SystemExit(f"refusing to overwrite non-empty output directory: {args.out_dir}")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rng, split_assignments = random.Random(args.seed), assignments(args.seed)
    public, gold, manifest, changed_dates = [], [], [], 0
    for world in range(WORLD_COUNT):
        split, verdict = split_assignments[world]
        for condition in CONDITIONS:
            visible, hidden = make_case(rng, world, condition, verdict, split)
            redesign_case(visible, hidden, rng, world)
            repaired = repair_dates(visible, hidden)
            changed_dates += sum(a["published_at"] != b["published_at"]
                                 for a, b in zip(visible["documents"], repaired["documents"]))
            if reversed_edges(repaired, hidden):
                raise AssertionError("chronology repair left a reversed lineage edge")
            public.append(repaired)
            gold.append({"case_id": repaired["case_id"], **hidden})
            manifest.append({"case_id": repaired["case_id"], "world": world,
                             "condition": condition, "split": split})
    for filename, rows in (("public.jsonl", public), ("gold.jsonl", gold)):
        with (args.out_dir / filename).open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    (args.out_dir / "manifest.json").write_text(json.dumps({
        "version": VERSION, "seed": args.seed, "world_count": WORLD_COUNT, "cases": manifest,
        "chronology": {"reversed_edges": 0, "changed_dates": changed_dates},
        "design_changes": ["attributed verbatim republication", "unattributed reports require abstention",
                           "varied independent-observation wording"],
        "status": "candidate; synthetic and gold-by-construction; pending blinded human review",
    }, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"version": VERSION, "cases": len(public), "changed_dates": changed_dates,
                      "output": str(args.out_dir)}))


if __name__ == "__main__":
    main()
