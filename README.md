# EchoTrace

EchoTrace is a small, reproducible study of a simple research problem: several articles can repeat
one observation, but still look like independent evidence. This repository contains the code and
synthetic benchmark used to measure that problem.

## What is included

- EchoBench-Synthetic v1.1: 2,640 fictional cases in 240 world-disjoint micro-worlds.
- EchoGraph: an interpretable CPU source-family grouping baseline.
- URL, domain, lexical, TF-IDF, and MiniLM comparison baselines.
- Feature ablations and a Bayesian confidence-inflation simulation.
- Held-out results, validation results, and reproducibility metadata.
- Unit tests and the frozen experiment protocol.

The benchmark is synthetic and gold-by-construction. It must not be used to infer truth, source
reliability, plagiarism, or misconduct. The repository does not include the research paper or any
LaTeX source.

## Quick start

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev,cpu-research]"
.venv/bin/python -m pytest -q
```

Validate the released benchmark:

```bash
.venv/bin/python scripts/validate_benchmark_v1.py
.venv/bin/python scripts/leakage_probe_v1.py
```

Re-run the CPU validation study:

```bash
.venv/bin/python scripts/evaluate_v1_detection.py \
  --split validation --tune --include-semantic \
  --output artifacts/detection-validation-v1.1.json
.venv/bin/python scripts/simulate_confidence_v1.py \
  --split validation --include-semantic \
  --output artifacts/confidence-simulation-validation-v1.1.json
```

The released held-out results are already included in `artifacts/`. Held-out evaluation was run
once under the recorded freeze manifest.

## Data layout

`data/echobench_synthetic_v1_public.jsonl` is the agent-visible benchmark projection.
`data/echobench_synthetic_v1_gold.jsonl` contains evaluator-only labels and provenance.
`data/echobench_synthetic_v1_manifest.json` contains the version, seed, and split assignments.
See `data/DATA_CARD_v1.1.md` for intended use and limitations.

## Reproducibility

The exact method settings, model revision, results, and SHA-256 freeze record are in `artifacts/`.
The semantic baseline uses `sentence-transformers/all-MiniLM-L6-v2` with a pinned revision. The
study runs on CPU and does not require CUDA, a paid API, or external source pages.

## License and citation

The source code is released under the Apache License 2.0. Synthetic benchmark data and its terms
are described in `data/DATA_LICENSE.md`. If you use this repository, please cite the eventual
EchoTrace paper when it is publicly released.

## Author

Ayush Dev  
Nepal Engineering College  
Bhaktapur, Nepal
