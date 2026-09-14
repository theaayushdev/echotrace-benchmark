# Author-curated real-source pilot protocol

This descriptive pilot checks whether EchoTrace's taxonomy can be applied to real science
communication. It is performed by Ayush Dev and is not independent validation or a prevalence
sample. Collect 30 source clusters: 20 with visible, determinate provenance and 10 deliberately
ambiguous clusters. Begin each cluster with a narrowly worded factual claim.

For every inspected page, record its canonical URL, access/publication timestamps, SHA-256 of the
inspected content, any direct upstream URL, relationship, observability, author ID, verification,
smallest supporting evidence span, and notes. Store hashes and short spans rather than copyrighted
article bodies. Respect access controls and site terms. Do not infer copying from similar wording.

Validate work in progress with:

```bash
python3 -m echotrace.cli audit --data data/live_audit.csv
```

The release gate adds `--require-complete`; it requires the 20/10 balance, a root in determinate
clusters, an `unknown` relationship in ambiguous clusters, evidence spans, and personal verification
for every row. URLs or labels must never be invented merely to fill the quota.

`live_audit_cluster_plan.csv` supplies the prespecified 20/10 slots and selection rules. Change a
topic family only before collecting that slot, record the change in notes, and never choose a case
because it makes a method look successful. The actual observations belong in `live_audit.csv`.
