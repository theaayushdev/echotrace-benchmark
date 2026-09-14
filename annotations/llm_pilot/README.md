# Human review of exploratory LLM answers

No human judgments have been entered. The exporter creates a shuffled packet with provider,
model, arm, gold labels, and condition hidden. This reduces overt identity cues but the answer
itself may reveal the treatment or model style; do not claim perfect blinding.

Give a reviewer only this guide, packet.jsonl, and an independent copy of reviews.csv. Do not
give evaluator_mapping.json, model logs, or benchmark gold. Reviewers work separately and use
their own stable reviewer IDs. Reading the packet does not count as a completed review.

For each record, read the displayed documents and answer. Enter yes/no/unclear unless otherwise
specified:

- answer_substantive: does it contain an actual answer rather than a placeholder or boilerplate?
- verdict_supported_by_text: does its verdict follow from the displayed text? This is entailment,
  not proof that the underlying world claim is true.
- asserts_independent_corroboration: does the answer explicitly assert independent confirmation,
  distinct observations, or equivalent additional evidential strength? Merely mentioning several
  reports or consistent statements is not enough.
- provenance_assertion_warranted: yes/no/unclear/not_applicable. Is that assertion justified by
  visible provenance? Unknown lineage is not evidence of independence or copying.
- uncertainty_appropriate: does the answer acknowledge material uncertainty when making a
  provenance judgment? Do not require provenance discussion in an answer making no such claim;
  use not_applicable in that case.
- rationale and evidence_span: explain the decision and quote the smallest decisive passage.

Disagreements require discussion/adjudication documented separately, after independent records
are saved. A sole-author review must be called an author review. Model-generated judgments must
never be recorded as human judgments. No false-corroboration rate can be reported until this
annotation is actually completed and its denominator/uncertain-label policy is specified.
