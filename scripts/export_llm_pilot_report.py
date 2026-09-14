#!/usr/bin/env python3
"""Export transparent pilot results and an empty, model-blinded human review packet."""
import csv
import hashlib
import json
import random
import sys
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from echotrace.llm_pilot import summarize


def main():
    directories = [ROOT / "artifacts/llm-pilot-v1.2", ROOT / "artifacts/llm-pilot-v1.2-gemini37"]
    records, summaries = [], []
    for directory in directories:
        if not directory.exists():
            continue
        summary = summarize(directory)
        plan = json.loads((directory / "plan.json").read_text())
        requests = {r["id"]: r for r in plan["requests"]}
        for provider, stats in summary["providers"].items():
            summaries.append((directory.name, provider, stats))
            path = directory / (provider + ".jsonl")
            if not path.exists():
                continue
            latest = {r["id"]: r for r in map(json.loads, path.read_text().splitlines())}
            for r in latest.values():
                if r["status"] != "valid":
                    continue
                records.append({**r, "run": directory.name, "evaluation": plan["cases"][r["case_id"]],
                                "prompt": requests[r["id"]]["prompt"]})

    lines = ["# EchoTrace LLM feasibility pilot", "",
        "Exploratory training-only results. These are not held-out results, human validation, or evidence of publication readiness.", "",
        "## Coverage", "", "| Run / provider | Requested model | Planned | Attempted | Schema-valid | Complete three-arm cases |",
        "|---|---|---:|---:|---:|---:|"]
    for run, provider, s in summaries:
        lines.append(f"| {run} / {provider} | {s['model']} | {s['planned']} | {s['attempted']} | {s['valid']} | {s['complete_paired_cases']} |")
    lines += ["", "## Evidence-verdict outcomes", "",
              "Schema validity is not answer quality. All denominators below include only schema-valid responses.", "",
              "| Run / provider | Arm | N | Verdict accuracy | Multiclass Brier |",
              "|---|---|---:|---:|---:|"]
    tex = []
    labels = {"gemini": "Gemini", "groq": "Qwen", "openrouter": "Nemotron"}
    for run, provider, s in summaries:
        for arm, a in s["arms"].items():
            if a["n_valid"]:
                lines.append(f"| {run} / {provider} | {arm} | {a['n_valid']} | {a['accuracy']:.3f} | {a['brier']:.4f} |")
                tex.append(f"{labels[provider]} & {arm} & {a['n_valid']} & {a['accuracy']:.3f} & {a['brier']:.4f} " + chr(92) * 2)
    lines += ["", "## Mechanical output-quality flags", "",
              "Flags were defined after seeing pilot outputs; they are descriptive checks, not preregistered outcomes.", ""]
    placeholder = [r for r in records if r["answer"]["answer"].strip().lower() == "at most 100 words"]
    long_answers = [r for r in records if len(r["answer"]["answer"].split()) > 100]
    lines += [f"- Literal answer-placeholder copies: {len(placeholder)}.",
              f"- Answers exceeding the requested 100-word length: {len(long_answers)}.",
              "- No independent human labels have been entered by this exporter.", "",
              "## Interpretation", "",
              "Only three training worlds were sampled. The detector was trained on these worlds. "
              "Correctly classifying directly stated evidence does not establish source-family reasoning. "
              "Probabilities concern evidence entailment, not truth. Brier scores here are not a measurement "
              "of real-world truth calibration. No significance tests or generalization intervals are reported.", "",
              "The original Gemini model returned availability errors. Its alternative is a separately "
              "identified run, not pooled as the same model. All raw failures remain in the JSONL logs.", "",
              "Source-family counts and human-rated false-corroboration rates are NOT measured by this pilot. "
              "The next experiment needs separate provenance diagnostics, human answer review, and fresh holdouts."]
    (ROOT / "research/LLM_PILOT_RESULTS.md").write_text("\n".join(lines) + "\n")
    (ROOT / "paper/generated/llm-pilot-rows.tex").write_text(
        "\\newcommand{\\PilotRows}{%\n" + "\n".join(tex) + "\n}\n")

    # Never overwrite a reviewer-filled ledger. Export only once after collection has stopped.
    review = ROOT / "annotations/llm_pilot"
    review.mkdir(exist_ok=True)
    packet = review / "packet.jsonl"
    if packet.exists():
        print("Existing review packet retained; delete/move it explicitly only if a new review is intended")
    else:
        random.Random(20260913).shuffle(records)
        rows, mapping = [], []
        for r in records:
            review_id = "review_" + hashlib.sha256((r["run"] + r["provider"] + r["id"]).encode()).hexdigest()[:16]
            prompt = r["prompt"]
            rows.append({"review_id": review_id,
                         "question_and_claim": prompt.split("Question: ", 1)[1].split("\nDocuments:", 1)[0],
                         "documents": prompt.split("\nDocuments:\n", 1)[1].split("\nReturn JSON only:", 1)[0],
                         "answer": r["answer"]})
            mapping.append({"review_id": review_id, "run": r["run"], "provider": r["provider"],
                            "request_id": r["id"], "case_id": r["case_id"], "arm": r["arm"]})
        packet.write_text("".join(json.dumps(r) + "\n" for r in rows))
        (review / "evaluator_mapping.json").write_text(json.dumps(mapping, indent=2) + "\n")
        with (review / "reviews.csv").open("x", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["review_id", "reviewer_id", "answer_substantive", "verdict_supported_by_text",
                             "asserts_independent_corroboration", "provenance_assertion_warranted",
                             "uncertainty_appropriate", "rationale", "evidence_span"])
        # Small balanced starter packet for a teacher/classmate; not a prevalence sample.
        selected, counts = [], Counter()
        by_id = {r["review_id"]: r for r in rows}
        for item in mapping:
            stratum = (item["provider"], item["arm"])
            if counts[stratum] < 2:
                selected.append(by_id[item["review_id"]])
                counts[stratum] += 1
        starter = ["# EchoTrace independent review: starter packet", "",
                   "Read REVIEW_GUIDE.md first. Judge only the shown evidence; model identities and gold labels are withheld.",
                   "This is a small exploratory sample, not a representative estimate of error rates.", ""]
        for index, row in enumerate(selected, 1):
            starter += [f"## Example {index}: {row['review_id']}", "",
                        row["question_and_claim"], "", "### Documents", "",
                        "```text", row["documents"], "```", "", "### Answer to review", "",
                        row["answer"]["answer"], "", "Verdict: " + row["answer"]["verdict"], "",
                        "Citations: " + ", ".join(row["answer"]["citations"]), ""]
        (review / "STARTER_PACKET.md").write_text("\n".join(starter) + "\n")
        with (review / "STARTER_REVIEWS.csv").open("x", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["review_id", "reviewer_id", "answer_substantive", "verdict_supported_by_text",
                             "asserts_independent_corroboration", "provenance_assertion_warranted",
                             "uncertainty_appropriate", "rationale", "evidence_span"])
            for row in selected:
                writer.writerow([row["review_id"]] + [""] * 8)
    print(json.dumps({"schema_valid_outputs": len(records), "placeholder_flags": len(placeholder),
                      "long_answer_flags": len(long_answers), "report": "research/LLM_PILOT_RESULTS.md"}))


if __name__ == "__main__":
    main()
