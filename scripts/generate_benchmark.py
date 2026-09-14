#!/usr/bin/env python3
from __future__ import annotations

import argparse
import random
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from echotrace.io import write_cases  # noqa: E402
from echotrace.schemas import (  # noqa: E402
    BenchmarkCase,
    Document,
    GoldClaim,
    LineageEdge,
)

DOMAINS = (
    "health",
    "science",
    "environment",
    "public-policy",
    "finance",
    "consumer-technology",
    "transportation",
    "workplace",
)
CONDITIONS = ("exact_echo", "paraphrase_echo", "cross_domain_echo", "two_roots", "four_roots")
CONDITION_CODES = {name: f"c{index}" for index, name in enumerate(CONDITIONS)}
SUBJECTS = (
    "the Aster Vale program",
    "the Belora field trial",
    "the Cinder Lake initiative",
    "the Dorin measurement project",
    "the Elara municipal pilot",
    "the Fennel Ridge study",
    "the Gannet Point deployment",
    "the Helio North assessment",
    "the Iridia workplace experiment",
    "the Juniper transit evaluation",
)
MEASURES = (
    "completion time",
    "reported energy use",
    "average processing delay",
    "measured error rate",
    "weekly participation",
    "material consumption",
    "service interruptions",
    "average response time",
)
DOMAINS_POOL = (
    "northstar.example",
    "dailyledger.example",
    "evidencepost.example",
    "civicwire.example",
    "researchbrief.example",
    "marketobserver.example",
    "techwindow.example",
    "publicrecord.example",
    "independentdesk.example",
    "reportinghub.example",
)
CONTEXT_SENTENCES = (
    "The report describes the comparison period, measurement procedure, and observed result.",
    "The note summarizes the measured outcome and the baseline used in the comparison.",
    "The article gives the evaluation window and reports the resulting estimate.",
    "The brief records the observed result together with a short description of the assessment.",
)


def split_for(world_index: int) -> str:
    if world_index < 48:
        return "train"
    if world_index < 60:
        return "validation"
    return "test"


def number_fingerprint(world_index: int) -> tuple[int, int]:
    supported = 11 + (world_index * 7) % 73
    contradicted = supported + 5 + world_index % 9
    return supported, contradicted


def support_sentence(subject: str, measure: str, value: int) -> str:
    return f"The final assessment found that {subject} reduced {measure} by {value} percent."


def support_variant(subject: str, measure: str, value: int, variant: int) -> str:
    choices = (
        f"Reviewers reported a {value} percent reduction in {measure} after evaluating {subject}.",
        f"According to the published assessment, {measure} fell by {value} percent during {subject}.",
        f"Results attributed to {subject} show {measure} was {value} percent lower than the baseline.",
        f"A comparison with baseline conditions puts the decline in {measure} at {value} percent for {subject}.",
    )
    return choices[variant % len(choices)]


def make_document(
    doc_id: str,
    domain: str,
    day: date,
    title: str,
    sentence: str,
    links: tuple[str, ...] = (),
    attribution: str = "",
) -> Document:
    lead = f"{attribution} " if attribution else ""
    context = CONTEXT_SENTENCES[sum(ord(character) for character in doc_id) % len(CONTEXT_SENTENCES)]
    text = f"{lead}{sentence} {context}"
    return Document(
        doc_id=doc_id,
        url=f"https://{domain}/{doc_id}",
        title=title,
        text=text,
        published_at=f"{day.isoformat()}T09:00:00Z",
        domain=domain,
        author=f"Desk {int(doc_id[-1], 36) % 7 + 1}",
        outbound_links=links,
        metadata={"language": "en"},
    )


