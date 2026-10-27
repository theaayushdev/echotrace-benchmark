# EchoTrace CPU study protocol (v1.1)

Status: pre-test freeze candidate. No held-out test metric may be computed or inspected until
`scripts/freeze_cpu_study_v1.py` succeeds. Any substantive post-freeze change requires v1.2.

## Scope and claims

This first paper is a controlled benchmark and simulation study, not an end-to-end language-model
agent study. It asks whether source-family structure can be inferred from visible documents and how
counting dependent documents as independent observations inflates confidence under explicit Bayesian
assumptions. It does not claim to infer truth, plagiarism, or causal web provenance.

## Research questions and hypotheses

- RQ1: How accurately do CPU-feasible methods recover source families in controlled cases?
- RQ2: How much confidence error results from using document count instead of source-family count?
- RQ3: Which visible signals drive EchoGraph-Classic's results?
- H1: EchoGraph-Classic has higher exclusive-family pair F1 and lower root-count MAE than URL,
  domain, bag-of-words, TF-IDF, and MiniLM clustering baselines.
- H2: EchoGraph-Classic yields lower posterior error than raw document counting in the prespecified
  confidence simulation.

## Data

- EchoBench-Synthetic v1.1: 240 worlds × 11 conditions = 2,640 cases and 12 documents per case.
- World-disjoint split: 150 train, 30 validation, and 60 held-out test worlds.
- Verdicts are balanced within every split. Gold provenance and splits are separated from public
  rows. Ambiguous-provenance cases have abstention gold and are excluded from determinate partition
  metrics rather than assigned a fabricated family count.
- No completed human audit or real-source evaluation is included. Gold labels are synthetic and
  defined by construction. Prepared audit materials are future work and must not be described as
  completed or as human validation.

## Methods

All methods run on CPU and receive the same four claim-relevant documents in the detection study:
URL/document count, all-one-family, domain grouping, lexical bag-of-words clustering, within-case
TF-IDF clustering, pinned `sentence-transformers/all-MiniLM-L6-v2` clustering, and
EchoGraph-Classic. Thresholds are selected on validation by lowest root-count MAE, then highest pair
F1, then proximity to 0.5. EchoGraph ablations remove links, attribution, lexical, numeric,
chronology, and domain features one group at a time.

The confidence study is a transparent sensitivity analysis. Priors are {0.10, 0.25, 0.50, 0.75,
0.90}; per-independent-family likelihood ratios are {1.5, 2, 3, 5}; supported and contradicted
claims update odds in opposite directions; insufficient cases use LR=1. These are assumptions, not
estimated real-world effect sizes.

## Outcomes and statistics

The detection co-primary outcomes are exclusive-family pair F1 and root-count MAE. Report results
by condition, including failures and ablations. The simulation outcomes are posterior absolute
error and excess absolute log odds relative to oracle family count. The micro-world is the sampling
unit. Report means, medians, and 95% percentile intervals from 10,000 whole-world bootstrap
replicates. Do not interpret validation results as held-out evidence.

## Pre-test gates

Before test evaluation:

1. Dataset structural validation and the documented coarse-metadata leakage probe pass.
2. The scope is frozen as synthetic and gold-by-construction, with no human-validation or
   real-world generalization claim.
3. Thresholds, the MiniLM model revision, benchmark, method code, metric code, simulation, and this
   protocol are SHA-256 frozen by `scripts/freeze_cpu_study_v1.py`.

The test commands must include the resulting freeze manifest and may run only once for v1.1:

```bash
.venv/bin/python scripts/evaluate_v1_detection.py --split test --include-semantic \
  --freeze-manifest artifacts/freeze-cpu-v1.1.json \
  --output artifacts/detection-test-v1.1.json
.venv/bin/python scripts/simulate_confidence_v1.py --split test --include-semantic \
  --freeze-manifest artifacts/freeze-cpu-v1.1.json \
  --output artifacts/confidence-simulation-test-v1.1.json
```

The paper is revised only after these commands and release checks complete.
