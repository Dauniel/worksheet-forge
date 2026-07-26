"""Combining like terms and distributing."""

from __future__ import annotations

import random

import sympy as sp

from ..core.latexfmt import coeff, terms
from ..core.problem import Problem
from ..core.registry import register
from ..core.sampling import nonzero_int, pick

X = sp.Symbol("x")
Y = sp.Symbol("y")

RANGES = {"easy": (1, 9), "medium": (2, 12), "hard": (2, 20)}


def _c(rng: random.Random, difficulty: str) -> int:
    lo, hi = RANGES[difficulty]
    return nonzero_int(rng, -hi, hi) if rng.random() < 0.5 else rng.randint(lo, hi)


def _mk(question: str, expr, subskill: str, difficulty: str) -> Problem:
    expr = sp.expand(expr)
    return Problem(
        question_latex=f"${question}$",
        answer_latex=f"${sp.latex(expr)}$",
        answer_expr=expr,
        topic="like_terms",
        subskill=subskill,
        difficulty=difficulty,
        verify={"kind": "simplify", "expr": question},
    )


@register("like_terms", "combine_like_terms")
def combine_like_terms(rng: random.Random, difficulty: str) -> Problem:
    a, b, c, d = (_c(rng, difficulty) for _ in range(4))
    if difficulty == "hard" and rng.random() < 0.5:
        e = _c(rng, difficulty)
        question = terms(coeff(a, "x"), coeff(b, "y"), str(c), coeff(d, "x"), coeff(e, "y"))
        expr = a * X + b * Y + c + d * X + e * Y
    else:
        question = terms(coeff(a, "x"), str(b), coeff(c, "x"), str(d))
        expr = a * X + b + c * X + d
    return _mk(question, expr, "combine_like_terms", difficulty)


@register("like_terms", "distribute_and_combine")
def distribute_and_combine(rng: random.Random, difficulty: str) -> Problem:
    k = _c(rng, difficulty)
    a, b = _c(rng, difficulty), _c(rng, difficulty)
    inner = terms(coeff(a, "x"), str(b))
    tail_c, tail_k = _c(rng, difficulty), _c(rng, difficulty)

    prefix = coeff(k, "") or ""
    lead = f"{prefix}({inner})" if prefix not in ("", "-") else f"{'-' if prefix == '-' else ''}({inner})"
    question = terms(lead, coeff(tail_c, "x"), str(tail_k))
    expr = k * (a * X + b) + tail_c * X + tail_k
    return _mk(question, expr, "distribute_and_combine", difficulty)
