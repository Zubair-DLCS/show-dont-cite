"""Ask mode: the answer-engine front end.

question -> short answer + atomic claims (each with its negation)
         -> negation-checked PoCs per claim
         -> answer printed with an evidence verdict next to every claim.
"""
from __future__ import annotations

import json
import re

from .backends import ChatBackend
from .claims import Claim
from .pipeline import check_claim
from .prompts import DECOMPOSE_PROMPT, DECOMPOSE_SYSTEM
from .provers import LLMProver

_MARK = {"DEMONSTRATED": "[shown]", "REFUTED": "[shown FALSE]", "VACUOUS": "[hollow evidence]",
         "INCONCLUSIVE": "[inconclusive]", "ABSTAIN": "[not testable by code]", "ERROR": "[PoC failed to run]"}


def _extract_json(text: str) -> dict:
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL) or re.search(r"(\{.*\})", text, re.DOTALL)
    if not m:
        raise ValueError(f"model did not return JSON:\n{text[:500]}")
    return json.loads(m.group(1))


def decompose(backend: ChatBackend, question: str) -> tuple[str, list[Claim]]:
    data = _extract_json(backend.complete(DECOMPOSE_SYSTEM, DECOMPOSE_PROMPT.format(question=question)))
    claims = [Claim(id=f"q{i:02d}", claim=c["claim"], negation=c["negation"], label="unknown", category="ask")
              for i, c in enumerate(data.get("claims", []), 1) if c.get("claim") and c.get("negation")]
    return data.get("answer", ""), claims


def ask(backend: ChatBackend, question: str, timeout: int = 30) -> tuple[str, list[dict]]:
    answer, claims = decompose(backend, question)
    prover = LLMProver(backend)
    results = [check_claim(c, prover, timeout) for c in claims]
    return answer, results


def format_answer(question: str, answer: str, results: list[dict]) -> str:
    lines = [f"Q: {question}", "", answer.strip(), "", "Evidence:"]
    for r in results:
        lines.append(f"  {_MARK.get(r['verdict'], r['verdict']):<24} {r['claim']}")
    shown = sum(r["verdict"] in ("DEMONSTRATED", "REFUTED") for r in results)
    lines.append("")
    lines.append(f"{shown}/{len(results)} claims have non-hollow executable evidence.")
    if any(r["verdict"] == "REFUTED" for r in results):
        lines.append("WARNING: at least one claim in the answer was shown to be FALSE by its own PoCs.")
    return "\n".join(lines)
