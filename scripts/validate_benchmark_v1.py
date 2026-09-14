#!/usr/bin/env python3
"""Structural and shortcut-leakage checks for EchoBench-Synthetic v1."""
from __future__ import annotations
import argparse, json, re
from collections import Counter
from pathlib import Path

FORBIDDEN = re.compile(r"supporter|contradict|distractor|unattributed|verbatim|paraphrase|world_\d|condition", re.I)

def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--data", type=Path, default=Path(__file__).parents[1] / "data"); args = ap.parse_args()
    pub = [json.loads(x) for x in (args.data / "echobench_synthetic_v1_public.jsonl").read_text().splitlines()]
    gold = [json.loads(x) for x in (args.data / "echobench_synthetic_v1_gold.jsonl").read_text().splitlines()]
    manifest_document = json.loads((args.data / "echobench_synthetic_v1_manifest.json").read_text())
    assert manifest_document["version"] == "1.1"
    manifest = manifest_document["cases"]
    assert len(pub) == len(gold) == len(manifest) == 2640
    assert len({x["case_id"] for x in pub}) == len(pub)
    assert all(set(x) == {"case_id", "query", "documents"} for x in pub)
    assert all(len(x["documents"]) == 12 for x in pub)
    ids = [d["doc_id"] for x in pub for d in x["documents"]]
    assert len(ids) == len(set(ids)) and all(re.fullmatch(r"doc_[0-9a-f]{16}", i) for i in ids)
    assert all(not FORBIDDEN.search(json.dumps(x)) for x in pub)
    assert Counter(x["condition"] for x in manifest) == Counter({c: 240 for c in {x["condition"] for x in manifest}})
    assert Counter(x["split"] for x in manifest) == Counter({"train": 1650, "validation": 330, "test": 660})
    verdicts = Counter(x["gold_claim"]["verdict"] for x in gold)
    assert verdicts == Counter({"supported": 880, "contradicted": 880, "insufficient": 880})
    gold_by_id = {x["case_id"]: x for x in gold}
    split_verdicts = Counter((x["split"], gold_by_id[x["case_id"]]["gold_claim"]["verdict"]) for x in manifest)
    assert split_verdicts == Counter({
        ("train", "supported"): 550, ("train", "contradicted"): 550, ("train", "insufficient"): 550,
        ("validation", "supported"): 110, ("validation", "contradicted"): 110, ("validation", "insufficient"): 110,
        ("test", "supported"): 220, ("test", "contradicted"): 220, ("test", "insufficient"): 220,
    })
    for public_row in pub:
        gold_row = gold_by_id[public_row["case_id"]]
        documents = {doc["doc_id"]: doc for doc in public_row["documents"]}
        relevant = set(gold_row["gold_claim"]["relevant_doc_ids"])
        assert len(relevant) == 4 and relevant <= set(documents)
        assert len(gold_row["gold_relationships"]) == 6
        text = " ".join(documents[doc_id]["text"].lower() for doc_id in relevant)
        verdict = gold_row["gold_claim"]["verdict"]
        if verdict == "supported":
            assert gold_row["gold_claim"]["supporting_doc_ids"] and "no improvement" not in text
        elif verdict == "contradicted":
            assert gold_row["gold_claim"]["contradicting_doc_ids"] and "no improvement" in text
        else:
            assert not gold_row["gold_claim"]["supporting_doc_ids"] and not gold_row["gold_claim"]["contradicting_doc_ids"]
        if gold_row["condition"] == "ambiguous_provenance":
            assert gold_row["gold_root_count"] == 0 and not gold_row["gold_families"]
            assert all(item["action"] == "abstain" for item in gold_row["gold_relationships"])
        else:
            assert {item for family in gold_row["gold_families"] for item in family} == relevant
    print(json.dumps({"status": "ok", "cases": len(pub), "worlds": len({x["world"] for x in manifest}), "documents": len(ids), "verdicts": verdicts, "split_verdicts": {f"{split}:{verdict}": count for (split, verdict), count in split_verdicts.items()}}))

if __name__ == "__main__": main()
