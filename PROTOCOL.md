# Frozen evaluation protocol

This file is the preregistration checklist for EchoTrace. Timestamp the release commit or archive it
before any test-set model call.

## Hypotheses and primary outcomes

H1: ordinary research-agent confidence will fail to distinguish four independent roots from four
cross-domain derivatives of one root. H2: EchoGraph will reduce root-count MAE and false
corroboration rate (FCR) relative to standard retrieval. The two primary outcomes are root-count MAE
and FCR, aggregated first within matched micro-worlds.

The mitigation claim requires a paired 95% bootstrap interval favoring EchoGraph on the designated
primary comparison and no more than a 0.02 absolute decrease in verdict accuracy. Report both
primary outcomes even if only one supports the claim.

## Locked design

- 400 cases: 80 worlds times five conditions; world-disjoint 240/60/100 case splits.
- Naturalistic is the primary track; diagnostic is a secondary sensitivity analysis.
- Six model families: three commercial and three hosted open-weight families.
- Methods: standard, domain deduplication, lexical/semantic deduplication, MMR, EchoGraph, and a
  gold-family diagnostic upper bound.
- EchoGraph features and its threshold are trained/tuned using train and validation only.
- The threshold minimizes validation root-count MAE, breaking ties by family-pair F1 and then
  proximity to 0.5. The grid is 0.30 through 0.90 in increments of 0.05.
- Paired bootstrap resamples micro-worlds 10,000 times. Secondary randomization-test p-values use
  Holm correction. A model-family mixed-effects analysis is secondary.
- Invalid or failed responses are excluded from task-quality metrics and reported through coverage
  and error rate; cost includes every attempted response. A mitigation claim requires at least 95%
  coverage in both compared runs.
- Maximum aggregate API spend is the exact cap in the frozen experiment configuration.

## Release gates

1. Two independent reviews exist for every case; all disagreements have one adjudication row.
2. Dataset, model configuration, prompt-bearing source, and this protocol are hashed with `freeze`.
3. API model IDs are dated/fixed and nonzero prices are recorded.
4. Smoke artifacts are excluded from the paper exporter unless visibly marked as smoke.
5. The live-web audit is reported separately and cannot change the controlled primary endpoint.
