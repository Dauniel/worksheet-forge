"""Exponent rules."""

from __future__ import annotations

import random

import sympy as sp

from ..core.problem import Problem
from ..core.registry import register
from ..core.sampling import nonzero_int, pick

X = sp.Symbol("x")
EXP_RANGE = {"easy": (2, 7), "medium": (2, 9), "hard": (2, 12)}
# Easy work keeps coefficients small but not fixed at 1 -- a constant
# coefficient collapses the sample space into a handful of archetypes.
COEF_RANGE = {"easy": (1, 4), "medium": (2, 9), "hard": (2, 12)}


def _mk(question: str, expr, subskill: str, difficulty: str, kind: str = "simplify") -> Problem:
    return Problem(
        question_latex=f"${question}$",
        answer_latex=f"${sp.latex(expr)}$",
        answer_expr=expr,
        topic="exponents",
        subskill=subskill,
        difficulty=difficulty,
        verify={"kind": kind, "expr": question},
    )


@register("exponents", "product_rule")
def product_rule(rng: random.Random, difficulty: str) -> Problem:
    lo, hi = EXP_RANGE[difficulty]
    a, b = rng.randint(lo, hi), rng.randint(lo, hi)
    ca = rng.randint(*COEF_RANGE[difficulty])
    cb = rng.randint(*COEF_RANGE[difficulty])
    lead_a = "" if ca == 1 else str(ca)
    lead_b = "" if cb == 1 else str(cb)
    question = rf"{lead_a}x^{{{a}}} \cdot {lead_b}x^{{{b}}}"
    return _mk(question, ca * cb * X ** (a + b), "product_rule", difficulty)


@register("exponents", "quotient_rule")
def quotient_rule(rng: random.Random, difficulty: str) -> Problem:
    lo, hi = EXP_RANGE[difficulty]
    b = rng.randint(lo, hi)
    a = b + rng.randint(1, hi)  # keep the result a positive power
    k = rng.randint(*COEF_RANGE[difficulty])
    lead = "" if k == 1 else str(k)  # never "1x"
    question = rf"\dfrac{{{lead}x^{{{a}}}}}{{x^{{{b}}}}}"
    return _mk(question, k * X ** (a - b), "quotient_rule", difficulty)


@register("exponents", "power_rule")
def power_rule(rng: random.Random, difficulty: str) -> Problem:
    lo, hi = EXP_RANGE[difficulty]
    a, n = rng.randint(lo, hi), rng.randint(2, 4 if difficulty != "hard" else 5)
    k = rng.randint(*COEF_RANGE[difficulty])
    lead = "" if k == 1 else str(k)
    question = rf"({lead}x^{{{a}}})^{{{n}}}"
    return _mk(question, k**n * X ** (a * n), "power_rule", difficulty)


@register("exponents", "negative_exponents")
def negative_exponents(rng: random.Random, difficulty: str) -> Problem:
    """Numeric so the answer is a concrete fraction, not just a rewrite."""
    base = pick(rng, (2, 3, 4, 5) if difficulty == "easy" else (2, 3, 4, 5, 6, 7, 10))
    n = rng.randint(1, 3 if difficulty == "easy" else 4)
    k = rng.randint(1, 9)
    lead = "" if k == 1 else f"{k} \\cdot "

    style = rng.randrange(3)
    if style == 0:
        question = rf"{lead}{base}^{{-{n}}}"
        value = sp.Rational(k, base**n)
    elif style == 1:
        question = rf"\dfrac{{{k}}}{{{base}^{{-{n}}}}}"
        value = sp.Integer(k * base**n)
    else:
        m = rng.randint(1, n)
        question = rf"{lead}({base}^{{{m}}})^{{-{n}}}"
        value = sp.Rational(k, base ** (m * n))
    return _mk(question, value, "negative_exponents", difficulty, "evaluate")


@register("exponents", "zero_and_negative_powers")
def zero_and_negative_powers(rng: random.Random, difficulty: str) -> Problem:
    """Mixed product of powers of the same base, including zero exponents."""
    base = pick(rng, (2, 3, 5) if difficulty == "easy" else (2, 3, 5, 6, 7))
    a = rng.randint(2, 5)
    b = rng.randint(-4, 0)
    question = rf"{base}^{{{a}}} \cdot {base}^{{{b}}}"
    value = sp.Rational(base) ** (a + b)
    return _mk(question, value, "zero_and_negative_powers", difficulty, "evaluate")
