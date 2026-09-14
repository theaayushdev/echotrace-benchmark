# EchoBench review guide

Reviewers work independently and must not see the other reviewer's answers. Add one row per case
with `round=independent`; use a stable pseudonymous reviewer ID. Enter `yes` or `no` for every
check and explain every `no` in `notes`.

- `claim_correct`: the gold claim, verdict, supporting IDs, and contradicting IDs match the texts.
- `lineage_correct`: every dependency edge and evidence family matches the document transformations.
- `condition_correct`: the case realizes its named condition and required root count.
- `no_label_leakage`: agent-visible text does not reveal hidden generation or lineage labels.
- `fluent`: documents are coherent enough to test the intended phenomenon.

When independent reviews disagree or contain a `no`, a third person inspects the case after it is
corrected and adds one `round=adjudication` row. The tooling upgrades a case to `double_reviewed`
only when two independent rows agree with all checks passing, or to `adjudicated` only when the
adjudication row passes every check. It never overwrites the original generated dataset.

Run:

```bash
python3 -m echotrace.cli reviews --data data/echobench.jsonl \
  --ledger annotations/reviews.csv
python3 -m echotrace.cli reviews --data data/echobench.jsonl \
  --ledger annotations/reviews.csv --apply-output data/echobench-reviewed.jsonl
```

