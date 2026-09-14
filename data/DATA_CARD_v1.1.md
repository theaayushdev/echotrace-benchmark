# EchoBench-Synthetic v1.1 data card

## Purpose

EchoBench-Synthetic v1.1 evaluates whether a method can group claim-relevant documents by shared
source family. A source family represents reliance on the same underlying report, study, dataset,
sample, or observation. It is not a truth, reliability, or plagiarism label.

## Composition

The release contains 2,640 cases: 240 fictional micro-worlds crossed with 11 provenance conditions.
Each case has 12 documents, four of which are relevant to one focal claim. Verdicts (`supported`,
`contradicted`, `insufficient`) are balanced within train, validation, and test. Worlds are assigned
to exactly one split: 150 train, 30 validation, and 60 test.

The conditions cover one and four origins, direct and multihop derivatives, attribution, two roots,
same wording/domain with independent observations, a shared dataset, study/replication structure,
and ambiguous provenance. Ambiguous cases deliberately have `unknown`/`abstain` pair labels and no
fabricated root count.

## Files and access

- `echobench_synthetic_v1_public.jsonl`: query and shuffled public documents only.
- `echobench_synthetic_v1_gold.jsonl`: evaluator-only verdict, relevance, pair relationships,
  lineage, family, root-count, condition, world, and split fields.
- `echobench_synthetic_v1_manifest.json`: version, seed, and case-to-world/split index.

Public rows must be the only input to a system under evaluation. The gold and manifest files are
joined only by trusted evaluation code.

## Construction and validation

All content is templated and fictional; `.example` domains prevent accidental representation as
real sources. Generation is deterministic with seed 20260911. Structural validation checks counts,
balance, separation, pair labels, and world leakage. A coarse nearest-centroid metadata probe is a
shortcut screen, not proof that no shortcut exists.

A deterministic 66-case training sample is reserved for a gold-blind construction/quality audit by
the sole author. This is not independent human validation. Any defect requires fixing the generator,
regenerating all derived files, and restarting that audit.

## Limitations and appropriate use

The prose and causal structures are synthetic and much simpler than real reporting ecosystems.
Family partitions are gold by construction, not discovered historical facts. Results therefore
measure controlled discrimination and sensitivity to predefined structures; they do not establish
open-web provenance performance or real-world prevalence. The separate 30-cluster real-source pilot
is author-curated, descriptive, and also not a prevalence sample.

Do not use this dataset to accuse a person or publisher of copying, rank source reliability, infer
claim truth, or train systems for high-stakes provenance decisions without additional validation.
