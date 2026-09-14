# AI diagnostic face-validity audit: EchoBench-Synthetic v1.2 candidate

**Status:** diagnostic review by an AI assistant, 2026-09-14. This is not a
human review, independent annotation, gold-blind audit, or evidence of
real-world validity. It must not be reported as any of those.

## Scope and method

One validation/supported case was selected for each provenance condition (11
cases). The public query and four claim-relevant documents were inspected for
whether a careful reviewer could infer the intended relationship from visible
text and metadata. Sampling was condition-stratified and therefore used gold
metadata to select examples; it was a targeted generator diagnostic, not a
blind measurement of annotator accuracy.

The verdict wording was clear in every inspected case. The finding below is
about provenance observability, not whether the stated intervention result is
supported.

## Findings

| Condition | Observable relation from public text? | Diagnostic finding |
| --- | --- | --- |
| `single_origin` | Yes | Explicit primary-report, briefing, digest, and trace language make the intended ancestry too easy. |
| `four_independent` | Yes | Separate team/sample identifiers directly reveal independence. |
| `verbatim_derivative` | No | Identical prose alone is not evidence of copying or one evidence root. A reviewer following the guide should answer unknown/abstain. |
| `attributed_paraphrase` | Yes | “According to the earlier investigation” makes ancestry explicit. |
| `unattributed_multihop` | No | Sequence words such as “subsequent” and “later” do not establish that an account reused an upstream source. The gold chain is not reliably observable. |
| `two_roots` | Yes | Named teams and cited team reports expose both source families. |
| `same_wording_independent` | Yes | Explicit independent-sample language resolves the intended counterexample. |
| `same_domain_independent` | Yes | Explicit own-sample language resolves the intended counterexample. |
| `shared_dataset` | Yes | Reuse of the same dataset ID is stated directly. |
| `shared_study_replication` | Yes | The original study/commentary relation and new sample IDs are stated directly. |
| `ambiguous_provenance` | Yes | The text appropriately instructs uncertainty and gives no provenance. |

## Consequences

The candidate is chronology-valid but is **not ready for a confirmatory
evaluation**. It mixes directly announced provenance relations with two gold
relations that are not justified by the public evidence. That can inflate
performance and makes a claim of source-family inference too strong.

Before any human packet or v1.2 held-out test is frozen:

1. Redesign `verbatim_derivative` to include observable source signals (for
   example, a dated upstream attribution, a URL/citation trace, or a document
   history) if same-family is to be the gold answer. Otherwise change its gold
   target to unknown/abstain.
2. Redesign `unattributed_multihop` as a true uncertainty condition, or supply
   observable but indirect provenance signals and have humans verify that they
   support the intended inference.
3. Reduce templated cues in every explicit condition: vary source language,
   topic framing, document length, claim wording, and how provenance is
   expressed. The model should not be able to solve the task by matching fixed
   phrases such as “separate sample” or “reuses dataset.”
4. Generate a new candidate after those changes, then run the blinded human
   review. Do not revise gold labels to agree with an AI reviewer after seeing
   model outputs.
