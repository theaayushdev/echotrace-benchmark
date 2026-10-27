#!/usr/bin/env python3
"""Generate EchoBench-Synthetic v1.4: v1.3 structure with diversified prose.

Adds 36 topics (3x v1.1), six prose styles per provenance role, varied
distractors, and held-out prose styles used only by half of the test worlds.
Gold structure and observability rules are inherited from v1.3. The release is
synthetic, gold-by-construction, and pending blinded human review.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.generate_benchmark_v1 as base
from echotrace.chronology import repair_dates, reversed_edges
from scripts.generate_benchmark_v1 import CONDITIONS, finding, make_case
from scripts.generate_benchmark_v1_2 import WORLD_COUNT, assignments
from scripts.generate_benchmark_v1_3 import redesign_case

VERSION = "1.4-candidate"
EXTRA_TOPICS = [
    ("bridge inspection", "a drone survey", 21, "improved defect recall"),
    ("hospital scheduling", "a queue model", 10, "reduced waiting time"),
    ("irrigation planning", "a soil-moisture controller", 24, "reduced water use"),
    ("wildfire detection", "a camera network", 17, "improved early detection"),
    ("public transit reliability", "a dispatch rule", 8, "reduced late arrivals"),
    ("seed germination", "a coating treatment", 14, "improved germination"),
    ("grid load forecasting", "a hybrid forecaster", 12, "reduced forecast error"),
    ("landslide warning", "a rainfall threshold", 19, "improved lead time"),
    ("literacy tutoring", "a peer-reading program", 11, "improved reading scores"),
    ("cold-chain monitoring", "a sensor tag", 16, "reduced spoilage"),
    ("noise mapping", "a crowdsourced app", 9, "reduced mapping error"),
    ("pothole repair", "a prioritization model", 13, "reduced repair backlog"),
    ("river turbidity sensing", "an optical probe", 15, "improved detection"),
    ("pharmacy stock planning", "a reorder policy", 18, "reduced stockouts"),
    ("rooftop solar siting", "a shading model", 20, "improved yield"),
    ("earthquake damage triage", "a rapid survey form", 14, "improved triage accuracy"),
    ("bus-stop shelter use", "a redesign", 7, "increased ridership"),
    ("wetland monitoring", "a satellite index", 22, "improved mapping accuracy"),
    ("e-waste collection", "a drop-off scheme", 23, "increased collection"),
    ("dental screening", "a school program", 12, "improved early detection"),
    ("fishery quota setting", "a stock model", 10, "reduced overshoot"),
    ("rural telemedicine", "a nurse-led protocol", 17, "reduced referral delay"),
    ("airport baggage handling", "a sorting policy", 9, "reduced mishandling"),
    ("soil carbon sampling", "a stratified design", 15, "reduced sampling variance"),
]

# Roles: origin (first-hand observation), derivative (cites an upstream URL),
# dataset (names a dataset that may be reused), unknown (no provenance cue).
SEEN_STYLES = {
    "news": {
        "origin": ["Researchers {team} report from sample {sample} that {result}.",
                   "A newly released evaluation (sample {sample}) finds that {result}."],
        "derivative": ["Coverage drawing on {url} notes that {result}.",
                       "As first reported at {url}, {result}."],
        "dataset": ["Using dataset {sample}, the analysts conclude that {result}.",
                    "Working from the shared records in {sample}, the team finds that {result}."],
        "unknown": ["Observers say that {result}.", "It has been stated that {result}."],
    },
    "academic": {
        "origin": ["We measured outcomes on sample {sample} and observed that {result}.",
                   "On sample {sample}, our analysis shows that {result}."],
        "derivative": ["Following the study at {url}, we restate that {result}.",
                       "Citing {url}, this review summarizes that {result}."],
        "dataset": ["Re-analysing dataset {sample}, we find that {result}.",
                    "Our estimate on dataset {sample} indicates that {result}."],
        "unknown": ["The literature suggests that {result}.", "Findings are described as follows: {result}."],
    },
    "bulletin": {
        "origin": ["BULLETIN: field team {team}, sample {sample}. Result: {result}.",
                   "Field note from team {team} (sample {sample}): {result}."],
        "derivative": ["BULLETIN (from {url}): {result}.", "Relayed from {url}: {result}."],
        "dataset": ["BULLETIN: dataset {sample} analysed; {result}.",
                    "Dataset {sample} was re-examined and it appears that {result}."],
        "unknown": ["BULLETIN: reportedly, {result}.", "Word is that {result}."],
    },
    "blog": {
        "origin": ["We ran our own trial on sample {sample}, and honestly: {result}.",
                   "Our group (team {team}) looked at sample {sample} and saw that {result}."],
        "derivative": ["Saw this at {url} and wanted to pass it along: {result}.",
                       "Short recap of {url}: {result}."],
        "dataset": ["I dug into dataset {sample} myself and {result}.",
                    "Back to dataset {sample} again; it turns out that {result}."],
        "unknown": ["People keep saying that {result}.", "Apparently {result}."],
    },
}
UNSEEN_STYLES = {
    "memo": {
        "origin": ["MEMO. Re: sample {sample} (team {team}). Outcome: {result}.",
                   "Internal memo, team {team}: on sample {sample}, {result}."],
        "derivative": ["MEMO. Forwarding the account at {url}; in brief, {result}.",
                       "Memo summary of {url}: {result}."],
        "dataset": ["MEMO. Dataset {sample} reviewed; conclusion: {result}.",
                    "Memo on dataset {sample}: the evidence is that {result}."],
        "unknown": ["MEMO. Unsourced note: {result}.", "Memo: it is said that {result}."],
    },
    "forum": {
        "origin": ["Posting from team {team}: sample {sample} came back and {result}.",
                   "Thread update, sample {sample}: {result}."],
        "derivative": ["Linking {url} here since it covers this: {result}.",
                       "Copying the gist from {url}: {result}."],
        "dataset": ["Reran everything on dataset {sample} and {result}.",
                    "Dataset {sample} again, same story: {result}."],
        "unknown": ["Someone mentioned that {result}.", "No source, but {result}."],
    },
}
NEUTRALS = [
    "A methods note discusses {topic} and {system} but gives no result for the focal comparison.",
    "This overview of {topic} describes background context for {system} without reporting outcomes.",
    "A glossary entry defines terms used in {topic} research and mentions {system} only in passing.",
    "A budget summary for a {topic} programme lists equipment for {system} and reports no findings.",
    "A workshop agenda on {topic} schedules a session about {system}; no results are given.",
    "An equipment catalogue for {topic} describes {system} specifications and says nothing about outcomes.",
    "A policy brief on {topic} refers to {system} as an area for future study.",
    "A training manual for {topic} explains how to operate {system} and omits any evaluation.",
]
TAILS = [
    " The report describes the setting, method, and observations available to its authors.",
    " Background and limitations are discussed elsewhere in the document.",
    " Further details appear in the accompanying notes.",
    "",
]
SAMPLE_TOKEN = re.compile(r"(?:DS|ST)-\d{3}-[A-C]")


def role_of(condition: str, doc: dict, text: str) -> str:
    if condition in {"ambiguous_provenance", "unattributed_multihop"}:
        return "unknown"
    if condition == "shared_dataset":
        return "dataset"
    return "derivative" if doc["outbound_links"] else "origin"


def rewrite_prose(visible: dict, hidden: dict, rng: random.Random, world: int, held_out: bool) -> str:
    """Replace relevant-document and distractor text; return the style name."""
    topic, system, value, outcome = base.TOPICS[world % len(base.TOPICS)]
    result = finding(hidden["gold_claim"]["verdict"], system, topic, value, outcome)
    bank = UNSEEN_STYLES if held_out else SEEN_STYLES
    style = rng.choice(sorted(bank))
    relevant = hidden["gold_claim"]["relevant_doc_ids"]
    documents = {doc["doc_id"]: doc for doc in visible["documents"]}
    for index, doc_id in enumerate(relevant):
        doc = documents[doc_id]
        match = SAMPLE_TOKEN.search(doc["text"])
        role = role_of(hidden["condition"], doc, doc["text"])
        sample = match.group(0) if match else f"{world:03d}-{index + 1}"
        url = doc["outbound_links"][0] if doc["outbound_links"] else ""
        template = rng.choice(bank[style][role])
        doc["text"] = template.format(result=result, sample=sample, team="ABCD"[index], url=url)
        doc["text"] += rng.choice(TAILS)
    for doc in visible["documents"]:
        if doc["doc_id"] not in relevant:
            doc["text"] = rng.choice(NEUTRALS).format(topic=topic, system=system) + rng.choice(TAILS)
    return style


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=20260916)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "data" / "echobench_synthetic_v1_4")
    args = parser.parse_args()
    if args.out_dir.exists() and any(args.out_dir.iterdir()):
        raise SystemExit(f"refusing to overwrite non-empty output directory: {args.out_dir}")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    base.TOPICS = base.TOPICS + EXTRA_TOPICS
    rng, split_assignments = random.Random(args.seed), assignments(args.seed)
    public, gold, manifest = [], [], []
    for world in range(WORLD_COUNT):
        split, verdict = split_assignments[world]
        held_out = split == "test" and world % 2 == 0
        for condition in CONDITIONS:
            visible, hidden = make_case(rng, world, condition, verdict, split)
            redesign_case(visible, hidden, rng, world)
            style = rewrite_prose(visible, hidden, rng, world, held_out)
            repaired = repair_dates(visible, hidden)
            if reversed_edges(repaired, hidden):
                raise AssertionError("chronology repair left a reversed lineage edge")
            hidden["prose_style"] = style
            hidden["style_heldout"] = held_out
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
        "topics": len(base.TOPICS),
        "styles": {"seen": sorted(SEEN_STYLES), "heldout": sorted(UNSEEN_STYLES)},
        "chronology": {"reversed_edges": 0},
        "status": "candidate; synthetic and gold-by-construction; pending blinded human review",
    }, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"version": VERSION, "cases": len(public), "topics": len(base.TOPICS),
                      "output": str(args.out_dir)}))


if __name__ == "__main__":
    main()
