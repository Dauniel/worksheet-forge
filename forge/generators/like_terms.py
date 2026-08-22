"""Combining like terms and distributing."""

from __future__ import annotations

import random

import sympy as sp

import math

from ..core.latexfmt import coeff, linear, terms
from ..core.problem import Problem
from ..core.registry import register
from ..core.sampling import nonzero_int, pick

X = sp.Symbol("x")
Y = sp.Symbol("y")

RANGES = {"easy": (1, 9), "medium": (2, 12), "hard": (2, 20)}

# How often ``combine_like_terms`` uses a second variable (``3x + 2y + 5 + x +
# 4y``) rather than one variable and constants. Easy stays single-variable so
# the first exposure is only about collecting one kind of term; from medium on,
# a second variable is the point of the exercise -- a student who can only
# collect x-terms has not learned the skill. Gating this behind "hard" *and* a
# coin flip (as this once did) meant a medium section never showed two
# variables at all, and a hard one showed them barely half the time.
TWO_VAR_CHANCE = {"easy": 0.0, "medium": 0.45, "hard": 0.75}


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
    if rng.random() < TWO_VAR_CHANCE[difficulty]:
        e = _c(rng, difficulty)
        question = terms(coeff(a, "x"), coeff(b, "y"), str(c), coeff(d, "x"), coeff(e, "y"))
        expr = a * X + b * Y + c + d * X + e * Y
    else:
        question = terms(coeff(a, "x"), str(b), coeff(c, "x"), str(d))
        expr = a * X + b + c * X + d
    return _mk(question, expr, "combine_like_terms", difficulty)

@register("like_terms", "polynomial_like_terms")
def polynomial_like_terms(rng: random.Random, difficulty: str) -> Problem:
    """Combine repeated powers while keeping each exponent unchanged."""
    degrees = (2,) if difficulty == "easy" else ((2, 1) if difficulty == "medium" else (3, 2, 1))
    rendered, expr = [], sp.Integer(0)
    for degree in degrees:
        a, b = _c(rng, difficulty), _c(rng, difficulty)
        while a + b == 0:
            b = _c(rng, difficulty)
        variable = "x" if degree == 1 else rf"x^{{{degree}}}"
        rendered.extend((coeff(a, variable), coeff(b, variable)))
        expr += (a + b) * X**degree
    rng.shuffle(rendered)
    return _mk(terms(*rendered), expr, "polynomial_like_terms", difficulty)


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


@register("like_terms", "add_subtract_linear")
def add_subtract_linear(rng: random.Random, difficulty: str) -> Problem:
    """Add or subtract two parenthesized binomials, including the classic
    ``(...) - (...)`` case where the second parenthesis' signs must flip."""
    a1, b1, a2, b2 = (_c(rng, difficulty) for _ in range(4))
    op = pick(rng, ("+", "-"))
    left = linear(a1, b1, "x")
    right = linear(a2, b2, "x")
    question = f"({left}) {op} ({right})"
    expr = (a1 * X + b1) + (a2 * X + b2) if op == "+" else (a1 * X + b1) - (a2 * X + b2)
    return _mk(question, expr, "add_subtract_linear", difficulty)


@register("like_terms", "factor_gcf")
def factor_gcf(rng: random.Random, difficulty: str) -> Problem:
    """Backwards construction: pick a coprime (a, b), then multiply by a GCF
    g so the printed expression's true greatest common factor is exactly g."""
    gcf_range = {"easy": (2, 6), "medium": (2, 9), "hard": (3, 12)}[difficulty]
    while True:
        a = nonzero_int(rng, -9, 9)
        b = nonzero_int(rng, -9, 9)
        if math.gcd(abs(a), abs(b)) == 1:
            break
    g = rng.randint(*gcf_range)
    question = terms(coeff(g * a, "x"), str(g * b))
    inner = terms(coeff(a, "x"), str(b))
    prefix = coeff(g, "") or str(g)
    answer = f"{prefix}({inner})"
    expr = g * (a * X + b)  # unexpanded: the verifier expands both sides itself
    return Problem(
        question_latex=f"${question}$",
        answer_latex=f"${answer}$",
        answer_expr=expr,
        topic="like_terms",
        subskill="factor_gcf",
        difficulty=difficulty,
        verify={"kind": "simplify", "expr": question},
    )
