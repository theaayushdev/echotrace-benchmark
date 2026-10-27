"""Integrity checks for the one-shot held-out CPU study."""

from __future__ import annotations

import json
from pathlib import Path

from .io import sha256_file


def validate_cpu_freeze(path: str | Path, root: str | Path, run_name: str) -> dict:
    target = Path(path)
    document = json.loads(target.read_text(encoding="utf-8"))
    if not document.get("frozen") or document.get("version") != "1.1":
        raise RuntimeError("not a valid frozen EchoTrace CPU v1.1 manifest")
    if run_name in document.get("completed_test_runs", []):
        raise RuntimeError(f"held-out run {run_name!r} is already recorded as complete")
    root_path = Path(root)
    mismatches = [
        relative
        for relative, expected in document.get("sha256", {}).items()
        if not (root_path / relative).is_file() or sha256_file(root_path / relative) != expected
    ]
    if mismatches:
        raise RuntimeError(f"frozen file integrity failure: {mismatches}")
    return document


def mark_test_run_complete(path: str | Path, document: dict, run_name: str) -> None:
    completed = list(document.get("completed_test_runs", []))
    completed.append(run_name)
    document["completed_test_runs"] = completed
    Path(path).write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
