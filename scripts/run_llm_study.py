#!/usr/bin/env python3
"""Freeze, prepare, execute, or analyze the free-tier v1.4 LLM study."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from echotrace.llm_study import analyze, execute, freeze, prepare


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("freeze", "prepare", "execute", "analyze"))
    parser.add_argument("--directory", default="artifacts/llm-study-v1.4/dev")
    parser.add_argument("--split", choices=("validation", "test"), default="validation")
    parser.add_argument("--model")
    parser.add_argument("--limit", type=int, help="maximum new requests in this invocation")
    args = parser.parse_args()
    if args.action == "freeze":
        print(json.dumps(freeze(ROOT), indent=2))
    elif args.action == "prepare":
        print(json.dumps(prepare(ROOT, ROOT / args.directory, args.split), indent=2))
    elif args.action == "execute":
        if not args.model:
            parser.error("execute requires --model")
        print(json.dumps(execute(ROOT, ROOT / args.directory, args.model, args.limit)))
    else:
        print(json.dumps(analyze(ROOT / args.directory), indent=2))


if __name__ == "__main__":
    main()
