# EchoTrace research questions v1

## Primary research question

How accurately can CPU-feasible methods recover source-family structure, and how much confidence
inflation follows when dependent documents are counted as independent observations?

## Research questions

**RQ1 — Detection.** Can a system identify source-family relationships among evidence documents,
including partial overlap, and abstain when the visible record is insufficient?

**RQ2 — Impact.** Under prespecified Bayesian priors and likelihood ratios, how much error follows
from using document count rather than source-family count?

**RQ3 — Mechanism.** Which link, attribution, lexical, numeric, chronology, and domain signals drive
EchoGraph-Classic's source-family inference performance?

RQ1–RQ3 are the prespecified questions for the final frozen evaluation. Real-source generalization
and human validation are explicitly outside the first paper's completed evidence.

## Operational vocabulary

EchoTrace uses **source-family dependence**, defined as whether multiple documents rely on the same
underlying observation, study, dataset, event, measurement, or upstream report. This is narrower
than true epistemic independence. Dependence is not reliability, truth, or evidence quality.

The primary annotation unit is a pair of evidence spans for one focal claim. Each pair has:

| Field | Values |
|---|---|
| Relationship | independent; direct derivative; indirect derivative; common dependency; partial overlap; unrelated; unknown |
| Dependency basis | upstream document; primary study; dataset; measurement/event; sample/cohort; editorial/organizational (multi-label) |
| Observability | explicit; inferable; indeterminate |
| Evaluation action | same family; distinct families; partial overlap; abstain |

The released system must communicate uncertainty and must not accuse a source of copying when the
available evidence supports only an unknown or partial-overlap label.

## Intended contribution

The first paper contributes a controlled benchmark, an interpretable CPU source-family inference
baseline (EchoGraph-Classic), ablations, and a transparent confidence-inflation simulation. It does
not claim an end-to-end assistant evaluation, solve open-web provenance discovery, or infer truth
from source relationships.
