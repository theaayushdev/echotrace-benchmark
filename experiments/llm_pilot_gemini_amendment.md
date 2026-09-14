# Gemini availability amendment, 2026-09-13

The original Gemini 3.8 Flash pilot returned HTTP 503 (high demand) on its first two attempted
requests and produced no answers. Retain those failures in the original log. Before any outputs
from the replacement, prepare the same training-only 12-case/three-arm pilot with Gemini 3.7
Flash, whose current official pricing page also lists a free input/output tier:
https://ai.google.dev/gemini-api/docs/pricing .

This is a different requested model, not an interchangeable retry or a hidden substitution.
Record it under artifacts/llm-pilot-v1.2-gemini37. The original plan remains unchanged. Permit
36 generation attempts on the alternative, for a maximum of 38 total Gemini attempts including
the two unsuccessful availability probes. No further automatic model substitutions follow.
All other original protocol provisions apply. The other providers are not rerun.

Rationale: service availability, determined before receiving any Gemini behavioral results.
This amendment is local and exploratory; it is not external preregistration.
