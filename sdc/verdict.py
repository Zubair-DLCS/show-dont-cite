"""The negation check: combine the claim-PoC and negation-PoC outcomes.

                      negation PoC
                    PASS          FAIL
claim PoC  PASS   VACUOUS       DEMONSTRATED
           FAIL   REFUTED       INCONCLUSIVE

A PoC that "proves" both a statement and its negation proves nothing.
"""
from __future__ import annotations

from .sandbox import PASS, FAIL

DEMONSTRATED = "DEMONSTRATED"    # evidence for the claim, and against its negation
REFUTED = "REFUTED"              # evidence against the claim, and for its negation
VACUOUS = "VACUOUS"              # both "proven": the evidence is hollow
INCONCLUSIVE = "INCONCLUSIVE"    # both "disproven"
ABSTAIN = "ABSTAIN"              # prover said the claim is not demonstrable by code
ERROR = "ERROR"                  # crash, timeout, or no RESULT line

ALL_VERDICTS = [DEMONSTRATED, REFUTED, VACUOUS, INCONCLUSIVE, ABSTAIN, ERROR]


def negation_checked(claim_status: str | None, neg_status: str | None,
                     claim_abstained: bool, neg_abstained: bool) -> str:
    if claim_abstained or neg_abstained:
        return ABSTAIN
    if claim_status not in (PASS, FAIL) or neg_status not in (PASS, FAIL):
        return ERROR
    return {
        (PASS, FAIL): DEMONSTRATED,
        (FAIL, PASS): REFUTED,
        (PASS, PASS): VACUOUS,
        (FAIL, FAIL): INCONCLUSIVE,
    }[(claim_status, neg_status)]


def single_poc(claim_status: str | None, claim_abstained: bool) -> str:
    """Baseline: what you get if you only run one PoC for the claim."""
    if claim_abstained:
        return ABSTAIN
    if claim_status == PASS:
        return DEMONSTRATED
    if claim_status == FAIL:
        return REFUTED
    return ERROR
