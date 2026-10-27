# LLM false-corroboration study on EchoBench-Synthetic v1.4 (protocol)

Status: DRAFT until `scripts/run_llm_study.py freeze` records the SHA-256 of this file, the study
code, configuration, dataset, and detector settings. No test-split request may be sent before the
freeze. Any change after the freeze requires a new protocol version and a new run directory.

This study replaces `llm_confirmatory_v1.2_DRAFT.md` for the zero-budget track. It uses only free
provider tiers. It is a closed-packet evidence-use study, not an autonomous web-agent study.

## Question and hypotheses

When an LLM receives four claim-relevant documents, does it count dependent reports as independent
evidence, and does provenance metadata reduce that error without harming verdicts?

- H1 (false corroboration): in the standard arm, on dependent conditions, models report more
  independent sources than the gold source-family count.
- H2 (confidence insensitivity): in the standard arm, a model's probability for the gold verdict
  is not materially higher with four independent families than with one origin, holding the world,
  claim, and verdict fixed. Because development responses were almost always at the probability
  ceiling, H2 is reported together with the ceiling rate (below); a sensitivity near zero with a
  high ceiling rate means saturation (full confidence from a single origin), not a measured
  inability to update.
- H3 (mitigation): EchoGraph-proposed source families reduce the false-corroboration rate relative
  to the standard arm, with verdict accuracy not lower by more than 0.05 and the undercount rate on
  independent conditions not higher by more than 0.10 (over-correction guard).

H1 and H2 are descriptive; their result is reported whichever way it falls. H3 is the single
confirmatory mitigation claim.

## Data

EchoBench-Synthetic v1.4 candidate (`data/echobench_synthetic_v1_4`), all 72 held-out test worlds
(24 per verdict). The sample size is fixed in advance as every test world; it is not chosen from
pilot results. Six conditions per world (432 cases):

| Condition | Gold families among relevant documents |
|---|---|
| single_origin | 1 |
| two_roots | 2 |
| shared_dataset | 3 |
| four_independent | 4 |
| same_wording_independent | 4 |
| ambiguous_provenance | undetermined (abstention) |

Dependent conditions for H1/H3 are single_origin, two_roots, and shared_dataset.
Each request contains the same four gold-relevant documents in their public order.

Development work uses the validation split only (12 worlds, same six conditions). The v1.4 test
split has not been used for detection, tuning, or any prior LLM request.

## Arms

All arms share the same evidence, question, claim, output schema, and output cap.

1. `standard`: no provenance guidance.
2. `reminder`: a fixed dependence reminder.
3. `echograph`: reminder plus EchoGraph-Classic proposed families, labelled as possibly wrong.
4. `oracle`: identical wording to `echograph`, but with gold families. It is a reference for the
   value of correct metadata, not a deployable method. For ambiguous cases it states that
   provenance could not be determined.

EchoGraph-Classic is trained on v1.4 training worlds with the threshold selected on validation
(`artifacts/v1.4-dev/detection-settings-v1.4.json`). The arm order per case rotates.

## Models

Three model families with verified free generation access on 2026-10-27:
`qwen/qwen3.8-27b` (Groq), `openai/gpt-oss-120b` (Groq), and `gemini-3.5-flash-lite` (Google).
Temperature 0. Requested and returned model IDs are logged. An unavailable model is reported as
missing; no substitute is pooled under its name.

## Output

JSON with answer (<= 100 words), verdict, verdict probabilities, citations, and
`independent_sources`: the number of distinct underlying observations, studies, or datasets among
the documents that bear on the claim, or `null` if this cannot be determined from the documents.
Asking for the count in every arm makes the standard arm a conservative baseline: it measures
counting errors even when the model is explicitly asked to consider independence.

## Outcomes

Primary (automatic; computed on schema-valid responses):

- False-corroboration rate (FCR): on dependent conditions, the fraction of responses whose
  `independent_sources` exceeds the gold family count. `null` counts as not overcounting.
- Confidence sensitivity: for supported/contradicted worlds, P(gold verdict | four_independent)
  minus P(gold verdict | single_origin), within world and arm.
- Confidence ceiling rate: for supported/contradicted cases, the fraction of responses whose
  gold-verdict probability is at least 0.99. It qualifies the interpretation of H2.

Secondary: absolute count error and exact-count accuracy on determinate cases; undercount rate on
independent conditions; abstention (`null`) rate on ambiguous cases; verdict accuracy;
multiclass Brier score; schema validity and coverage; latency and tokens.

Free-text answers are retained for a later blinded human rubric (explicit corroboration claims).
No human labels exist at freeze time; the paper must not describe this study as human-validated.

## Analysis

Unit of resampling: the micro-world. For each model, report each arm's estimates with 95%
percentile intervals from 10,000 whole-world bootstrap replicates (seed 20261027).

H3 confirmatory contrast, per model: FCR(echograph) - FCR(standard), paired by world. Holm
correction across the three models at family-wise alpha 0.05, using the paired bootstrap
two-sided p-value. H3 is supported for a model if its corrected interval/p-value favours echograph,
its verdict-accuracy difference interval lies above -0.05, and its undercount-rate difference
(echograph minus standard, independent conditions) interval lies below +0.10. If FCR in the standard
arm is zero for a model, H3 is reported as not testable for that model (floor), not as a failure. All other contrasts (reminder vs
standard, echograph vs reminder, oracle vs echograph) are reported as secondary, uncorrected.

Coverage rule: a model's H3 result is reported only if at least 90% of its planned test requests
are schema-valid in both compared arms; otherwise it is reported as inconclusive with coverage.

## Secondary: detector evaluation on the v1.4 test split

After the freeze, run `scripts/evaluate_v1_detection.py` once on the v1.4 test split with the
frozen validation settings (`artifacts/v1.4-dev/detection-settings-v1.4.json`) and write
`artifacts/v1.4-dev/detection-test-v1.4.json`. Outcomes and intervals are those of the v1.1 CPU
protocol (exclusive-family pair F1 and root-count MAE, whole-world bootstrap). Validation results
in `artifacts/v1.4-dev/detection-validation-v1.4.json` are development evidence only.

## Execution policy

- Requests rejected before generation (HTTP 429 rate limit or 503 unavailable) are retried after
  back-off, up to 6 times, and every attempt is logged. No completed response is ever re-requested,
  even if invalid.
- A request interrupted locally before any response was received (shutdown, crash, or Ctrl-C) is
  resent on resume. Its output was never observed, so resending cannot select among outcomes.
  Transport errors after sending (for example, timeouts) remain terminal.
- Pacing is configured per model to stay within free-tier limits.
- Run files are append-only JSONL. The plan file and all inputs are hash-checked before each run.

## Amendment before freeze (2026-10-27)

Made from validation-only development data (`artifacts/llm-study-v1.4/dev-r2/`), before any test
request. (1) Development showed over-correction: provenance guidance led some models to undercount
truly independent sources, so H3 adds a non-inferiority guard on the independent-condition
undercount rate (margin 0.10). (2) Gold-verdict probabilities were at or near 1.0 in both
single_origin and four_independent conditions, so the confidence ceiling rate is added to qualify
H2. (3) Standard-arm FCR was low for some models (floor), so H3 may be untestable for them; this is
stated in advance. Hypotheses, data, arms, models, and sample size are unchanged.

## Limitations stated in advance

Synthetic, gold-by-construction documents; provenance in v1.4 is often explicitly stated, so the
study measures use of visible provenance, not discovery of hidden provenance. Closed four-document
packets, not retrieval. Free-tier model aliases may change. No human validation at freeze.
