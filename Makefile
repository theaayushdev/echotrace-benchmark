.PHONY: test validate reproduce

test:
	.venv/bin/python -m pytest -q

validate:
	.venv/bin/python scripts/validate_benchmark_v1.py
	.venv/bin/python scripts/leakage_probe_v1.py

reproduce:
	.venv/bin/python scripts/evaluate_v1_detection.py --split validation --tune --include-semantic --output artifacts/detection-validation-v1.1.json
	.venv/bin/python scripts/simulate_confidence_v1.py --split validation --include-semantic --output artifacts/confidence-simulation-validation-v1.1.json
