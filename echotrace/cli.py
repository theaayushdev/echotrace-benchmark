from __future__ import annotations

import argparse
import json
from pathlib import Path

from .agents import LocalModelConfig, LocalTransformersAgent, MockResearchAgent, OpenAICompatibleAgent
from .agents.api import ModelConfig
from .benchmark import validate_dataset
from .benchmark_v1 import validate_v1_dataset
from .io import load_cases, load_responses, load_v1_cases
from .live_audit import validate_live_audit
from .metrics import aggregate_scores
from .review import apply_reviews, review_report
from .review_v1 import author_audit_report, review_v1_report
from .runner import evaluate_echo_graph, run_experiment, write_freeze_manifest


def _print(value: object) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def _add_data_source_arguments(command: argparse.ArgumentParser) -> None:
    command.add_argument("--data", help="legacy combined benchmark JSONL")
    command.add_argument("--v1-public", help="v1 public JSONL")
    command.add_argument("--v1-gold", help="v1 evaluator-only gold JSONL")
    command.add_argument("--v1-manifest", help="v1 split manifest JSON")


def _load_selected_cases(args: argparse.Namespace, parser: argparse.ArgumentParser):
    v1 = (args.v1_public, args.v1_gold, args.v1_manifest)
    if any(v1):
        if not all(v1) or args.data:
            parser.error("use either --data or all of --v1-public, --v1-gold, and --v1-manifest")
        return load_v1_cases(*v1)
    if not args.data:
        parser.error("a benchmark data source is required")
    return load_cases(args.data)


def main() -> None:
    parser = argparse.ArgumentParser(prog="echotrace")
    commands = parser.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate")
    _add_data_source_arguments(validate)

    run = commands.add_parser("run")
    _add_data_source_arguments(run)
    run.add_argument("--split", choices=("train", "validation", "test"), default="test")
    run.add_argument("--agent", choices=("mock", "api", "local"), default="mock")
    run.add_argument(
        "--method",
        choices=("standard", "domain_dedup", "embedding_dedup", "mmr", "echograph", "gold_graph"),
        default="standard",
    )
    run.add_argument("--track", choices=("naturalistic", "diagnostic"), default="naturalistic")
    run.add_argument("--output", required=True)
    run.add_argument("--model-config")
    run.add_argument("--model-id")
    run.add_argument("--model-revision")
    run.add_argument("--budget-usd", type=float, default=100.0)
    run.add_argument("--threshold", type=float, default=0.60)

    score = commands.add_parser("score")
    _add_data_source_arguments(score)
    score.add_argument("--responses", required=True)

    freeze = commands.add_parser("freeze")
    _add_data_source_arguments(freeze)
    freeze.add_argument("--config", action="append", default=[])
    freeze.add_argument("--output", default="artifacts/freeze-manifest.json")

    reviews = commands.add_parser("reviews")
    _add_data_source_arguments(reviews)
    reviews.add_argument("--ledger", required=True)
    reviews.add_argument("--apply-output")

    v1_reviews = commands.add_parser("v1-review")
    v1_reviews.add_argument("--public", required=True)
    v1_reviews.add_argument("--sample", required=True)
    v1_reviews.add_argument("--ledger", required=True)

    author_audit = commands.add_parser("author-audit")
    author_audit.add_argument("--gold", required=True)
    author_audit.add_argument("--sample", required=True)
    author_audit.add_argument("--ledger", required=True)

    audit = commands.add_parser("audit")
    audit.add_argument("--data", required=True)
    audit.add_argument("--require-complete", action="store_true")

    graph_score = commands.add_parser("graph-score")
    _add_data_source_arguments(graph_score)
    graph_score.add_argument("--split", choices=("validation", "test"), default="validation")
    graph_score.add_argument("--threshold", type=float, default=0.60)

    args = parser.parse_args()
    if args.command == "validate":
        if any((args.v1_public, args.v1_gold, args.v1_manifest)):
            if not all((args.v1_public, args.v1_gold, args.v1_manifest)) or args.data:
                parser.error("use either --data or all of --v1-public, --v1-gold, and --v1-manifest")
            report = validate_v1_dataset(args.v1_public, args.v1_gold, args.v1_manifest)
        elif args.data:
            report = validate_dataset(args.data)
        else:
            parser.error("a benchmark data source is required")
        _print(report)
        raise SystemExit(0 if report["valid"] else 1)
    if args.command == "score":
        cases = _load_selected_cases(args, parser)
        responses = load_responses(args.responses)
        _print(aggregate_scores(cases, responses))
        return
    if args.command == "freeze":
        files = [args.data] if args.data else [args.v1_public, args.v1_gold, args.v1_manifest]
        if not all(files):
            parser.error("a benchmark data source is required")
        _print(write_freeze_manifest(args.output, files[0], [*args.config, *files[1:]]))
        return
    if args.command == "reviews":
        if any((args.v1_public, args.v1_gold, args.v1_manifest)):
            parser.error("v1 uses the pair-level review workflow; use the v1-review command")
        if not args.data:
            parser.error("--data is required for legacy reviews")
        report = (
            apply_reviews(args.data, args.ledger, args.apply_output)
            if args.apply_output
            else review_report(args.data, args.ledger)
        )
        _print({key: value for key, value in report.items() if key != "statuses"})
        raise SystemExit(0 if report["valid"] else 1)
    if args.command == "v1-review":
        report = review_v1_report(args.public, args.sample, args.ledger)
        _print(report)
        raise SystemExit(0 if report["valid"] else 1)
    if args.command == "author-audit":
        report = author_audit_report(args.gold, args.sample, args.ledger)
        _print(report)
        raise SystemExit(0 if report["release_ready"] else 1)
    if args.command == "audit":
        report = validate_live_audit(args.data, args.require_complete)
        _print(report)
        raise SystemExit(0 if report["valid"] else 1)
    if args.command == "graph-score":
        _print(evaluate_echo_graph(_load_selected_cases(args, parser), args.split, args.threshold))
        return
    all_cases = _load_selected_cases(args, parser)
    cases = [case for case in all_cases if case.split == args.split]
    if args.agent == "mock":
        agent = MockResearchAgent()
    elif args.agent == "api":
        if not args.model_config or not args.model_id:
            parser.error("API agent requires --model-config and --model-id")
        agent = OpenAICompatibleAgent(ModelConfig.from_file(args.model_config, args.model_id))
    else:
        if not args.model_revision:
            parser.error("local agent requires --model-revision (a pinned model commit hash)")
        agent = LocalTransformersAgent(LocalModelConfig(model_id=args.model_id or "Qwen/Qwen2.5-7B-Instruct", revision=args.model_revision))
    summary = run_experiment(
        cases=cases,
        agent=agent,
        output_path=args.output,
        method=args.method,
        track=args.track,
        budget_usd=args.budget_usd,
        threshold=args.threshold,
        training_cases=all_cases,
    )
    _print(summary)


if __name__ == "__main__":
    main()