def build_case(world_index: int, condition: str, rng: random.Random) -> BenchmarkCase:
    world_id = f"mw-{world_index:03d}"
    case_id = f"{world_id}-{CONDITION_CODES[condition]}"
    topic = DOMAINS[world_index % len(DOMAINS)]
    subject = f"{SUBJECTS[world_index % len(SUBJECTS)]} {world_index + 17}"
    measure = MEASURES[world_index % len(MEASURES)]
    supported, contradicted = number_fingerprint(world_index)
    base_day = date(2031, 1, 1) + timedelta(days=world_index * 11)
    chosen_domains = rng.sample(DOMAINS_POOL, 8)
    documents: list[Document] = []
    edges: list[LineageEdge] = []
    families: list[list[str]] = []
    supporting_ids: list[str] = []

    if condition in {"exact_echo", "paraphrase_echo", "cross_domain_echo"}:
        root_id = f"{case_id}-s0"
        root_url = f"https://{chosen_domains[0]}/{root_id}"
        root_sentence = support_sentence(subject, measure, supported)
        documents.append(
            make_document(root_id, chosen_domains[0], base_day, f"Assessment of {subject}", root_sentence)
        )
        family = [root_id]
        supporting_ids.append(root_id)
        for index in range(1, 4):
            doc_id = f"{case_id}-s{index}"
            if condition == "exact_echo":
                sentence = root_sentence
                attribution = "A previously published assessment states that"
                links = (root_url,)
                transform = "near_verbatim"
            elif condition == "paraphrase_echo":
                sentence = support_variant(subject, measure, supported, index)
                attribution = "A review of an earlier report concludes that"
                links = (root_url,)
                transform = "paraphrase"
            else:
                sentence = support_variant(subject, measure, supported, index + 1)
                attribution = ""
                links = ()
                transform = "attribution_stripped"
            documents.append(
                make_document(
                    doc_id,
                    chosen_domains[index],
                    base_day + timedelta(days=index * 3),
                    f"New findings concerning {subject}",
                    sentence,
                    links,
                    attribution,
                )
            )
            family.append(doc_id)
            supporting_ids.append(doc_id)
            edges.append(LineageEdge(root_id, doc_id, transform))
        families.append(family)
    else:
        root_total = 2 if condition == "two_roots" else 4
        for index in range(root_total):
            root_id = f"{case_id}-s{index}"
            documents.append(
                make_document(
                    root_id,
                    chosen_domains[index],
                    base_day + timedelta(days=index),
                    f"Observation {index + 1} for {subject}",
                    support_variant(subject, measure, supported, index),
                )
            )
            families.append([root_id])
            supporting_ids.append(root_id)
        if condition == "two_roots":
            for index in range(2, 4):
                parent_index = index - 2
                parent_id = f"{case_id}-s{parent_index}"
                parent_url = f"https://{chosen_domains[parent_index]}/{parent_id}"
                doc_id = f"{case_id}-s{index}"
                documents.append(
                    make_document(
                        doc_id,
                        chosen_domains[index],
                        base_day + timedelta(days=5 + index),
                        f"Follow-up coverage of {subject}",
                        support_variant(subject, measure, supported, index + 1),
                        (parent_url,),
                        "Based on an earlier observation,",
                    )
                )
                edges.append(LineageEdge(parent_id, doc_id, "paraphrase"))
                families[parent_index].append(doc_id)
                supporting_ids.append(doc_id)

    contradicting_ids: list[str] = []
    for index in range(2):
        doc_id = f"{case_id}-c{index}"
        contradicting_ids.append(doc_id)
        sentence = (
            f"An independent check instead estimated that {subject} reduced {measure} by "
            f"{contradicted + index} percent."
        )
        documents.append(
            make_document(
                doc_id,
                chosen_domains[4 + index],
                base_day + timedelta(days=2 + index),
                f"Contrasting estimate for {subject}",
                sentence,
            )
        )
    for index in range(2):
        doc_id = f"{case_id}-d{index}"
        sentence = (
            f"A planning memorandum mentions {subject} but does not report a measured change in "
            f"{measure}; it discusses staffing scenario {world_index + index + 3} instead."
        )
        documents.append(
            make_document(
                doc_id,
                chosen_domains[6 + index],
                base_day + timedelta(days=7 + index),
                f"Planning note about {subject}",
                sentence,
            )
        )
    assert len(documents) == 8
    rng.shuffle(documents)
    claim_text = support_sentence(subject, measure, supported)
    return BenchmarkCase(
        case_id=case_id,
        micro_world_id=world_id,
        query=(
            f"What percentage reduction in {measure} was reported for {subject}? Assess the "
            "evidence, cite the documents used, and state confidence."
        ),
        documents=tuple(documents),
        condition=condition,
        gold_claims=(
            GoldClaim(
                text=claim_text,
                verdict="supported",
                supporting_doc_ids=tuple(supporting_ids),
                contradicting_doc_ids=tuple(contradicting_ids),
            ),
        ),
        gold_lineage_edges=tuple(edges),
        gold_root_count=len(families),
        gold_families=tuple(tuple(group) for group in families),
        split=split_for(world_index),
        review_status="generated",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(ROOT / "data" / "echobench.jsonl"))
    parser.add_argument("--seed", type=int, default=20260911)
    args = parser.parse_args()
    rng = random.Random(args.seed)
    cases = [
        build_case(world_index, condition, rng)
        for world_index in range(80)
        for condition in CONDITIONS
    ]
    write_cases(args.output, cases)
    print(f"wrote {len(cases)} cases to {args.output}")


if __name__ == "__main__":
    main()
