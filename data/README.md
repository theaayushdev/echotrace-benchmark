# EchoBench-Synthetic

EchoBench-Synthetic tests whether a method can tell which documents share an underlying origin. A
*source family* is a group of documents that rely on the same observation, study, dataset, or
upstream report. It is not a label of truth, reliability, or plagiarism.

## v1.4 (used in the paper)

`echobench_synthetic_v1_4/` contains 3,960 cases: 360 fictional micro-worlds crossed with 11
provenance conditions. Each world has one quantitative claim with a verdict of `supported`,
`contradicted`, or `insufficient`. Each case has 12 documents: four relevant to the claim and eight
distractors.

| File | Contents |
|---|---|
| `public.jsonl` | What a model sees: `case_id`, `query`, and `documents` (each with `doc_id`, `url`, `title`, `text`, `published_at`, `domain`, `outbound_links`) |
| `gold.jsonl` | Evaluator-only labels: source families, lineage edges, root count, claim verdict, condition, split, prose style |
| `manifest.json` | Version, generation seed, and per-case split assignment |

- **Splits:** whole worlds are assigned to train, validation, and test (216/72/72), with verdicts
  balanced within each split.
- **Prose:** 36 topics and six prose styles. Two styles (forum and memo) appear only in held-out
  worlds.
- **Chronology:** every derivative document is dated after its sources.
- **Domains:** all documents use reserved `.example` domains and describe fictional entities.

Regenerate and validate with:

```bash
python scripts/generate_benchmark_v1_4.py
python scripts/validate_benchmark_v1_2.py --data data/echobench_synthetic_v1_4
```

## v1.1 (earlier release)

`echobench_synthetic_v1_{public,gold,manifest}` contain 2,640 cases from 240 worlds. This release
was evaluated once under a frozen protocol (`experiments/protocol_v1.md`,
`artifacts/freeze-cpu-v1.1.json`). A later audit found that 577 of 2,250 training lineage edges
were dated backwards, so its results should not be carried over to corrected data. It is kept
unchanged for reproducibility.

## Status

Labels follow from the generator and have not been checked by human annotators. The data contains
no real people, organizations, or web pages.
