# EchoBench v1.1 sole-author audit

This audit checks benchmark construction and readability. It is performed by Ayush Dev, the sole
author, and must be reported as a **gold-blind author audit**, never as independent human validation.

The 66-case sample contains two training cases from each of the 33 condition-by-verdict cells. The
packet exposes the focal claim and public documents but hides condition, verdict, families, world,
and split. For each case, identify the four claim-relevant documents, assign the observed verdict,
and label their six pairs. Similar wording alone is not evidence of copying; use `unknown` and
`abstain` when the visible record is insufficient.

Run the resumable terminal form:

```bash
python3 scripts/run_author_audit_v1.py
```

It appends a case only after all six pair judgments are entered, so Ctrl+C is safe between cases.
Check the release gate with:

```bash
python3 -m echotrace.cli author-audit \
  --gold data/echobench_synthetic_v1_gold.jsonl \
  --sample annotations/v1/author_audit_sample.json \
  --ledger annotations/v1/author_audit.csv
```

Allowed dependency bases (semicolon-separated if multiple) are `upstream_document`,
`primary_study`, `dataset`, `measurement_event`, `sample_cohort`, `editorial_organizational`,
`distinct_observation`, and `unknown`. If the audit exposes a defect, fix the generator, regenerate,
resample, and restart the audit; do not silently edit gold to match the judgment.
