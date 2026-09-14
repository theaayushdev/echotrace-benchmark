# EchoTrace project context

This file is the durable handoff for future sessions. The project owner is Ayush Dev. The
confirmed affiliation is Nepal Engineering College, Bhaktapur, Nepal. Do not invent any other
authors, supervisors, reviewers, or affiliations.

## Research direction

EchoTrace studies false corroboration: the overestimation of evidential support when dependent
reports are treated as independent observations. The first paper is a CPU-feasible controlled
benchmark and simulation study, targeting an ACL-family Student Research Workshop.

Primary questions:

1. Can an AI system distinguish independent evidence from repeated or derivative reporting?
2. Under explicit Bayesian assumptions, how much confidence inflation follows from document counts?
3. Which visible signals drive EchoGraph-Classic's source-family inference performance?

Use the narrower term **source-family dependence**. It means that documents rely on the same
underlying observation, study, dataset, event, measurement, or upstream report. It is not a claim
that the system has established universal epistemic independence or truth.

## Agreed scope and safeguards

RQ1--RQ3 are the main study. Keep the existing v0.1 data
and paper results reproducible, but do not present them as confirmatory. The v1 benchmark uses
opaque public IDs, separate gold provenance, balanced supported/contradicted/insufficient cases,
ambiguous labels with abstention, world-level train/validation/test splits, CPU baselines,
EchoGraph feature ablations, and a Bayesian sensitivity analysis. Freeze the protocol and test set
before final evaluation.

See `research/questions_v1.md`, `experiments/protocol_v1.md`, `research/literature_review.csv`,
and `annotations/v1/README.md`. Generate/validate the current synthetic release with:

```bash
python3 scripts/generate_benchmark_v1.py --seed 20260911
python3 scripts/validate_benchmark_v1.py
```

## Current v1 status (2026-09-12)

EchoBench-Synthetic v1.1 contains 2,640 cases in 240 world-disjoint micro-worlds. The CPU protocol
was frozen and both one-shot held-out runs are complete. Test artifacts are
`artifacts/detection-test-v1.1.json` and `artifacts/confidence-simulation-test-v1.1.json`; the freeze
manifest records both completions. `paper/main.tex` and `paper/main.pdf` now report those results.
The paper is synthetic-only and gold-by-construction because the prepared human-audit and
real-source ledgers contain no observations. It must make no human-validation or real-world
generalization claim. There is no CUDA/GPU dependency in the first-paper study.

Related work includes TransplantQA/HERO-QA (Li, Padman, and Krishnan, 2026), which examines
institutional-source disagreement. Bara's Epistemic Sybil Resistance (2026, arXiv:2609.01873)
is more directly relevant to report multiplicity, ancestry, and overconfidence. EchoTrace must
defend its narrower contribution in observable document-family inference and downstream use.

## LLM development update (2026-09-13)

The owner requested an LLM extension and supplied Gemini, Groq, and OpenRouter credentials in
an ignored local .env file. Never print or share the credentials. He can ask a teacher or
classmate to independently review examples; no human judgments have yet been returned.

Implemented a separate training-only feasibility pilot:
- `experiments/llm_pilot_v1.2.md` and `configs/llm_pilot_v1.2.json`;
- `echotrace/llm_pilot.py`, `scripts/run_llm_pilot.py`, and six offline tests;
- immutable prompt/config/input hashes in `artifacts/llm-pilot-v1.2/plan.json`;
- 12 training cases from three worlds, excluding prepared author-audit worlds, three arms
  (standard, instruction, echograph), identical four relevant documents per arm.

Completed Qwen3.8-27B via Groq (36/36 schema-valid) and Nemotron 3 Super via OpenRouter
(35/36 schema-valid, one unusable provider response). Gemini 3.8 Flash returned two HTTP 503
responses; the separately documented Gemini 3.7 alternative also returned HTTP 503 on its
first call. No Gemini behavior results exist. Requests to the original model were not
silently replaced or pooled with the alternative. There were 75 generation attempts overall:
72 across Groq/OpenRouter plus three unsuccessful Gemini attempts.

`research/LLM_PILOT_RESULTS.md` contains the actual outcomes. Effects are mixed, sample size
is only three worlds, and the detector was trained on these worlds. A Qwen ordinary answer
asserted independent reports where provenance was unknown; one Nemotron response copied an
answer placeholder. These observations motivate human review, not a claimed general error rate.

`annotations/llm_pilot/STARTER_PACKET.md`, `STARTER_REVIEWS.csv`, and `REVIEW_GUIDE.md` provide
12 blinded examples for a teacher/classmate. The CSV contains IDs and blank judgment fields,
not completed annotations. Do not give reviewers evaluator_mapping.json or raw provider logs.

### Submission blocker: chronology

A post-freeze TRAINING-only audit found 577/2,250 gold lineage edges with a source timestamp
later than its derivative. The old structural validator did not check this; time-ordering also
affects link-feature computation. See `artifacts/chronology-audit-train-v1.1.json`.
All original CPU frozen hashes still match. Do not silently modify the old data or rerun its
held-out study. `main.tex` now discloses this issue and has corrected related work, log-odds
error terminology, and restrained numeric-ablation interpretation.

`echotrace/chronology.py` and `scripts/generate_development_v1_2.py` produce a 33-case
training-only chronology-corrected sample in `data/development-v1.2/`. It changes 17 dates,
has zero reversed edges, uses the SAME prose templates, and has no human validation. It is
not the final corrected benchmark or a fresh held-out test. Two chronology tests were added.

### Required next work

Collect independent human judgments; validate corrected and diversified benchmark construction;
finalize provenance diagnostics and corroboration scoring; determine sample size with a larger
development pilot; archive a final protocol; then run fresh held-out evaluation. The proposed
design is `experiments/llm_confirmatory_v1.2_DRAFT.md` and is NOT frozen or preregistered.
See `research/PUBLICATION_REVIEW_v1.2.md` for the critical review. The current main manuscript
and separate `paper/llm-pilot.tex` are development artifacts, not submission-ready claims.
