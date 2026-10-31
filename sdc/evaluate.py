"""Metrics for a results file.

The headline comparison is the single-PoC baseline (run one PoC for the claim,
trust a PASS) against the negation check (also run a PoC for the negation;
trust only PASS/FAIL). The question it answers: how often would you have
accepted a FALSE claim with "proof attached"?
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from .verdict import ABSTAIN, ALL_VERDICTS, DEMONSTRATED, REFUTED, VACUOUS


def load_results(path: str | Path) -> list[dict]:
    return [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]


def _rate(num: int, den: int) -> float | None:
    return round(num / den, 4) if den else None


def metrics(results: list[dict]) -> dict:
    true_ = [r for r in results if r["label"] == "true"]
    false_ = [r for r in results if r["label"] == "false"]
    untestable = [r for r in results if r["label"] == "untestable"]
    testable = true_ + false_

    def correct(r, key):
        return (r["label"] == "true" and r[key] == DEMONSTRATED) or \
               (r["label"] == "false" and r[key] == REFUTED)

    def decided(r, key):
        return r[key] in (DEMONSTRATED, REFUTED)

    m = {"n_claims": len(results), "n_true": len(true_), "n_false": len(false_),
         "n_untestable": len(untestable),
         "verdicts": {v: Counter(r["verdict"] for r in results).get(v, 0) for v in ALL_VERDICTS}}

    for key, tag in (("single_poc_verdict", "single_poc"), ("verdict", "negation_checked")):
        n_dec = sum(decided(r, key) for r in testable)
        m[tag] = {
            # Of FALSE claims, how many were accepted as proven? (lower is better)
            "false_acceptance_rate": _rate(sum(r[key] == DEMONSTRATED for r in false_), len(false_)),
            # Of TRUE claims, how many were accepted as proven? (higher is better)
            "true_acceptance_rate": _rate(sum(r[key] == DEMONSTRATED for r in true_), len(true_)),
            # Of testable claims, how many got a definite verdict?
            "coverage": _rate(n_dec, len(testable)),
            # Of definite verdicts, how many were right?
            "precision_of_decided": _rate(sum(correct(r, key) for r in testable), n_dec),
            "accuracy_all_testable": _rate(sum(correct(r, key) for r in testable), len(testable)),
        }

    m["vacuous_rate_testable"] = _rate(sum(r["verdict"] == VACUOUS for r in testable), len(testable))
    m["abstain_rate_untestable"] = _rate(sum(r["verdict"] == ABSTAIN for r in untestable), len(untestable))
    m["abstain_rate_testable"] = _rate(sum(r["verdict"] == ABSTAIN for r in testable), len(testable))

    vac = [r for r in results if r["verdict"] == VACUOUS]
    linted = [r for r in vac if r["claim_poc"]["lint"] or r["negation_poc"]["lint"]]
    m["vacuous_caught_by_static_lint"] = _rate(len(linted), len(vac))
    m["lint_flags"] = dict(Counter(f for r in results for s in ("claim_poc", "negation_poc")
                                   for f in r[s]["lint"]))
    m["by_category"] = {}
    for cat in sorted({r["category"] for r in testable}):
        rs = [r for r in testable if r["category"] == cat]
        m["by_category"][cat] = {"n": len(rs),
                                 "accuracy": _rate(sum(correct(r, "verdict") for r in rs), len(rs)),
                                 "vacuous": sum(r["verdict"] == VACUOUS for r in rs)}
    return m


def _fmt(x):
    return "n/a" if x is None else f"{100 * x:.1f}%"


def markdown_summary(m: dict, title: str = "") -> str:
    s, n = m["single_poc"], m["negation_checked"]
    lines = [f"### {title}" if title else "",
             f"{m['n_claims']} claims ({m['n_true']} true, {m['n_false']} false, "
             f"{m['n_untestable']} untestable)", "",
             "| metric | single PoC | negation-checked |", "|---|---|---|",
             f"| false claims accepted as proven (lower is better) | {_fmt(s['false_acceptance_rate'])} | {_fmt(n['false_acceptance_rate'])} |",
             f"| true claims accepted as proven | {_fmt(s['true_acceptance_rate'])} | {_fmt(n['true_acceptance_rate'])} |",
             f"| coverage (definite verdicts) | {_fmt(s['coverage'])} | {_fmt(n['coverage'])} |",
             f"| precision of definite verdicts | {_fmt(s['precision_of_decided'])} | {_fmt(n['precision_of_decided'])} |",
             "",
             f"Verdicts: " + ", ".join(f"{k} {v}" for k, v in m["verdicts"].items() if v),
             f"Vacuous rate (testable): {_fmt(m['vacuous_rate_testable'])}; "
             f"vacuous cases also caught by static lint: {_fmt(m['vacuous_caught_by_static_lint'])}",
             f"Abstained on untestable claims: {_fmt(m['abstain_rate_untestable'])}; "
             f"abstained on testable claims: {_fmt(m['abstain_rate_testable'])}"]
    return "\n".join(l for l in lines if l is not None)
