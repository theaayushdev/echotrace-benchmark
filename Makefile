.PHONY: check data-check paper-numbers paper

# Unit tests plus structural and leakage checks on the released benchmarks.
check:
	python -m pytest -q tests
	python scripts/validate_benchmark_v1_2.py --data data/echobench_synthetic_v1_4
	python scripts/validate_benchmark_v1.py

# Recompute every analysis and table value from the committed raw logs (no API calls).
paper-numbers:
	python scripts/run_llm_study.py analyze --directory artifacts/llm-study-v1.4/dev-r2
	python scripts/llm_count_breakdown.py
	python scripts/export_llm_study_results.py
	python scripts/export_v1_paper_results.py

paper:
	cd paper && latexmk -pdf main.tex
