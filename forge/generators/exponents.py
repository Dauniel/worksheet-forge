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
# negative_exponents and zero_and_negative_powers each used a bare
# ``if difficulty == "easy"`` test, so they advertised three tiers and
# implemented two -- medium and hard were byte-identical. Three bands each.
NEG_BASES = {
    "easy": (2, 3, 4, 5),
    "medium": (2, 3, 4, 5, 6, 7, 10),
    "hard": (2, 3, 5, 6, 7, 10, 11, 12),
}
NEG_MAX_N = {"easy": 3, "medium": 4, "hard": 4}
NEG_COEF = {"easy": (1, 9), "medium": (1, 9), "hard": (2, 12)}
ZNP_BASES = {"easy": (2, 3, 5), "medium": (2, 3, 5, 6, 7), "hard": (2, 3, 5, 6, 7, 10)}
ZNP_A = {"easy": (2, 5), "medium": (2, 5), "hard": (2, 6)}
ZNP_B = {"easy": (-4, 0), "medium": (-4, 0), "hard": (-5, 0)}
# Powers stay readable: no key running to seven figures.
ZNP_MAX = 100_000


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
    base = pick(rng, NEG_BASES[difficulty])
    n = rng.randint(1, NEG_MAX_N[difficulty])
    k = rng.randint(*NEG_COEF[difficulty])
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


@register("exponents", "combined_rules")
def combined_rules(rng: random.Random, difficulty: str) -> Problem:
    """Multi-variable expressions that stack several exponent rules at once:

    a nested power times a monomial, a quotient of two-variable monomials, a
    negative-exponent factor that must clean up positive, or a nested power
    of a quotient. Always resolves to a positive-exponent monomial.
    """
    lo, hi = EXP_RANGE[difficulty]
    Y = sp.Symbol("y")
    style = rng.randrange(4)

    if style == 0:
        ca = rng.randint(*COEF_RANGE[difficulty])
        a, b = rng.randint(lo, hi), rng.randint(1, hi)
        n = rng.randint(2, 3)
        cb = rng.randint(*COEF_RANGE[difficulty])
        c, d = rng.randint(lo, hi), rng.randint(1, hi)
        lead_a = "" if ca == 1 else str(ca)
        lead_b = "" if cb == 1 else str(cb)
        question = (
            rf"({lead_a}x^{{{a}}}y^{{{b}}})^{{{n}}} \cdot {lead_b}x^{{{c}}}y^{{{d}}}"
        )
        value = (ca**n) * cb * X ** (a * n + c) * Y ** (b * n + d)
    elif style == 1:
        ca = rng.randint(2, max(2, COEF_RANGE[difficulty][1]))
        divisors = [i for i in range(1, ca + 1) if ca % i == 0]
        cb = pick(rng, divisors)
        a = rng.randint(lo + 2, hi + 2)
        c = rng.randint(lo, a - 1)
        b = rng.randint(lo + 2, hi + 2)
        d = rng.randint(lo, b - 1)
        lead_a = "" if ca == 1 else str(ca)
        lead_b = "" if cb == 1 else str(cb)
        question = (
            rf"\dfrac{{{lead_a}x^{{{a}}}y^{{{b}}}}}{{{lead_b}x^{{{c}}}y^{{{d}}}}}"
        )
        value = sp.Rational(ca, cb) * X ** (a - c) * Y ** (b - d)
    elif style == 2:
        ca = rng.randint(2, 6)
        a = rng.randint(1, 3)
        n = rng.randint(2, 3)
        m = a * n + rng.randint(0, hi)
        question = rf"({ca}x^{{-{a}}})^{{{n}}} \cdot x^{{{m}}}"
        value = sp.Integer(ca**n) * X ** (m - a * n)
    else:
        ca = rng.randint(2, 6)
        divisors = [i for i in range(1, ca + 1) if ca % i == 0]
        cb = pick(rng, divisors)
        a = rng.randint(lo + 1, hi + 1)
        c = rng.randint(lo, a - 1)
        n = rng.randint(2, 3)
        lead_a = "" if ca == 1 else str(ca)
        lead_b = "" if cb == 1 else str(cb)
        question = rf"\left(\dfrac{{{lead_a}x^{{{a}}}}}{{{lead_b}x^{{{c}}}}}\right)^{{{n}}}"
        value = sp.Rational(ca, cb) ** n * X ** ((a - c) * n)

    return _mk(question, value, "combined_rules", difficulty)


@register("exponents", "zero_and_negative_powers")
def zero_and_negative_powers(rng: random.Random, difficulty: str) -> Problem:
    """Mixed product of powers of the same base, including zero exponents."""
    while True:
        base = pick(rng, ZNP_BASES[difficulty])
        a = rng.randint(*ZNP_A[difficulty])
        b = rng.randint(*ZNP_B[difficulty])
        value = sp.Rational(base) ** (a + b)
        if max(abs(sp.numer(value)), abs(sp.denom(value))) <= ZNP_MAX:
            break
    question = rf"{base}^{{{a}}} \cdot {base}^{{{b}}}"
    return _mk(question, value, "zero_and_negative_powers", difficulty, "evaluate")
