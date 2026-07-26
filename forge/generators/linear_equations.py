"""Linear equations, always constructed backwards from a chosen solution.

Choosing ``x_sol`` first and deriving a constant from it makes no-solution and
infinite-solution cases structurally impossible, and keeps the answer clean.
"""

from __future__ import annotations

import random
from fractions import Fraction

import sympy as sp

from ..core.latexfmt import coeff, linear, num, terms
from ..core.problem import Problem
from ..core.registry import register
from ..core.sampling import nonzero_int, pick

RANGES = {"easy": (1, 9), "medium": (2, 12), "hard": (2, 15)}
NICE_DENOMS = (2, 3, 4)


def _solution(rng: random.Random, difficulty: str) -> Fraction:
    """Bias hard toward integers; occasionally a tidy fraction on harder work."""
    lo, hi = RANGES[difficulty]
    whole = nonzero_int(rng, -hi, hi)
    if difficulty != "easy" and rng.random() < 0.2:
        return Fraction(whole, pick(rng, NICE_DENOMS))
    return Fraction(whole)


def _mk(lhs: str, rhs: str, x_sol, subskill: str, difficulty: str) -> Problem:
    value = sp.Rational(x_sol.numerator, x_sol.denominator)
    return Problem(
        question_latex=f"${lhs} = {rhs}$",
        answer_latex=f"$x = {sp.latex(value)}$",
        answer_expr=value,
        topic="linear_equations",
        subskill=subskill,
        difficulty=difficulty,
        verify={"kind": "solve", "var": "x", "lhs": lhs, "rhs": rhs},
    )


@register("linear_equations", "one_step")
def one_step(rng: random.Random, difficulty: str) -> Problem:
    lo, hi = RANGES[difficulty]
    x_sol = Fraction(nonzero_int(rng, -hi, hi))
    if rng.random() < 0.5:
        b = nonzero_int(rng, -hi, hi)
        return _mk(terms("x", num(b)), num(x_sol + b), x_sol, "one_step", difficulty)
    m = nonzero_int(rng, 2, hi)
    return _mk(coeff(m, "x"), num(m * x_sol), x_sol, "one_step", difficulty)


@register("linear_equations", "two_step")
def two_step(rng: random.Random, difficulty: str) -> Problem:
    lo, hi = RANGES[difficulty]
    x_sol = _solution(rng, difficulty)
    m = nonzero_int(rng, 2, hi)
    b = nonzero_int(rng, -hi, hi)
    # rhs derived from the chosen solution, so it is exact by construction.
    return _mk(linear(m, b), num(m * x_sol + b), x_sol, "two_step", difficulty)


@register("linear_equations", "multi_step_both_sides")
def multi_step_both_sides(rng: random.Random, difficulty: str) -> Problem:
    lo, hi = RANGES[difficulty]
    x_sol = _solution(rng, difficulty)
    m1 = nonzero_int(rng, -hi, hi)
    m2 = nonzero_int(rng, -hi, hi)
    while m2 == m1:  # equal slopes would give no solution or infinitely many
        m2 = nonzero_int(rng, -hi, hi)
    b1 = nonzero_int(rng, -hi, hi)
    b2 = (m1 - m2) * x_sol + b1
    return _mk(
        linear(m1, b1), linear(m2, b2), x_sol, "multi_step_both_sides", difficulty
    )


@register("linear_equations", "with_distribution")
def with_distribution(rng: random.Random, difficulty: str) -> Problem:
    lo, hi = RANGES[difficulty]
    x_sol = Fraction(nonzero_int(rng, -hi, hi))
    k = nonzero_int(rng, 2, min(hi, 9))
    a = nonzero_int(rng, 1, min(hi, 9))
    b = nonzero_int(rng, -hi, hi)
    c = nonzero_int(rng, -hi, hi)

    inner = linear(a, b)
    prefix = coeff(k, "")
    lhs = terms(f"{prefix}({inner})", num(c))
    rhs = num(k * (a * x_sol + b) + c)
    return _mk(lhs, rhs, x_sol, "with_distribution", difficulty)
