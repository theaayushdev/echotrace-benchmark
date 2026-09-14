#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from echotrace.io import load_cases, load_responses  # noqa: E402
from echotrace.metrics import aggregate_scores  # noqa: E402


def latex_escape(text: str) -> str:
    for old, new in (("_", r"\_"), ("%", r"\%"), ("&", r"\&"), ("#", r"\#")):
        text = text.replace(old, new)
    return text


def command_name(label: str) -> str:
    cleaned = re.sub(r"[^A-Za-z]", "", label.title())
    return cleaned or "Run"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=str(ROOT / "data" / "echobench.jsonl"))
    parser.add_argument("--run", action="append", required=True, help="LABEL=PATH")
    parser.add_argument("--allow-smoke", action="store_true")
    parser.add_argument("--output", default=str(ROOT / "paper" / "generated" / "results.tex"))
    args = parser.parse_args()
    cases = load_cases(args.data)
    rows: list[tuple[str, dict[str, object]]] = []
    smoke_found = False
    for specification in args.run:
        label, separator, path = specification.partition("=")
        if not separator:
            parser.error("--run must use LABEL=PATH")
        responses = load_responses(path)
        smoke = any(not response.trace or "provider_model" not in response.trace[0] for response in responses)
        smoke_found |= smoke
        rows.append((label, aggregate_scores(cases, responses)))
    if smoke_found and not args.allow_smoke:
        raise SystemExit("refusing to export mock/smoke results without --allow-smoke")
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    macro_lines = []
    for label, report in rows:
        metric = report["metrics"]
        prefix = command_name(label)
        macro_lines.extend(
            [
                rf"\expandafter\def\csname {prefix}RootMAE\endcsname{{{metric['root_count_mae']:.3f}}}",
                rf"\expandafter\def\csname {prefix}FCR\endcsname{{{metric['false_corroboration']:.3f}}}",
            ]
        )
    lines = [
        "% Generated from experiment artifacts. Do not edit by hand.",
        rf"\newcommand{{\ResultStatus}}{{{'SMOKE TEST---NOT A PAPER RESULT' if smoke_found else 'Frozen experiment results'}}}",
        *macro_lines,
        r"\begin{table*}[t]",
        r"\centering",
        r"\small",
        r"\begin{tabular}{lrrrrrrr}",
        r"\toprule",
        r"Run & Root MAE $\downarrow$ & FCR $\downarrow$ & ID $\uparrow$ & Cit. P. & Family F1 & Family R. & Cost (USD) \\",
        r"\midrule",
    ]
    for label, report in rows:
        metric = report["metrics"]
        lines.append(
            f"{latex_escape(label)} & {metric['root_count_mae']:.3f} & "
            f"{metric['false_corroboration']:.3f} & "
            f"{metric['independence_discrimination']:.3f} & "
            f"{metric['citation_precision']:.3f} & "
            f"{metric['evidence_family_pair_f1']:.3f} & "
            f"{metric['evidence_family_recall']:.3f} & {metric['cost_usd']:.2f} \\\\" 
        )
    lines.extend(
        [
            r"\bottomrule",
            r"\end{tabular}",
            r"\caption{Primary controlled-benchmark results. ID is independence discrimination; FCR is false corroboration rate.}",
            r"\label{tab:main-results}",
            r"\end{table*}",
        ]
    )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "runs": len(rows), "smoke": smoke_found}, indent=2))


if __name__ == "__main__":
    main()
