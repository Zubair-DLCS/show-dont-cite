"""Provers turn one statement into a PoC script (or an abstention).

- LLMProver: the real thing; asks a chat model for a PoC.
- OracleProver: ships the hand-written gold check. Upper bound; validates the harness.
- HollowPlainProver: always prints PASS, unconditionally. Static lint catches it.
- HollowDisguisedProver: computes something, then passes behind a tautological
  condition. Static lint does NOT catch it; the negation check does.
"""
from __future__ import annotations

import inspect
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from .backends import ChatBackend
from .prompts import POC_PROMPT, POC_SYSTEM

CLAIM, NEGATION = "claim", "negation"


@dataclass
class ProverOutput:
    code: str | None
    abstain_reason: str | None
    raw: str

    @property
    def abstained(self) -> bool:
        return self.abstain_reason is not None


_CODE_BLOCK = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.DOTALL)


def parse_llm_output(text: str) -> ProverOutput:
    stripped = text.strip()
    # Reasoning models sometimes wrap output in <think>...</think>.
    stripped = re.sub(r"<think>.*?</think>", "", stripped, flags=re.DOTALL).strip()
    m = re.match(r"^\s*NOT_DEMONSTRABLE\s*:?\s*(.*)$", stripped, re.IGNORECASE | re.DOTALL)
    if m and "```" not in stripped:
        return ProverOutput(None, m.group(1).strip() or "not demonstrable", text)
    blocks = _CODE_BLOCK.findall(stripped)
    if blocks:
        return ProverOutput(max(blocks, key=len).strip() + "\n", None, text)
    if "RESULT:" in stripped and ("print" in stripped or "import" in stripped):
        return ProverOutput(stripped + "\n", None, text)
    return ProverOutput(None, None, text)  # unparseable -> becomes ERROR downstream


class Prover:
    name = "base"

    def prove(self, statement: str, claim_id: str, polarity: str, timeout: int) -> ProverOutput:
        raise NotImplementedError  # pragma: no cover


class LLMProver(Prover):
    def __init__(self, backend: ChatBackend):
        self.backend = backend
        self.name = backend.name

    def prove(self, statement, claim_id, polarity, timeout):
        # Polarity is intentionally NOT shown to the model.
        prompt = POC_PROMPT.format(statement=statement, timeout=timeout)
        return parse_llm_output(self.backend.complete(POC_SYSTEM, prompt))


def _gold():
    root = Path(__file__).resolve().parent.parent / "gold"
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    import gold_checks
    return gold_checks.GOLD


class OracleProver(Prover):
    name = "oracle"

    def prove(self, statement, claim_id, polarity, timeout):
        gold = _gold()
        if claim_id not in gold:
            return ProverOutput(None, "no executable check exists for this claim", "")
        src = inspect.getsource(gold[claim_id])
        want = "holds" if polarity == CLAIM else "not holds"
        code = (f"{src}\n\nholds = bool({claim_id}())\n"
                f"print('original claim holds:', holds)\n"
                f"statement_true = holds if {polarity == CLAIM} else not holds\n"
                f"print('RESULT: PASS' if statement_true else 'RESULT: FAIL')\n")
        return ProverOutput(code, None, f"oracle ({want})")


class HollowPlainProver(Prover):
    name = "hollow-plain"

    def prove(self, statement, claim_id, polarity, timeout):
        code = ("import numpy as np\n"
                "x = np.random.default_rng(0).normal(size=1000)\n"
                "print('mean:', x.mean())\n"
                "print('RESULT: PASS')\n")
        return ProverOutput(code, None, "hollow-plain")


class HollowDisguisedProver(Prover):
    name = "hollow-disguised"

    def prove(self, statement, claim_id, polarity, timeout):
        code = ("import numpy as np\n"
                "rng = np.random.default_rng(0)\n"
                "samples = rng.normal(size=5000)\n"
                "effect = samples.mean()\n"
                "threshold = abs(effect) + 1.0  # 'chosen' after seeing the data\n"
                "print(f'effect={effect:.4f}  threshold={threshold:.4f}')\n"
                "if abs(effect) < threshold:\n"
                "    print('RESULT: PASS')\n"
                "else:\n"
                "    print('RESULT: FAIL')\n")
        return ProverOutput(code, None, "hollow-disguised")


def make_prover(kind: str, **kw) -> Prover:
    if kind == "oracle":
        return OracleProver()
    if kind == "hollow-plain":
        return HollowPlainProver()
    if kind == "hollow-disguised":
        return HollowDisguisedProver()
    if kind == "api":
        from .backends import OpenAICompatibleBackend
        return LLMProver(OpenAICompatibleBackend(model=kw.get("model"), api_base=kw.get("api_base"),
                                                 api_key=kw.get("api_key"),
                                                 temperature=kw.get("temperature", 0.2)))
    if kind == "hf":
        from .backends import TransformersBackend
        if not kw.get("model"):
            raise ValueError("--model is required for the hf prover")
        return LLMProver(TransformersBackend(kw["model"], load_in_4bit=kw.get("load_in_4bit", True)))
    raise ValueError(f"unknown prover {kind!r}")
