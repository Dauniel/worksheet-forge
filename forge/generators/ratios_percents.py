"""Proportions, percents, and percent change."""

from __future__ import annotations

import random
from fractions import Fraction

import sympy as sp

from ..core.latexfmt import num
from ..core.problem import Problem
from ..core.registry import register
from ..core.sampling import nonzero_int, pick

SCALES = {"easy": (2, 3, 4, 5), "medium": (2, 3, 4, 5, 6, 8), "hard": (3, 4, 6, 7, 9, 12)}
PERCENTS = {
    "easy": (10, 20, 25, 50, 75),
    "medium": (5, 12, 15, 20, 30, 40, 60, 80),
    "hard": (7, 12, 18, 22, 35, 45, 65, 85, 110, 125),
}


@register("ratios_percents", "proportions")
def proportions(rng: random.Random, difficulty: str) -> Problem:
    """Built backwards: choose the base ratio and a scale factor."""
    a = rng.randint(1, 12)
    b = rng.randint(2, 15)
    k = pick(rng, SCALES[difficulty])
    c, d = a * k, b * k

    # Hide one of the four entries behind x.
    slot = rng.randrange(4)
    cells = [str(a), str(b), str(c), str(d)]
    answer = [a, b, c, d][slot]
    cells[slot] = "x"
    lhs = rf"\dfrac{{{cells[0]}}}{{{cells[1]}}}"
    rhs = rf"\dfrac{{{cells[2]}}}{{{cells[3]}}}"
    value = sp.Integer(answer)
    return Problem(
        question_latex=f"${lhs} = {rhs}$",
        answer_latex=f"$x = {sp.latex(value)}$",
        answer_expr=value,
        topic="ratios_percents",
        subskill="proportions",
        difficulty=difficulty,
        verify={"kind": "solve", "var": "x", "lhs": lhs, "rhs": rhs},
    )


@register("ratios_percents", "percent_of")
def percent_of(rng: random.Random, difficulty: str) -> Problem:
    pct = pick(rng, PERCENTS[difficulty])
    whole = rng.randint(2, 40) * pick(rng, (4, 5, 10, 20))
    value = sp.Rational(pct, 100) * whole
    return Problem(
        question_latex=rf"${pct}\%$ of ${whole}$",
        answer_latex=f"${sp.latex(value)}$",
        answer_expr=value,
        topic="ratios_percents",
        subskill="percent_of",
        difficulty=difficulty,
        verify={"kind": "percent_of"},
    )


@register("ratios_percents", "percent_change")
def percent_change(rng: random.Random, difficulty: str) -> Problem:
    """Built backwards from a clean percentage so the answer is not ugly."""
    pct = pick(rng, PERCENTS[difficulty]) * rng.choice((1, -1))
    # Choose an old value divisible by 100/gcd so the new value stays an integer.
    step = 100 // sp.igcd(abs(pct), 100)
    old = step * rng.randint(1, max(3, 60 // step))
    new = old + sp.Rational(pct, 100) * old
    value = sp.Rational(pct)
    return Problem(
        question_latex=f"from ${old}$ to ${int(new)}$",
        answer_latex=rf"${sp.latex(value)}\%$",
        answer_expr=value,
        topic="ratios_percents",
        subskill="percent_change",
        difficulty=difficulty,
        verify={"kind": "percent_change"},
    )
