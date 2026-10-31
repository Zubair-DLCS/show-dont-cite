import json

import pytest

from sdc.ask import ask, format_answer
from sdc.backends import ChatBackend
from sdc.claims import Claim, load_claims
from sdc.evaluate import metrics
from sdc.lint import NO_COMPARISON, UNCONDITIONAL_PASS, lint
from sdc.pipeline import check_claim
from sdc.provers import LLMProver, parse_llm_output
from sdc.sandbox import ERROR, FAIL, NO_RESULT, PASS, TIMEOUT, run_script
from sdc.verdict import (ABSTAIN, DEMONSTRATED, INCONCLUSIVE, REFUTED, VACUOUS,
                         negation_checked, single_poc)
from sdc.cli import DEFAULT_CLAIMS


@pytest.mark.parametrize("c,n,expected", [
    (PASS, FAIL, DEMONSTRATED), (FAIL, PASS, REFUTED),
    (PASS, PASS, VACUOUS), (FAIL, FAIL, INCONCLUSIVE),
    (PASS, ERROR, "ERROR"), (TIMEOUT, FAIL, "ERROR"),
])
def test_verdict_matrix(c, n, expected):
    assert negation_checked(c, n, False, False) == expected


def test_abstain_wins():
    assert negation_checked(None, PASS, True, False) == ABSTAIN
    assert single_poc(None, True) == ABSTAIN


def test_sandbox_statuses():
    assert run_script("print('RESULT: PASS')").status == PASS
    assert run_script("print('x')\nprint('RESULT: FAIL')").status == FAIL
    assert run_script("print('no verdict')").status == NO_RESULT
    assert run_script("raise SystemExit(3)").status == ERROR
    assert run_script("import time\ntime.sleep(5)", timeout=1).status == TIMEOUT


def test_sandbox_only_last_line_counts():
    assert run_script("print('RESULT: PASS')\nprint('RESULT: FAIL')").status == FAIL


def test_lint():
    assert UNCONDITIONAL_PASS in lint("x = 1\nprint('RESULT: PASS')")
    assert lint("ok = 2 > 1\nprint('RESULT: PASS' if ok else 'RESULT: FAIL')") == []
    disguised = "e = 0.1\nif abs(e) < abs(e) + 1:\n    print('RESULT: PASS')\nelse:\n    print('RESULT: FAIL')"
    assert lint(disguised) == []  # static lint cannot see the tautology
    assert NO_COMPARISON in lint("print('RESULT: FAIL')")


def test_parse_llm_output():
    out = parse_llm_output("Here you go:\n```python\nprint('RESULT: PASS')\n```\n")
    assert out.code.strip() == "print('RESULT: PASS')" and not out.abstained
    ab = parse_llm_output("NOT_DEMONSTRABLE: historical fact")
    assert ab.abstained and "historical" in ab.abstain_reason
    think = parse_llm_output("<think>hmm</think>\n```py\nprint(1)\n```")
    assert think.code.strip() == "print(1)"
    assert parse_llm_output("I cannot do that.").code is None


def test_claims_file_is_valid():
    claims = load_claims(DEFAULT_CLAIMS)
    ids = [c.id for c in claims]
    assert len(ids) == len(set(ids)) >= 60
    assert all(c.claim != c.negation for c in claims)


class FakeLLM(ChatBackend):
    """Answers like an honest model for a toy claim set."""
    name = "fake"

    def complete(self, system, user):
        if "Question:" in user:
            return json.dumps({"answer": "Yes, sorted() is stable; heapq is a min-heap.",
                               "claims": [
                                   {"claim": "sorted() is stable", "negation": "sorted() is not stable"},
                                   {"claim": "heapq is a max-heap", "negation": "heapq is not a max-heap"},
                                   {"claim": "Python appeared in 1991", "negation": "Python did not appear in 1991"}]})
        stmt = user.split('"')[1]
        if "1991" in stmt:
            return "NOT_DEMONSTRABLE: historical"
        truth = {"sorted() is stable": True, "sorted() is not stable": False,
                 "heapq is a max-heap": False, "heapq is not a max-heap": True}[stmt]
        return f"```python\nv = {truth}\nprint('RESULT: PASS' if v else 'RESULT: FAIL')\n```"


def test_ask_mode_end_to_end():
    answer, results = ask(FakeLLM(), "Is sorted stable and is heapq a max-heap?", timeout=10)
    verdicts = [r["verdict"] for r in results]
    assert verdicts == [DEMONSTRATED, REFUTED, ABSTAIN]
    text = format_answer("q", answer, results)
    assert "shown FALSE" in text and "2/3" in text


def test_metrics_on_llm_prover():
    claim = Claim("t1", "sorted() is stable", "sorted() is not stable", "true", "python")
    rec = check_claim(claim, LLMProver(FakeLLM()), timeout=10)
    m = metrics([rec])
    assert rec["verdict"] == DEMONSTRATED
    assert m["negation_checked"]["true_acceptance_rate"] == 1.0
