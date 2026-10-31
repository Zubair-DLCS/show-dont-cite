"""Loading and validating benchmark claims."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path

VALID_LABELS = {"true", "false", "untestable"}


@dataclass
class Claim:
    id: str
    claim: str
    negation: str
    label: str = "unknown"  # true | false | untestable | unknown (ask mode)
    category: str = "misc"

    def to_dict(self) -> dict:
        return asdict(self)


def load_claims(path: str | Path, ids: list[str] | None = None,
                limit: int | None = None) -> list[Claim]:
    claims = []
    with open(path, encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            for key in ("id", "claim", "negation"):
                if not rec.get(key):
                    raise ValueError(f"{path}:{line_no}: missing '{key}'")
            if rec.get("label", "unknown") not in VALID_LABELS | {"unknown"}:
                raise ValueError(f"{path}:{line_no}: bad label {rec.get('label')!r}")
            claims.append(Claim(**{k: rec[k] for k in
                                   ("id", "claim", "negation", "label", "category") if k in rec}))
    if ids:
        wanted = set(ids)
        claims = [c for c in claims if c.id in wanted]
    if limit:
        claims = claims[:limit]
    return claims
