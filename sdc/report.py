"""Single-file HTML report: every claim with its verdict and both PoCs."""
from __future__ import annotations

import html
from pathlib import Path

from .evaluate import metrics

_COLORS = {"DEMONSTRATED": "#1f7a4d", "REFUTED": "#1d5fa8", "VACUOUS": "#b3261e",
           "INCONCLUSIVE": "#8a6d00", "ABSTAIN": "#5f6368", "ERROR": "#6b3fa0"}

_CSS = """
body{font:15px/1.5 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;margin:0;background:#f6f6f3;color:#1c1c1c}
main{max-width:1100px;margin:0 auto;padding:32px 20px}
h1{font-size:26px;margin:0 0 4px}.sub{color:#555;margin:0 0 24px}
.tiles{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:28px}
.tile{background:#fff;border:1px solid #e2e2dc;border-radius:10px;padding:12px 16px;min-width:150px}
.tile b{display:block;font-size:22px}.tile span{color:#555;font-size:13px}
.card{background:#fff;border:1px solid #e2e2dc;border-radius:10px;padding:16px 18px;margin-bottom:14px}
.head{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.badge{color:#fff;border-radius:999px;padding:2px 10px;font-size:12px;font-weight:600;letter-spacing:.02em}
.meta{color:#666;font-size:13px}.wrong{color:#b3261e;font-weight:600}
.claim{margin:8px 0 10px;font-size:16px}
.sides{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media(max-width:800px){.sides{grid-template-columns:1fr}}
.side{background:#fafaf8;border:1px solid #ecece6;border-radius:8px;padding:10px}
.side h4{margin:0 0 4px;font-size:13px;text-transform:uppercase;color:#555;letter-spacing:.04em}
.st{font-weight:700}.st.pass{color:#1f7a4d}.st.fail{color:#1d5fa8}.st.other{color:#6b3fa0}
pre{white-space:pre-wrap;word-break:break-word;background:#1e1e1e;color:#e6e6e6;padding:10px;border-radius:6px;font-size:12.5px;max-height:420px;overflow:auto}
summary{cursor:pointer;color:#333;font-size:13px;margin-top:6px}
.flag{background:#fdecea;color:#b3261e;border-radius:4px;padding:1px 6px;font-size:12px;margin-left:6px}
.filters{margin:0 0 16px}.filters button{border:1px solid #ccc;background:#fff;border-radius:6px;padding:4px 10px;margin:0 6px 6px 0;cursor:pointer}
.filters button.on{background:#1c1c1c;color:#fff;border-color:#1c1c1c}
"""

_JS = """
function f(v,b){document.querySelectorAll('.filters button').forEach(x=>x.classList.remove('on'));b.classList.add('on');
document.querySelectorAll('.card').forEach(c=>{c.style.display=(v==='ALL'||c.dataset.v===v||(v==='WRONG'&&c.dataset.w==='1'))?'':'none'})}
"""


def _e(s) -> str:
    return html.escape(str(s if s is not None else ""))


def _side(title: str, s: dict) -> str:
    if s["abstained"]:
        body = f"<div class='st other'>ABSTAINED</div><div class='meta'>{_e(s['abstain_reason'])}</div>"
    else:
        st = s["status"] or "none"
        cls = st if st in ("pass", "fail") else "other"
        ex = s.get("exec") or {}
        flags = "".join(f"<span class='flag'>{_e(f)}</span>" for f in s["lint"])
        out = (ex.get("stdout") or "") + (("\n[stderr]\n" + ex["stderr"]) if ex.get("stderr") else "")
        body = (f"<div><span class='st {cls}'>{_e(st.upper())}</span>{flags}"
                f"<span class='meta'> &middot; {ex.get('seconds', 0):.2f}s</span></div>"
                f"<details><summary>output</summary><pre>{_e(out.strip() or '(no output)')}</pre></details>"
                f"<details><summary>proof-of-concept code</summary><pre>{_e(s['code'] or s['raw'])}</pre></details>")
    return f"<div class='side'><h4>{title}</h4><div class='meta'>{_e(s['statement'])}</div>{body}</div>"


def render(results: list[dict], title: str = "Show, Don't Cite") -> str:
    m = metrics(results)
    prover = results[0]["prover"] if results else "?"
    n = m["negation_checked"]
    s = m["single_poc"]

    def pct(x):
        return "n/a" if x is None else f"{100 * x:.0f}%"
    tiles = [
        (pct(s["false_acceptance_rate"]), "false claims accepted, single PoC"),
        (pct(n["false_acceptance_rate"]), "false claims accepted, negation-checked"),
        (pct(n["precision_of_decided"]), "precision of definite verdicts"),
        (pct(m["vacuous_rate_testable"]), "hollow (VACUOUS) evidence"),
        (str(m["n_claims"]), "claims"),
    ]
    out = [f"<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
           f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
           f"<title>{_e(title)}</title><style>{_CSS}</style></head><body><main>",
           f"<h1>{_e(title)}</h1><p class='sub'>Prover: <b>{_e(prover)}</b>. Every claim gets two "
           f"independently generated proofs of concept: one for the claim and one for its negation. "
           f"If both pass, the evidence is hollow.</p>",
           "<div class='tiles'>" + "".join(f"<div class='tile'><b>{a}</b><span>{_e(b)}</span></div>"
                                           for a, b in tiles) + "</div>",
           "<div class='filters'>" + "".join(
               f"<button onclick=\"f('{v}',this)\"{' class=on' if v == 'ALL' else ''}>{v.title()}</button>"
               for v in ["ALL", "WRONG", "DEMONSTRATED", "REFUTED", "VACUOUS", "INCONCLUSIVE", "ABSTAIN", "ERROR"]
           ) + "</div>"]
    for r in results:
        v = r["verdict"]
        wrong = (r["label"] == "true" and v != "DEMONSTRATED") or \
                (r["label"] == "false" and v != "REFUTED") or \
                (r["label"] == "untestable" and v != "ABSTAIN")
        out.append(
            f"<div class='card' data-v='{v}' data-w='{1 if wrong else 0}'><div class='head'>"
            f"<span class='badge' style='background:{_COLORS.get(v, '#444')}'>{v}</span>"
            f"<span class='meta'>{_e(r['id'])} &middot; {_e(r['category'])} &middot; ground truth: "
            f"<b>{_e(r['label'])}</b> &middot; single-PoC baseline would say {_e(r['single_poc_verdict'])}</span>"
            + ("<span class='wrong'>disagrees with ground truth</span>" if wrong and r['label'] != 'unknown' else "")
            + f"</div><div class='claim'>{_e(r['claim'])}</div><div class='sides'>"
            f"{_side('PoC for the claim', r['claim_poc'])}{_side('PoC for the negation', r['negation_poc'])}"
            f"</div></div>")
    out.append(f"<script>{_JS}</script></main></body></html>")
    return "".join(out)


def write_report(results: list[dict], path: str | Path, title: str = "Show, Don't Cite") -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render(results, title), encoding="utf-8")
    return path
