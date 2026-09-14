# EchoTrace manuscript

Author: **Ayush Dev** (sole author), Nepal Engineering College, Bhaktapur, Nepal.

`main.pdf` is the current IEEE-style synthetic study manuscript. Numerical commands in
`generated/v1-results.tex` are exported directly from the frozen held-out JSON artifacts. The
older exploratory manuscript and assets remain preserved in `archive/`.

## Build

From the repository root, using the existing local Tectonic installation:

```bash
python3 scripts/export_v1_paper_results.py
.tools/tectonic/tectonic --keep-logs paper/main.tex
```

Experiments require Python, NumPy, CPU PyTorch, and sentence-transformers. No API key, paid model,
CUDA GPU, or external source corpus is needed. Tectonic downloads missing TeX packages on its
first build.

Alternatively, upload the manuscript source ZIP to Overleaf, select `main.tex`, and compile;
or run `latexmk -pdf main.tex` inside this directory with an IEEEtran-enabled TeX distribution.
Existing generated assets allow compiling without rerunning Python.

## Evidence status

The v1.1 CPU study is frozen and both one-shot held-out experiments are complete. It is a
synthetic, gold-by-construction component study with oracle relevant-document membership. It makes
no language-model-answer, human-validation, or live-web claim. The document states these limits in
the abstract, methods, limitations, and conclusion.

Legacy generated files are retained for compatibility but are not included. Do not replace the
held-out table with mock-agent or validation-only data.

IEEEtran provides the requested conference appearance. A specific venue has not been selected;
page limits, anonymous-review requirements, and final submission formatting remain venue-specific.

## LLM development and submission status

`llm-pilot.tex` is a separate exploratory report, with tables exported using
`scripts/export_llm_pilot_report.py`. It is not the final LLM study. Build with:

```bash
.tools/tectonic/tectonic --keep-logs paper/llm-pilot.tex
```

A training-only construction audit found reversed lineage timestamps in v1.1. `main.tex` now
discloses that limitation. Chronology-valid v1.2 and v1.3 candidate releases are available locally,
but neither has completed blinded human review, a frozen protocol, or held-out evaluation. The v1.3
candidate additionally changes unobservable repeated-report lineage to abstention and adds visible
republication links. Do not treat either manuscript as submission-ready yet. The older `EchoTrace_LaTeX_Source.zip` predates these revisions.
`EchoTrace_Development_Source_2026-09-13.zip` packages the revised main manuscript and separate
pilot report for local compilation or Overleaf; it remains a development snapshot.
