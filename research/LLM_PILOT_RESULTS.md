# EchoTrace LLM feasibility pilot

Exploratory training-only results. These are not held-out results, human validation, or evidence of publication readiness.

## Coverage

| Run / provider | Requested model | Planned | Attempted | Schema-valid | Complete three-arm cases |
|---|---|---:|---:|---:|---:|
| llm-pilot-v1.2 / gemini | gemini-3.8-flash | 36 | 2 | 0 | 0 |
| llm-pilot-v1.2 / groq | qwen/qwen3.8-27b | 36 | 36 | 36 | 12 |
| llm-pilot-v1.2 / openrouter | nvidia/nemotron-3-super-120b-a12b:free | 36 | 36 | 35 | 11 |
| llm-pilot-v1.2-gemini37 / gemini | gemini-3.7-flash | 36 | 1 | 0 | 0 |

## Evidence-verdict outcomes

Schema validity is not answer quality. All denominators below include only schema-valid responses.

| Run / provider | Arm | N | Verdict accuracy | Multiclass Brier |
|---|---|---:|---:|---:|
| llm-pilot-v1.2 / groq | standard | 12 | 0.917 | 0.1671 |
| llm-pilot-v1.2 / groq | instruction | 12 | 0.750 | 0.4854 |
| llm-pilot-v1.2 / groq | echograph | 12 | 0.833 | 0.3025 |
| llm-pilot-v1.2 / openrouter | standard | 12 | 0.750 | 0.5000 |
| llm-pilot-v1.2 / openrouter | instruction | 11 | 0.727 | 0.5455 |
| llm-pilot-v1.2 / openrouter | echograph | 12 | 0.833 | 0.3067 |

## Mechanical output-quality flags

Flags were defined after seeing pilot outputs; they are descriptive checks, not preregistered outcomes.

- Literal answer-placeholder copies: 1.
- Answers exceeding the requested 100-word length: 0.
- No independent human labels have been entered by this exporter.

## Interpretation

Only three training worlds were sampled. The detector was trained on these worlds. Correctly classifying directly stated evidence does not establish source-family reasoning. Probabilities concern evidence entailment, not truth. Brier scores here are not a measurement of real-world truth calibration. No significance tests or generalization intervals are reported.

The original Gemini model returned availability errors. Its alternative is a separately identified run, not pooled as the same model. All raw failures remain in the JSONL logs.

Source-family counts and human-rated false-corroboration rates are NOT measured by this pilot. The next experiment needs separate provenance diagnostics, human answer review, and fresh holdouts.
