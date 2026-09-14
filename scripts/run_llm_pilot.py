#!/usr/bin/env python3
"""Prepare, execute, or summarize the explicitly exploratory LLM pilot."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from echotrace.llm_pilot import execute, prepare, summarize


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "execute", "summarize"))
    parser.add_argument("--directory", default="artifacts/llm-pilot-v1.2")
    parser.add_argument("--provider", choices=("gemini", "groq", "openrouter"))
    args = parser.parse_args()
    if args.action == "prepare":
        print(json.dumps(prepare(ROOT, ROOT / args.directory), indent=2))
    elif args.action == "execute":
        if not args.provider:
            parser.error("execute requires --provider")
        execute(ROOT, ROOT / args.directory, args.provider)
    else:
        print(json.dumps(summarize(ROOT / args.directory), indent=2))


if __name__ == "__main__":
    main()
