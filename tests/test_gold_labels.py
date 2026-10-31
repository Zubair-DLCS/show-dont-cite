"""Every testable label in the benchmark is re-derived by running code,
through the same sandbox the LLM PoCs go through."""
import pytest

from sdc.claims import load_claims
from sdc.cli import DEFAULT_CLAIMS
from sdc.pipeline import check_claim
from sdc.provers import OracleProver

CLAIMS = load_claims(DEFAULT_CLAIMS)


@pytest.mark.parametrize("claim", CLAIMS, ids=[c.id for c in CLAIMS])
def test_label_matches_execution(claim):
    rec = check_claim(claim, OracleProver(), timeout=60)
    expected = {"true": "DEMONSTRATED", "false": "REFUTED", "untestable": "ABSTAIN"}[claim.label]
    assert rec["verdict"] == expected, rec["claim_poc"]["exec"]
