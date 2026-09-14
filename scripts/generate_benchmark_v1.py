#!/usr/bin/env python3
"""Generate EchoBench-Synthetic v1.1 with separated public and gold views."""

from __future__ import annotations

import argparse
import json
import random
from itertools import combinations
from pathlib import Path

VERSION = "1.1"
TOPICS = [
    ("battery recycling", "a pilot process", 20, "improved recovery"),
    ("urban heat mapping", "a sensor network", 14, "reduced estimation error"),
    ("crop disease detection", "a field model", 18, "improved detection"),
    ("low-cost water testing", "a community assay", 11, "improved sensitivity"),
    ("traffic signal control", "an adaptive controller", 16, "reduced delay"),
    ("remote learning support", "a tutoring system", 13, "improved completion"),
    ("air-quality forecasting", "a forecasting model", 22, "improved accuracy"),
    ("coastal flood warning", "an alert protocol", 17, "reduced warning time"),
    ("forest restoration", "a planting intervention", 9, "improved survival"),
    ("medical image triage", "a screening tool", 15, "improved sensitivity"),
    ("warehouse routing", "a routing policy", 12, "reduced travel time"),
    ("solar microgrids", "a dispatch policy", 19, "reduced outage duration"),
]
CONDITIONS = [
    "single_origin",
    "four_independent",
    "verbatim_derivative",
    "attributed_paraphrase",
    "unattributed_multihop",
    "two_roots",
    "same_wording_independent",
    "same_domain_independent",
    "shared_dataset",
    "shared_study_replication",
    "ambiguous_provenance",
]


def opaque(rng: random.Random, prefix: str) -> str:
    return f"{prefix}_{rng.randbytes(8).hex()}"


def finding(verdict: str, system: str, topic: str, value: int, outcome: str) -> str:
    if verdict == "supported":
        return f"{system} for {topic} {outcome} by approximately {value} percent"
    if verdict == "contradicted":
        return f"{system} for {topic} produced no improvement; the measured change was approximately zero percent"
    return f"the evaluation of {system} for {topic} did not report a measurable comparison"


