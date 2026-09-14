# EchoBench-Synthetic v1.2 candidate

This is a new, separate synthetic candidate release. It does not modify or
replace frozen v1.1 files or claims.

It contains 3,960 cases in 360 world-disjoint micro-worlds: 216 training, 72
validation, and 72 test worlds. Each of the 11 provenance conditions appears
once per world; verdicts are balanced within each split. During generation,
every derivative date is moved forward as necessary to follow each upstream
lineage source. The manifest records 1,462 changed document dates and zero
reversed lineage edges.

Validate it with:

```bash
python3 scripts/validate_benchmark_v1_2.py
```

Status: candidate only. The prose templates remain inherited from v1.1, labels
are gold-by-construction, no human review is complete, and no confirmatory
protocol or held-out evaluation has been frozen for this release.
