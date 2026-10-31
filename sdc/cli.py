"""Command line.

  python -m sdc run    --prover oracle --out results/oracle.jsonl
  python -m sdc run    --prover api --model llama-3.3-70b-versatile --out results/llama70b.jsonl
  python -m sdc eval   results/llama70b.jsonl
  python -m sdc report results/llama70b.jsonl -o results/llama70b.html
  python -m sdc ask    "Is Python's sort stable, and is heapq a max-heap?"
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .claims import load_claims
from .evaluate import load_results, markdown_summary, metrics
from .report import write_report

DEFAULT_CLAIMS = Path(__file__).resolve().parent.parent / "data" / "claims_seed.jsonl"


def _prover_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--prover", default="api",
                   choices=["api", "hf", "oracle", "hollow-plain", "hollow-disguised"])
    p.add_argument("--model", help="model name (api) or HF repo id (hf)")
    p.add_argument("--api-base", help="OpenAI-compatible base URL (or env SDC_API_BASE)")
    p.add_argument("--api-key", help="API key (or env SDC_API_KEY)")
    p.add_argument("--temperature", type=float, default=0.2)
    p.add_argument("--no-4bit", action="store_true", help="hf: load in full precision")
    p.add_argument("--timeout", type=int, default=30, help="seconds per PoC")


def _make(args):
    from .provers import make_prover
    return make_prover(args.prover, model=args.model, api_base=args.api_base,
                       api_key=args.api_key, temperature=args.temperature,
                       load_in_4bit=not args.no_4bit)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="sdc", description="Show, Don't Cite")
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="run the benchmark with a prover")
    _prover_args(r)
    r.add_argument("--claims", default=str(DEFAULT_CLAIMS))
    r.add_argument("--ids", nargs="*")
    r.add_argument("--limit", type=int)
    r.add_argument("--out", required=True)
    r.add_argument("--no-resume", action="store_true")

    e = sub.add_parser("eval", help="print metrics for a results file")
    e.add_argument("results", nargs="+")
    e.add_argument("--json", action="store_true")

    rep = sub.add_parser("report", help="write an HTML report")
    rep.add_argument("results")
    rep.add_argument("-o", "--out", required=True)
    rep.add_argument("--title", default="Show, Don't Cite")

    a = sub.add_parser("ask", help="answer a question with negation-checked PoCs")
    a.add_argument("question")
    _prover_args(a)
    a.add_argument("--report", help="also write an HTML report here")

    args = ap.parse_args(argv)

    if args.cmd == "run":
        from .pipeline import run
        claims = load_claims(args.claims, ids=args.ids, limit=args.limit)
        prover = _make(args)
        if args.no_resume and Path(args.out).exists():
            Path(args.out).unlink()
        results = run(claims, prover, args.out, timeout=args.timeout)
        print()
        print(markdown_summary(metrics(results), title=prover.name))

    elif args.cmd == "eval":
        for path in args.results:
            m = metrics(load_results(path))
            print(json.dumps(m, indent=2) if args.json else markdown_summary(m, title=path))
            print()

    elif args.cmd == "report":
        res = load_results(args.results)
        print(write_report(res, args.out, args.title))

    elif args.cmd == "ask":
        if args.prover not in ("api", "hf"):
            sys.exit("ask needs a language-model prover: --prover api or --prover hf")
        from .ask import ask, format_answer
        prover = _make(args)
        answer, results = ask(prover.backend, args.question, timeout=args.timeout)
        print(format_answer(args.question, answer, results))
        if args.report:
            print(write_report(results, args.report, title=args.question))


if __name__ == "__main__":
    main()
