# EchoTrace

EchoTrace is a reproducible research scaffold for testing whether AI research agents mistake
copied, paraphrased, or unattributed reports for independent corroboration.

The repository contains:

- **EchoBench v1.1**: 2,640 deterministic cases from 240 fictional micro-worlds, with separate
  public and evaluator-only gold views. The original 400-case v0.1 release is preserved.
- **EchoGraph**: an interpretable source-dependence detector and independence-aware reranker.
- **Agent runner**: mock and OpenAI-compatible API adapters with caching and budget limits.
- **Evaluation**: lineage, root-count, false-corroboration, citation, utility, and cost metrics.
- **Paper**: an IEEE-style manuscript reporting the completed v1.1 CPU study, with a separate
  exploratory LLM feasibility report under development.
- **Research controls**: a gold-blind author audit, author-curated real-source pilot, integrity
  freeze, whole-world bootstrap inference, and leakage safeguards. The first-paper study runs on
  CPU and requires neither a CUDA GPU nor a paid API.

## Quick start

```bash
python3 scripts/generate_benchmark.py
python3 -m unittest discover -s tests -v
python3 -m echotrace.cli validate --data data/echobench.jsonl
python3 -m echotrace.cli run --data data/echobench.jsonl --split test \
  --agent mock --method standard --output artifacts/runs/mock-standard.jsonl
python3 -m echotrace.cli score --data data/echobench.jsonl \
  --responses artifacts/runs/mock-standard.jsonl
python3 scripts/export_paper_assets.py \
  --run smoke=artifacts/runs/mock-standard.jsonl --allow-smoke
```

The mock agent tests plumbing and is deliberately incapable of producing a publishable result.

## Optional API-backed models

Paid APIs and local generative models are legacy/optional extensions and are not required for the
CPU-first paper. Use the API adapter only for a separately funded supplementary comparison.

Copy `configs/models.example.json` to `configs/models.json`, replace model identifiers and
endpoint URLs with dated stable versions, and set the named environment variables. Secrets are
never stored in traces. The adapter targets OpenAI-compatible `chat/completions` endpoints.
Prices must be nonzero and current before a frozen run; `max_input_tokens` and `max_output_tokens`
provide a conservative per-request cost bound.

```bash
export PROVIDER_API_KEY=...
python3 -m echotrace.cli run --data data/echobench.jsonl --split test \
  --agent api --model-config configs/models.json --model-id provider-name \
  --method echograph --output artifacts/runs/provider-echograph.jsonl \
  --budget-usd 100
```

Preview the full matrix without network calls or spend:

```bash
python3 scripts/run_matrix.py --config configs/experiment.example.json
```

Execution additionally requires a fully reviewed dataset, all credentials, `--execute`, and an
exact `--confirm-budget` value. Existing JSONL outputs are resumed by case ID.

## Review, audit, and statistics

The [annotation guide](annotations/ANNOTATION_GUIDE.md), [live-audit protocol](data/LIVE_AUDIT_PROTOCOL.md),
and [frozen protocol](PROTOCOL.md) define the manual work and locked claims. Their validators are:

```bash
python3 -m echotrace.cli reviews --data data/echobench.jsonl --ledger annotations/reviews.csv
python3 -m echotrace.cli audit --data data/live_audit.csv
python3 scripts/analyze_runs.py --baseline artifacts/runs/baseline.jsonl \
  --candidate artifacts/runs/echograph.jsonl
python3 scripts/tune_threshold.py --output artifacts/threshold-selection.json
```

The analysis reports matched-micro-world bootstrap intervals, paired randomization p-values, and
Holm corrections. Install `.[research]` for the optional prespecified mixed-effects follow-up.

## Scientific safeguards

- Tune features and thresholds on `train`/`validation`; do not inspect test labels during tuning.
- Run `freeze` before final experiments to record dataset, prompt, and configuration hashes.
- Never replace the paper's pending macros with invented results.
- Human verification status is tracked separately. Generated cases are not described as
  human-verified until the two reviews and adjudication fields are complete.
