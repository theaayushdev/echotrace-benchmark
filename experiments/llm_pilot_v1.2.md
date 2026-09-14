# EchoTrace LLM feasibility pilot v1.2

Status: exploratory training-only pilot; specified before pilot generation calls.
This is not the confirmatory LLM study or external preregistration.

## Purpose

Verify API access, structured answers, runtime, quotas, and outcome sensitivity before designing
the final study. An API key grants access to a provider, not evidence that every listed model
can generate successfully. Gemini, Qwen (Groq), and Nemotron (OpenRouter) are requested by explicit
model ID in configs/llm_pilot_v1.2.json. Record returned model IDs and provider fingerprints where
available; aliases are not immutable weight snapshots.

## Sample and intervention

Choose the lexicographically first eligible training world for each verdict (supported,
contradicted, insufficient), excluding all worlds in the prepared author audit. Include four
conditions from each world: single_origin, four_independent, shared_dataset, ambiguous_provenance.
This is 12 cases and three worlds, not 12 independent replicates. The selection is deterministic
and makes no reference to model performance.

Each case is submitted in three isolated calls: standard, instruction, echograph. Standard asks
for an evidence verdict, short answer, three-class probabilities, and citations. It does NOT ask
for family counts or mention independence. Instruction adds a source-dependence reminder.
EchoGraph uses the identical reminder plus an explicitly fallible inferred partition. All arms
receive identical four gold-relevant documents in identical order; this is oracle relevance,
not retrieval evaluation. All document text is preserved. Extra metadata tokens are recorded,
not described as equal input token usage. Output caps and requested temperature (0) are equal.
Within each case, arm order is rotated deterministically to reduce fixed-order confounding.

EchoGraph is fitted on the existing determinate v1.1 training cases and uses the previously fixed
v1.1 threshold. Therefore this pilot is in-sample for the detector and cannot measure detector
generalization or confirm its mitigation effectiveness. The pilot prompts are archived and hashed
before API calls. Gold labels, split, world, and condition are never serialized into a request.

## Outcomes

Report every planned/attempted/valid/invalid/failed call per provider and arm. Require a valid
three-way verdict, finite probabilities in [0,1] summing to one, verdict attaining maximal
probability, a nonempty answer, and citations referring only to shown documents. Invalid outputs
are retained and not silently repaired or retried. Report accuracy and multiclass Brier score
(unhalved sum of squared class-probability errors) on valid responses with explicit denominators.
These probabilities describe the evidence-entailment verdict, NOT factual truth or normative
Bayesian confidence. A drop in confidence alone is not evidence of improvement.

No inferential p-values or publishable effect estimates are warranted from three pilot worlds.
Pairwise intervention summaries use complete matched cases only. All failures remain in the
coverage report. This answer-only pilot cannot score source-family overcounting or human-judged
false-corroboration assertions; those require separate diagnostics/annotation.

## Execution and limits

At most 36 generation attempts per provider, 108 total. Use only the configured free OpenRouter
model, with fallback routing disabled. Use the user-provided Gemini/Groq accounts intended for
free access; account billing tier cannot be inferred from a key. No account upgrades, purchases,
paid-model substitution, or additional runs are automatic. Stop a provider on authentication,
billing, quota, network, or server errors. A failed call is recorded and not retried automatically.
Generation requests are journaled before sending; uncertain interrupted calls are not resubmitted.
Persist answers, usage, timestamps, request hashes, returned model IDs, and failure status.
Credentials are loaded as data (never sourced as shell code) and excluded from artifacts.

## Gates for a subsequent confirmatory study

1. Independent human inspection of provenance observability and answer/corroboration labels.
2. Novelty comparison with Bara (2026), arXiv:2609.01873, and Li et al. (2026), arXiv:2605.29084.
3. Fresh development and held-out worlds with held-out prose templates/topics; a new random seed
   on the same templates alone is not a generalization test. Keep pilot material out of test.
4. Separate ordinary-answer and explicit provenance-diagnostic calls. Add lexical/semantic
   deduplication and oracle-metadata controls; include independent-source preservation outcomes.
5. Determine required world count from pilot variability and a smallest meaningful effect.
   Fix co-primary metrics, missing-data handling, repeated-run design, multiplicity correction,
   confidence intervals, and all model/prompt/threshold choices before held-out collection.
6. Timestamp/archive that protocol before held-out collection; do not call this pilot preregistered.
7. Author-curated real-source pilot with accurately attributed human review and licensing.

The existing CPU study remains completed evidence. The LLM extension is unfinished until these
gates and its final evaluation are completed. No publication or acceptance is guaranteed.
