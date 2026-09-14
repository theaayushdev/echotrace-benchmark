# EchoBench-Synthetic v1.3 candidate

This candidate was generated after the AI diagnostic audit of v1.2. It does
not replace v1.1 or v1.2, and no result from its test split exists.

Changes from v1.2:

- A verbatim republication now carries a visible upstream URL and explicit
  republication/attribution language, so same-family gold is auditable.
- Unattributed repeated reports now have an `unknown`/`abstain` gold target;
  they no longer assert an unobservable hidden lineage.
- Independent-observation language has several phrasings rather than one
  fixed surface form.

The release contains 3,960 cases in 360 world-disjoint micro-worlds, with
zero reversed lineage edges. It is still generated text with gold-by-
construction labels. It requires blinded human review and a new protocol
freeze before any held-out test evaluation.

```bash
python3 scripts/validate_benchmark_v1_2.py --data data/echobench_synthetic_v1_3
```