- `data/echobench.jsonl` is immutable generated input; applying reviews writes a separate reviewed
  artifact.

## Paper

`paper/main.tex` uses `IEEEtran` in conference mode. The compiled PDF is `paper/main.pdf`.
See [paper/README.md](paper/README.md) for the build and [editorial notes](paper/EDITORIAL_NOTES.md)
for evidence limits and the changes required before a confirmatory study. The original paper is
preserved in `paper/archive/`.

```bash
OPENBLAS_NUM_THREADS=1 python3 scripts/paper_validation.py
.tools/tectonic/tectonic --keep-logs paper/main.tex
```

The new paper analysis uses oracle supporters on validation only and is separate from the legacy
agent exporter. `artifacts/graph-validation.json` and `artifacts/threshold-selection.json` have an
all-document/supporting-family scope mismatch; do not cite them as supporting-family evaluation.
The existing `PROTOCOL.md` is an uncompleted draft checklist, not proof of archived preregistration.

## EchoBench-Synthetic v1.1 (current research track)

The repaired benchmark keeps condition and provenance labels out of the public retrieval view.
Generate it deterministically and run the structural leakage checks with:

```bash
python3 scripts/generate_benchmark_v1.py --seed 20260911
python3 scripts/validate_benchmark_v1.py
python3 scripts/leakage_probe_v1.py
```

The generator writes separate public and gold JSONL files plus a split manifest. The v1 research
questions, factorized provenance taxonomy, annotation rules, and frozen experimental protocol are
in `research/questions_v1.md`, `annotations/v1/README.md`, and `experiments/protocol_v1.md`.
The older `data/echobench.jsonl` remains preserved as EchoBench-Synthetic v0.1 for reproducibility
of the exploratory paper results.

### v1 readiness and execution

The current v1 release is balanced by verdict within every world-disjoint split and uses
evidence-entailment labels. Validate the evaluator-side join with:

```bash
python3 -m echotrace.cli validate \
  --v1-public data/echobench_synthetic_v1_public.jsonl \
  --v1-gold data/echobench_synthetic_v1_gold.jsonl \
  --v1-manifest data/echobench_synthetic_v1_manifest.json
python3 scripts/leakage_probe_v1.py
.venv/bin/python scripts/evaluate_v1_detection.py --split validation --tune \
  --include-semantic --output artifacts/detection-validation-v1.1.json
.venv/bin/python scripts/simulate_confidence_v1.py --split validation \
  --include-semantic --output artifacts/confidence-simulation-validation-v1.1.json
```

The first study is synthetic and gold-by-construction; it makes no completed human-validation or
real-world-generalization claim. Create the integrity freeze with:

```bash
python3 scripts/freeze_cpu_study_v1.py
```

Then run the two held-out commands in `experiments/protocol_v1.md`. Each verifies every frozen hash
and records its one-shot completion. The prepared audit and live-source workflows remain available
for a later study but must not be reported as completed.

For future sessions, the durable research handoff is [research/PROJECT_CONTEXT.md](research/PROJECT_CONTEXT.md).

## LLM extension (v1.2 development)

The new LLM feasibility pilot uses provider credentials in a local ignored `.env` file. It runs
on training data and does not constitute held-out agent evaluation. The older API runner uses a
different dataset/prompt workflow; use `scripts/run_llm_pilot.py` for this pilot.

See [pilot protocol](experiments/llm_pilot_v1.2.md),
[publication review](research/PUBLICATION_REVIEW_v1.2.md), and
[Gemini availability amendment](experiments/llm_pilot_gemini_amendment.md).
The runner archives prompts, retains failures, checks input hashes, and never silently retries
failed requests. Model aliases and free quotas can change; an API key alone does not verify billing.

```bash
# Read-only with respect to providers: summarize existing results.
.venv/bin/python scripts/run_llm_pilot.py summarize
```

The LLM study still needs human checks and a separately specified final evaluation before its
results can support stronger publication claims.
