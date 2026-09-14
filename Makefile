.PHONY: check check-v1 generate smoke

check:
	python3 -m unittest discover -s tests -v
	python3 -m echotrace.cli validate --data data/echobench.jsonl
	python3 -m echotrace.cli reviews --data data/echobench.jsonl --ledger annotations/reviews.csv
	python3 -m echotrace.cli audit --data data/live_audit.csv

generate:
	python3 scripts/generate_benchmark.py

check-v1:
	.venv/bin/python -m pytest -q
	python3 scripts/validate_benchmark_v1.py
	python3 scripts/leakage_probe_v1.py

smoke:
	python3 -m echotrace.cli run --data data/echobench.jsonl --split test --agent mock \
		--method standard --output artifacts/runs/mock-standard.jsonl
	python3 -m echotrace.cli run --data data/echobench.jsonl --split test --agent mock \
		--method echograph --output artifacts/runs/mock-echograph.jsonl
	python3 scripts/analyze_runs.py --baseline artifacts/runs/mock-standard.jsonl \
		--candidate artifacts/runs/mock-echograph.jsonl --output artifacts/smoke-analysis.json


.PHONY: paper paper-analysis
paper-analysis:
	python3 scripts/export_v1_paper_results.py

paper:
	.tools/tectonic/tectonic --keep-logs paper/main.tex
