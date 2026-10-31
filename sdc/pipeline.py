"""Claim -> two independent PoCs (claim, negation) -> sandbox -> verdict."""
from __future__ import annotations

import json
import time
from pathlib import Path

from .claims import Claim
from .lint import lint
from .provers import CLAIM, NEGATION, Prover, ProverOutput
from .sandbox import NO_RESULT, run_script
from .verdict import negation_checked, single_poc


def _side(prover: Prover, statement: str, claim_id: str, polarity: str, timeout: int) -> dict:
    t0 = time.time()
    try:
        out = prover.prove(statement, claim_id, polarity, timeout)
    except Exception as exc:  # backend failure is recorded, not fatal
        out = ProverOutput(None, None, f"PROVER_EXCEPTION: {type(exc).__name__}: {exc}")
    gen_seconds = time.time() - t0
    side = {"statement": statement, "abstained": out.abstained,
            "abstain_reason": out.abstain_reason, "code": out.code,
            "raw": out.raw[-4000:], "gen_seconds": round(gen_seconds, 2),
            "lint": [], "exec": None, "status": None}
    if out.abstained:
        return side
    if not out.code:
        side["status"] = NO_RESULT
        side["lint"] = ["unparseable_output"]
        return side
    side["lint"] = lint(out.code)
    res = run_script(out.code, timeout=timeout)
    side["exec"] = res.to_dict()
    side["status"] = res.status
    return side


def check_claim(claim: Claim, prover: Prover, timeout: int = 30) -> dict:
    c = _side(prover, claim.claim, claim.id, CLAIM, timeout)
    n = _side(prover, claim.negation, claim.id, NEGATION, timeout)
    return {
        **claim.to_dict(),
        "prover": prover.name,
        "claim_poc": c,
        "negation_poc": n,
        "verdict": negation_checked(c["status"], n["status"], c["abstained"], n["abstained"]),
        "single_poc_verdict": single_poc(c["status"], c["abstained"]),
    }


def run(claims: list[Claim], prover: Prover, out_path: str | Path,
        timeout: int = 30, resume: bool = True, verbose: bool = True) -> list[dict]:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    done: dict[str, dict] = {}
    if resume and out_path.exists():
        for line in out_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                done[rec["id"]] = rec
    results = []
    with open(out_path, "a", encoding="utf-8") as fh:
        for i, claim in enumerate(claims, 1):
            if claim.id in done:
                results.append(done[claim.id])
                continue
            rec = check_claim(claim, prover, timeout)
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            results.append(rec)
            if verbose:
                print(f"[{i}/{len(claims)}] {claim.id} label={claim.label:<10} "
                      f"claim={rec['claim_poc']['status'] or 'abstain'}  "
                      f"neg={rec['negation_poc']['status'] or 'abstain'}  -> {rec['verdict']}",
                      flush=True)
    return results
