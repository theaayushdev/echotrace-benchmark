# Confirmatory LLM extension: design draft

Status: NOT FROZEN. Do not use this document to authorize final test access or claim preregistration.
The feasibility pilot and post-freeze construction audit have exposed issues that must be resolved
before determining the final evaluation sample. This file specifies the proposed design for review.

## Research contribution to test

Can provenance inferred from visible document evidence reduce unsupported assertions of independent
corroboration in generated answers, beyond a reminder or similarity-based grouping, while preserving
correct use of genuinely independent evidence? This differs from assuming known provenance in an
aggregation equation. It does not assume EchoTrace will improve outcomes.

## Dataset gates

- Complete a chronology-corrected release. Validate DAGs, source-before-derivative timestamps,
  links, family membership, verdict labels, pair actions, and public/gold separation.
- Human-review development examples for observability, coherent prose, and meaning of partial
  overlap. Cases whose latent lineage cannot be inferred from displayed content must support
  abstention rather than a forced, unobservable family assignment.
- Introduce new prose templates and topic holdouts. Keep entire matched worlds and shared text
  templates in one split. A corrected copy of exposed v1.1 test cases is development evidence.
- Preserve document count and evidence content across treatment arms. Distinguish source-family
  membership from reliability and from the independent information contributed by an analysis.
- Counterfactual document conditions: repeated single origin, multiple independent roots, same
  wording with independent observations, paraphrased common source, shared dataset, replication,
  mixed/partial overlap, and indeterminate provenance. Vary report multiplicity in a separate
  controlled comparison; measure and report token-length differences rather than hiding them.
- Repairing dates alone is not sufficient. Screen for ID, date, title, URL, wording, topic, and
  template shortcuts; archive both successful checks and residual weaknesses.

## Two independent tasks

1. Ordinary answering: ask for a concise evidence-based answer, verdict, evidence-verdict
   probabilities, and citations. Do not ask about roots/families in the standard condition.
   Human reviewers assess explicit independence/corroboration assertions using the displayed
   sources. An entailment-correct verdict can coexist with an unsupported provenance assertion.
2. Provenance diagnostic: a separate stateless call asks for all relevant document-pair actions
   (same family, distinct families, partial overlap, abstain), rationale spans, and a partition
   only where an exclusive partition is defensible. Never feed the diagnostic answer into the
   ordinary-answer task or call the diagnostic condition naturalistic.

The first experiment uses oracle relevant-document membership to isolate the evidence-use
component. Retrieval from a larger corpus is a separate extension and must not be claimed from
four preselected documents. An LLM answering a closed packet is not a full autonomous web agent.

## Arms and model selection

Ordinary answer arms: standard; dependence reminder; same reminder plus semantic grouping;
same reminder plus EchoGraph grouping; same reminder plus oracle grouping as a diagnostic control.
An oracle grouping is not guaranteed to produce the best answer; measure its result.
Preserve all document text and order across arms, with matched output caps and recorded metadata
overhead. Avoid attributing a benefit to grouping if it instead comes from different instructions.

Select three actual model families based on successful development access, stable availability,
and quotas, before final collection. Pin immutable versions where offered; otherwise record the
requested/returned identifier, serving provider, fingerprint, timestamp, and alias limitations.
An unavailable model is missing data, not permission to silently pool another version.

## Proposed co-primary outcomes

- Ordinary answers: fraction of all assessable answers containing an unsupported assertion of
  independent corroboration, defined by blinded human labels. Also report assertion frequency,
  conditional error among assertions, and the number of unassessable/unclear outputs. Abstaining
  from every answer must not appear to solve the task: track verdict accuracy and substantive
  answer coverage, plus preservation on truly independent-source cases.
- Diagnostics: source-family overcount error on human-assessable determinate cases, alongside
  absolute root-count error, pair F1, coverage, abstention on indeterminate cases, and partial-overlap
  performance. A model that abstains on everything must have zero coverage, not perfect accuracy.

Secondary outcomes: evidence-verdict Brier score, citation validity/support, unsupported certainty,
metadata token overhead, latency, and repeated-run variability. Evidence-verdict probability and
factual-truth probability are different quantities. A decrease in confidence is not by itself a win.

## Decisions needed before freezing

Specify a smallest meaningful improvement and tolerable loss on independent-evidence cases with
the research supervisor/reviewer. Use a larger development sample to estimate world-level variance;
the current three-world pilot cannot provide a reliable sample-size estimate. Determine the number
of worlds, repeats, human-reviewed answers, and API requests from that analysis and quota inventory.
Do not adopt an arbitrary 300-case sample merely because it fits an API allowance.

Predefine matched-world contrasts and 95% whole-world bootstrap intervals; use multiplicity
correction across the fixed primary comparisons. Resample complete worlds, not individual calls
or matched variants. Fix repeated-run settings and document-order randomization before collection.
Report all model/arm cells, failures, truncations, parsing errors, human agreement, and adjudication.
Specify exclusion and unclear-label sensitivity analyses before test labels/results are examined.

## Release gates

Human annotations must be independently collected, with reviewer consent and accurate attribution.
The author can perform a separate review, but cannot count as two independent reviewers. An
author-curated real-source pilot is descriptive and must not be advertised as representative.

Finalize code, prompts, dataset, model configuration, analysis, and human rubric; run offline
integrity tests; timestamp/archive the protocol; then execute the held-out matrix once under a
documented resume policy. After evaluation, write the paper around measured results, including
negative findings and remaining construct limitations. Venue formatting follows venue selection.
