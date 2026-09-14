# Chronology-corrected development sample

This contains 33 development cases from three new world identifiers, generated with the same
v1.1 prose templates. It is not a new held-out test set or a final v1.2 benchmark.

The repair topologically traverses synthetic lineage and moves a derivative's publication date
forward when necessary so it follows every source by at least one day. It leaves text, links,
and gold families unchanged. There are zero reversed lineage edges in this sample. Date changes
may alter metadata distributions; leakage checks and human review remain necessary.

Files: public.jsonl contains queries/documents; gold.jsonl contains evaluator labels;
manifest.json records scope, seed, counts, and hashes. All cases have the train split.

Regeneration: scripts/generate_development_v1_2.py. The generator refuses to overwrite the existing
directory. These generated labels have not been human validated. The existing dataset license
applies to original synthetic text. The original v1.1 files were not changed.
