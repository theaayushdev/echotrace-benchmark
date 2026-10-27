# EchoTrace

Code, data, and raw model outputs for the paper
**EchoTrace: Do Language Models Mistake Repeated Reports for Independent Corroboration?**
(Ayush Dev, Nepal Engineering College). The paper is [`paper/main.pdf`](paper/main.pdf).

When several documents support a claim, a model may treat them as independent confirmation even
if they all derive from one observation. We call this *false corroboration*. EchoTrace measures it
on a synthetic benchmark in which the provenance of every document is known by construction.

## Findings

These are exploratory results from 12 validation worlds, not confirmatory tests.

- Without guidance, GPT-OSS-120B overcounts dependent sources in 0.47 of cases
  (95% CI [0.27, 0.67]), usually by reporting the number of documents. Qwen3.8-27B and
  Gemini 3.5 Flash-Lite rarely do.
- Guidance removes overcounting but over-corrects. GPT-OSS then undercounts genuinely independent
  sources, even when given the correct source families, and Gemini abstains on many determinate
  cases.
- No model's confidence in its verdict depends on how many independent sources support it.
- The EchoGraph detector reaches family-pair F1 0.920 [0.907, 0.933] in a single held-out run,
  but remains weak on shared-dataset provenance.

A confirmatory protocol for the held-out test worlds is frozen in this repository but has not yet
been run.

## Repository layout

| Path | Contents |
|---|---|
| `paper/` | Manuscript source, compiled PDF, and generated result macros |
| `data/` | EchoBench-Synthetic v1.4 (used in the paper) and v1.1; see [`data/README.md`](data/README.md) |
| `echotrace/` | Benchmark loading, EchoGraph detector, baselines, metrics, and the LLM study runner |
| `scripts/` | Benchmark generation and validation, detector evaluation, study execution, result export |
| `experiments/` | Study protocols (`llm_study_v1.4.md` is the language-model study) |
| `configs/` | Model and endpoint configuration for the language-model study |
| `artifacts/` | Frozen manifests, raw append-only model response logs, and analysis outputs |
| `tests/` | Unit tests |

## Reproducing the paper

Python 3.10 or later. Everything runs on CPU, and reproducing the reported numbers needs no API key.

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
make check          # unit tests and benchmark validation
make paper-numbers  # recompute every analysis and table value from the raw logs
make paper          # build paper/main.pdf (requires a LaTeX distribution)
```

`make paper-numbers` regenerates `artifacts/llm-study-v1.4/dev-r2/analysis.json` and
`paper/generated/*.tex` byte-for-byte from the committed response logs.

The detector evaluation additionally needs `pip install -e ".[cpu-research]"` for the MiniLM
baseline:

```bash
python scripts/evaluate_v1_detection.py --split validation \
  --public data/echobench_synthetic_v1_4/public.jsonl \
  --gold data/echobench_synthetic_v1_4/gold.jsonl \
  --manifest data/echobench_synthetic_v1_4/manifest.json \
  --settings artifacts/v1.4-dev/detection-settings-v1.4.json \
  --include-semantic --output detection-validation.json
```

## Re-running the language models

New model requests need your own free-tier keys in an untracked `.env` file at the repository
root:

```
GROQ_API_KEY=...
GEMINI_API_KEY=...
```

```bash
python scripts/run_llm_study.py prepare --directory artifacts/my-run --split validation
python scripts/run_llm_study.py execute --directory artifacts/my-run --model gptoss
python scripts/run_llm_study.py analyze --directory artifacts/my-run
```

Runs are append-only and resume safely after interruption. Groq's free tier allows about 200,000
tokens per model per day, which is about 190 study requests. Provider model aliases can change
over time.

## Study integrity

- `artifacts/llm-study-v1.4/freeze.json` records SHA-256 hashes of the protocol, code,
  configuration, data, and detector settings. Test-split runs refuse to start if any of them
  change.
- No language model has been sent a test-split case. The detector's held-out run was executed once,
  after the freeze.
- Raw response logs include every attempt, including rejected and invalid responses, and contain
  no credentials. Provider account identifiers in rate-limit error messages are replaced with
  `[REDACTED]`; no analysed field is affected.
- In the earlier v1.1 manifest (`artifacts/freeze-cpu-v1.1.json`), the hash for
  `scripts/evaluate_v1_detection.py` no longer matches. The script was later extended to accept
  newer benchmark versions. The v1.1 results were produced before that change, and all other v1.1
  hashes match.

## Limitations

The documents are synthetic and their provenance is usually visible through links and
attribution, so the study measures whether models *use* visible provenance, not whether they
discover hidden ancestry. Models receive closed four-document packets rather than retrieving
evidence. No result has been validated by human annotators. Source dependence is not a measure of
truth or quality and should not be used to judge authors or publishers.

## Citation

```bibtex
@misc{dev2026echotrace,
  author = {Dev, Ayush},
  title  = {{EchoTrace}: Do Language Models Mistake Repeated Reports for Independent Corroboration?},
  year   = {2026},
  url    = {https://github.com/theaayushdev/echotrace-benchmark}
}
```

## License

Code is licensed under Apache-2.0 ([`LICENSE`](LICENSE)). The generated benchmark data is
licensed under CC BY 4.0 ([`data/DATA_LICENSE.md`](data/DATA_LICENSE.md)).
