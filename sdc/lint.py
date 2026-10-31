"""Cheap static checks for hollow PoCs.

These catch only the laziest failure (printing PASS unconditionally). The
point of the project is that static checks are not enough: a PoC can wrap
PASS in a condition that is always true. The negation check catches both.
"""
from __future__ import annotations

import ast

UNCONDITIONAL_PASS = "unconditional_pass"
NO_COMPARISON = "no_comparison"
SYNTAX_ERROR = "syntax_error"

_BRANCHING = (ast.If, ast.IfExp, ast.While, ast.For, ast.Try, ast.Match,
              ast.BoolOp, ast.comprehension)


def _mentions_pass(node: ast.AST) -> bool:
    for sub in ast.walk(node):
        if isinstance(sub, ast.Constant) and isinstance(sub.value, str) and "RESULT: PASS" in sub.value:
            return True
    return False


def lint(code: str) -> list[str]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return [SYNTAX_ERROR]

    parents: dict[ast.AST, ast.AST] = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node

    flags = []
    # Walk up from every "RESULT: PASS" literal; if no branching construct
    # sits anywhere above it (including an `x if c else y` inside print()),
    # the PASS cannot depend on anything the script computed.
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and _mentions_pass(node):
            cur, guarded = node, False
            while cur in parents:
                cur = parents[cur]
                if isinstance(cur, _BRANCHING):
                    guarded = True
                    break
            if not guarded:
                flags.append(UNCONDITIONAL_PASS)
                break

    if not any(isinstance(n, (ast.Compare, ast.Assert)) for n in ast.walk(tree)):
        flags.append(NO_COMPARISON)
    return flags