def make_case(rng: random.Random, world: int, condition: str, verdict: str, split: str):
    topic, system, value, outcome = TOPICS[world % len(TOPICS)]
    claim = f"{system.capitalize()} for {topic} {outcome} by approximately {value} percent."
    query = f"What does the evidence show about {system} for {topic}?"
    ids = [opaque(rng, "doc") for _ in range(12)]
    domains = [f"source-{rng.randrange(10_000, 99_999)}.example" for _ in ids]
    if condition == "same_domain_independent":
        domains[:4] = [domains[0]] * 4
    urls = [f"https://{domains[i]}/item/{rng.randbytes(6).hex()}" for i in range(12)]
    dates = [
        f"{2020 + (i // 2)}-{1 + rng.randrange(12):02d}-{1 + rng.randrange(27):02d}T00:00:00+00:00"
        for i in range(12)
    ]
    result = finding(verdict, system, topic, value, outcome)
    neutral = f"A methods note discusses {topic} and {system} but gives no result for the focal comparison."
    edges: list[dict[str, str]] = []
    links: list[list[str]] = [[] for _ in ids]
    bases: dict[tuple[str, str], str] = {}

    if condition == "single_origin":
        families = [ids[:4]]
        texts = [
            f"A primary field report states that {result}.",
            f"A briefing based on the primary field report says that {result}.",
            f"A later digest repeats the briefing's account: {result}.",
            f"A news summary traces its account to the primary field report and states that {result}.",
        ]
        edges = [
            {"source_id": ids[0], "derivative_id": ids[1], "transformation": "attributed_summary"},
            {"source_id": ids[1], "derivative_id": ids[2], "transformation": "digest"},
            {"source_id": ids[0], "derivative_id": ids[3], "transformation": "news_summary"},
        ]
        links[1], links[2], links[3] = [urls[0]], [urls[1]], [urls[0]]
    elif condition == "four_independent":
        families = [[item] for item in ids[:4]]
        texts = [
            f"Team {letter} evaluated a separate sample {world:03d}-{i + 1}; {result}."
            for i, letter in enumerate("ABCD")
        ]
    elif condition == "verbatim_derivative":
        families = [ids[:4]]
        texts = [f"The investigation reports that {result}."] * 4
        edges = [
            {"source_id": ids[0], "derivative_id": ids[i], "transformation": "near_exact_reuse"}
            for i in range(1, 4)
        ]
    elif condition == "attributed_paraphrase":
        families = [ids[:4]]
        texts = [f"The original investigation reports that {result}."] + [
            f"According to the earlier investigation, the available finding is that {result}."
            for _ in range(3)
        ]
        edges = [
            {
                "source_id": ids[0],
                "derivative_id": ids[i],
                "transformation": "attributed_restatement",
            }
            for i in range(1, 4)
        ]
        for i in range(1, 4):
            links[i] = [urls[0]]
    elif condition == "unattributed_multihop":
        families = [ids[:4]]
        texts = [
            f"A field investigation concludes that {result}.",
            f"One account describes the finding this way: {result}.",
            f"A subsequent bulletin reports the same outcome: {result}.",
            f"A later digest says the available evaluation indicates that {result}.",
        ]
        edges = [
            {
                "source_id": ids[i],
                "derivative_id": ids[i + 1],
                "transformation": "uncredited_restatement",
            }
            for i in range(3)
        ]
    elif condition == "two_roots":
        families = [ids[:2], ids[2:4]]
        texts = [
            f"Team A's sample {world:03d}-A found that {result}.",
            f"A bulletin citing Team A states that {result}.",
            f"Team B's separate sample {world:03d}-B found that {result}.",
            f"A digest citing Team B states that {result}.",
        ]
        edges = [
            {"source_id": ids[0], "derivative_id": ids[1], "transformation": "attributed_summary"},
            {"source_id": ids[2], "derivative_id": ids[3], "transformation": "attributed_summary"},
        ]
        links[1], links[3] = [urls[0]], [urls[2]]
    elif condition == "same_wording_independent":
        families = [[item] for item in ids[:4]]
        texts = [
            f"Independent sample {world:03d}-{i + 1} was collected by Team {letter}. The investigation reports that {result}."
            for i, letter in enumerate("ABCD")
        ]
    elif condition == "same_domain_independent":
        families = [[item] for item in ids[:4]]
        texts = [
            f"Division {letter} collected its own sample {world:03d}-{i + 1}; its evaluation found that {result}."
            for i, letter in enumerate("ABCD")
        ]
    elif condition == "shared_dataset":
        families = [ids[:2], [ids[2]], [ids[3]]]
        texts = [
            f"Analysis one uses dataset DS-{world:03d}-A and finds that {result}.",
            f"Analysis two reuses dataset DS-{world:03d}-A and finds that {result}.",
            f"A separate dataset DS-{world:03d}-B indicates that {result}.",
            f"A separate dataset DS-{world:03d}-C indicates that {result}.",
        ]
        bases[tuple(sorted((ids[0], ids[1])))] = "dataset"
    elif condition == "shared_study_replication":
        families = [ids[:2], [ids[2]], [ids[3]]]
        texts = [
            f"The original study on sample ST-{world:03d}-A reports that {result}.",
            f"A commentary summarizes study ST-{world:03d}-A and states that {result}.",
            f"A replication on newly collected sample ST-{world:03d}-B finds that {result}.",
            f"A second replication on sample ST-{world:03d}-C finds that {result}.",
        ]
        edges = [{"source_id": ids[0], "derivative_id": ids[1], "transformation": "study_summary"}]
        links[1] = [urls[0]]
    else:
        families = []
        texts = [
            f"An account says that {result}, but it does not identify the observation used.",
            f"A second account says that {result}, without naming a study or source.",
            f"A short note gives the same statement—{result}—but supplies no provenance.",
            f"The available page states that {result}; its relationship to the other accounts is not documented.",
        ]

    texts.extend([neutral for _ in range(8)])
    normalized = [
        f"{text} The report describes the setting, method, and observations available to its authors."
        for text in texts
    ]
    docs = [
        {
            "doc_id": ids[i],
            "url": urls[i],
            "title": f"Report on {topic} ({rng.randrange(1000, 9999)})",
            "text": normalized[i],
            "published_at": dates[i],
            "domain": domains[i],
            "outbound_links": links[i],
        }
        for i in range(12)
    ]
    rng.shuffle(docs)

    relationships = []
    family_index = {doc_id: index for index, family in enumerate(families) for doc_id in family}
    direct = {(edge["source_id"], edge["derivative_id"]) for edge in edges}
    direct |= {(right, left) for left, right in direct}
    for left, right in combinations(ids[:4], 2):
        pair = tuple(sorted((left, right)))
        if condition == "ambiguous_provenance":
            relation, basis, observable, action = "unknown", "unknown", "indeterminate", "abstain"
        elif family_index[left] != family_index[right]:
            relation, basis, observable, action = (
                "independent",
                "distinct_observation",
                "explicit",
                "distinct_families",
            )
        elif pair in bases:
            relation, basis, observable, action = (
                "common_dependency",
                bases[pair],
                "explicit",
                "same_family",
            )
        elif (left, right) in direct:
            relation, basis, observable, action = (
                "direct_derivative",
                "upstream_document",
                "explicit" if links[ids.index(left)] or links[ids.index(right)] else "inferable",
                "same_family",
            )
        else:
            relation, basis, observable, action = (
                "indirect_derivative",
                "upstream_document",
                "inferable",
                "same_family",
            )
        relationships.append(
            {
                "left_doc_id": pair[0],
                "right_doc_id": pair[1],
                "relationship": relation,
                "dependency_basis": basis,
                "observability": observable,
                "action": action,
            }
        )

    relevant = ids[:4]
    gold = {
        "gold_root_count": 0 if condition == "ambiguous_provenance" else len(families),
        "gold_families": families,
        "gold_relationships": relationships,
        "gold_lineage_edges": edges,
        "gold_claim": {
            "text": claim,
            "verdict": verdict,
            "supporting_doc_ids": relevant if verdict == "supported" else [],
            "contradicting_doc_ids": relevant if verdict == "contradicted" else [],
            "relevant_doc_ids": relevant,
        },
        "condition": condition,
        "micro_world_id": f"world_{world:04d}",
        "split": split,
        "review_status": "gold_by_construction",
    }
    return {"case_id": opaque(rng, "case"), "query": query, "documents": docs}, gold


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=20260911)
    parser.add_argument("--out-dir", type=Path, default=Path(__file__).parents[1] / "data")
    args = parser.parse_args()
    rng = random.Random(args.seed)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    assignments: dict[int, tuple[str, str]] = {}
    for verdict_index, verdict in enumerate(("supported", "contradicted", "insufficient")):
        worlds = list(range(verdict_index, 240, 3))
        random.Random(args.seed + verdict_index + 1).shuffle(worlds)
        for world in worlds[:50]:
            assignments[world] = ("train", verdict)
        for world in worlds[50:60]:
            assignments[world] = ("validation", verdict)
        for world in worlds[60:]:
            assignments[world] = ("test", verdict)
    public, gold, manifest = [], [], []
    for world in range(240):
        split, verdict = assignments[world]
        for condition in CONDITIONS:
            visible, hidden = make_case(rng, world, condition, verdict, split)
            public.append(visible)
            gold.append({"case_id": visible["case_id"], **hidden})
            manifest.append(
                {
                    "case_id": visible["case_id"],
                    "world": world,
                    "condition": condition,
                    "split": split,
                }
            )
    public_path = args.out_dir / "echobench_synthetic_v1_public.jsonl"
    gold_path = args.out_dir / "echobench_synthetic_v1_gold.jsonl"
    manifest_path = args.out_dir / "echobench_synthetic_v1_manifest.json"
    with public_path.open("w", encoding="utf-8") as handle:
        for row in public:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    with gold_path.open("w", encoding="utf-8") as handle:
        for row in gold:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    manifest_path.write_text(
        json.dumps({"version": VERSION, "seed": args.seed, "cases": manifest}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "version": VERSION,
                "cases": len(public),
                "worlds": 240,
                "conditions": len(CONDITIONS),
                "public": str(public_path),
                "gold": str(gold_path),
                "manifest": str(manifest_path),
            }
        )
    )


if __name__ == "__main__":
    main()
