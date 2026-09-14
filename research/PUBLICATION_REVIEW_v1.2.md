# Publication review and LLM extension

## Evidence status

The v1.1 CPU study is complete. The LLM work is a training-only feasibility pilot, described in
experiments/llm_pilot_v1.2.md, and cannot establish held-out agent improvements. No human review
or real-source observations have been supplied. Do not label a generated or AI-reviewed annotation
as a judgment by Ayush Dev or an independent human.

## Closest work checked against primary sources, 2026-09-13

- Bara, *Epistemic Sybil Resistance* (2026), https://arxiv.org/html/2609.01873v1:
  Section 8 uses a single main language model for numerical extraction and explicit aggregators.
  It already separates report count, evidence roots, and similarity. EchoTrace must establish
  value in document-level observable provenance inference and its downstream consequences.
  Multi-model testing alone does not establish a new scientific contribution.
- Li, Padman, and Krishnan, *Same Question, Different Source, Different Answer* (2026),
  https://arxiv.org/abs/2605.29084: institutional-source disagreement in medical RAG.
  This differs from shared-origin inference. Corrected the manuscript's first-author given name
  and title to match the primary record.
- Qian et al., *Relevant Is Not Warranted* (2026), https://arxiv.org/abs/2605.28044:
  compares calibrated versus force-raised claims. Distinguish evidence warrant from provenance.
- Bibliographic title/author checks also performed for ALCE, DeepResearch Bench, Cited but Not
  Verified, DeepWeb-Bench, and LineageRAG using their ACL/arXiv records. This is not a complete
  reference or licensing audit.

## Material issues and actions

**Submission blocker discovered during this review:** the training-only chronological audit
found 577/2,250 lineage edges with a later-dated source than derivative. See
`artifacts/chronology-audit-train-v1.1.json` and `scripts/audit_training_chronology.py`.
The original structural tests did not check this. Link detection time-orders document pairs,
so this can also affect link features, not just the chronology ablation. The direction and
magnitude of its impact on test performance have not been measured. Do not silently repair
the frozen release or claim that unchanged test scores apply to a corrected version.

`scripts/generate_development_v1_2.py` now produces 33 training-only development cases with
chronologically valid lineage. This corrects timestamp ordering only; it does not resolve
template generalization, partial overlap, or provenance observability. Human inspection and a
full new release/evaluation are still necessary. The main manuscript discloses this defect.

1. The legacy naturalistic API prompt asks for predicted evidence groups. That can prime
   independence reasoning. New ordinary-answer prompts omit it; provenance diagnostics must be
   independent calls, not appended questions in the same conversation.
2. The simulation's `excess_absolute_log_odds` field is absolute log-odds error, not a signed or
   one-sided excess. Corrected manuscript terminology without changing frozen artifacts.
3. The explanation of numeric-ablation performance was too causal. Rephrased as a hypothesis
   requiring a new experiment. Preserve the negative result and avoid test-driven model selection.
4. Current synthetic verdicts are directly stated in short templates. A ceiling in LLM accuracy
   is plausible and does not prove dependence reasoning. Use pilot observations to decide whether
   answer verdicts are sensitive enough; measure family recovery and false corroboration directly.
5. Three pilot worlds are too few for useful generalization intervals or power estimation. The
   planned 12 cases and 108 calls are infrastructure checks, not a publication-sized sample.
6. Model listing does not establish generation access or free quota. Record failed generation
   calls and actual returned model IDs. No routing across model families or silent replacements.
7. User-provided keys are in an ignored local .env file; no keys belong in release artifacts.

## Work required for a strong LLM submission

- Inspect observability with humans, complete the 66-case author audit, and obtain an independent
  second annotation where feasible. Final gold must distinguish unknown from incorrect inference.
- Develop new topic/prose holdouts, stronger controlled dependence manipulations, and clean
  evaluation material. Do not claim new random strings make templates unseen.
- Compare standard, instruction-only, semantic/lexical grouping, inferred provenance, and oracle
  provenance under the same evidence access. Record metadata overhead and preserve relevant facts.
- Evaluate ordinary answers for explicit false-corroboration claims with a blinded human rubric.
  Separately evaluate family partitions/counts, abstention, and partial overlap. Do not use a
  decrease in evidence-verdict confidence as a surrogate for normative truth calibration.
- Choose co-primary outcomes and a smallest meaningful effect; calculate the required number of
  worlds after a larger development pilot. Include paired world-level inference, multiplicity
  control, missing-output coverage, and robustness to document ordering and repeated calls.
- Archive the final protocol before new held-out API calls; implement that study only after its
  data and measurement decisions are resolved. Include a real-source pilot and independent review.
- Select a venue and follow its official current template, anonymity, page-limit, and AI-use
  disclosure rules. Archive a release after credential/license review. The repository currently
  has no Git commits; a local SHA-256 freeze is not external preregistration.

## Local execution

```bash
OPENBLAS_NUM_THREADS=1 .venv/bin/python scripts/run_llm_pilot.py prepare
.venv/bin/python scripts/run_llm_pilot.py execute --provider gemini
.venv/bin/python scripts/run_llm_pilot.py execute --provider groq
.venv/bin/python scripts/run_llm_pilot.py execute --provider openrouter
.venv/bin/python scripts/run_llm_pilot.py summarize
```

The prepared directory is immutable; preparation fails if it already exists. Execution resumes
only not-yet-attempted requests, never retries failed/uncertain ones, and rejects changed study
inputs. No inference calls are made by prepare or summarize. Account upgrades and publishing
are separate actions, not performed by this workflow.
