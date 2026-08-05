"""Exponential and logarithmic equations, plus the log product rule.

Every equation is built backwards from a chosen clean answer: exponential
equations from ``x_sol`` via ``c = a**x_sol``; logarithmic equations from the
definition ``log_b(x) = c  <=>  x = b**c``. ``condense_log`` is the one case
that isn't equation-solving -- it's checked by recomputing both sides of the
log product identity numerically/symbolically instead.
"""

from __future__ import annotations

import random

import sympy as sp

from ..core.latexfmt import dnum
from ..core.problem import Problem
from ..core.registry import register
from ..core.sampling import pick

BASES = (2, 3, 4, 5, 6, 7, 8, 9, 10)
X_SOL_RANGE = {"easy": (0, 6), "medium": (-4, 7), "hard": (-5, 8)}


@register("exponential_logarithms", "solve_exponential")
def solve_exponential(rng: random.Random, difficulty: str) -> Problem:
    """``a^x = c``, with ``c = a**x_sol`` so the answer is always exact.

    Drawing from nine small bases (rather than a wide exponent range on a
    few) keeps every ``c`` a reasonable size -- ``10^7`` is the worst case,
    never a 15-digit number or a fraction with a huge denominator.
    """
    a = pick(rng, BASES)
    lo, hi = X_SOL_RANGE[difficulty]
    x_sol = rng.randint(lo, hi)
    c = sp.Rational(a) ** x_sol

    return Problem(
        question_latex=f"${a}^x = {dnum(c)}$",
        answer_latex=f"$x = {x_sol}$",
        answer_expr=sp.Integer(x_sol),
        topic="exponential_logarithms",
        subskill="solve_exponential",
        difficulty=difficulty,
        verify={"kind": "solve_exponential"},
    )


C_RANGE = {"easy": (1, 7), "medium": (1, 8), "hard": (1, 9)}


@register("exponential_logarithms", "solve_logarithmic")
def solve_logarithmic(rng: random.Random, difficulty: str) -> Problem:
    """``log_b(x) = c``, with ``x = b**c`` so the answer is always exact.

    Nine small bases keep ``x = b**c`` a reasonable size for the same reason
    as ``solve_exponential``: ``10^7`` is the worst case, never absurd.
    """
    b = pick(rng, BASES)
    lo, hi = C_RANGE[difficulty]
    c = rng.randint(lo, hi)
    x_val = b ** c

    return Problem(
        question_latex=rf"$\log_{{{b}}}(x) = {c}$",
        answer_latex=f"$x = {x_val}$",
        answer_expr=sp.Integer(x_val),
        topic="exponential_logarithms",
        subskill="solve_logarithmic",
        difficulty=difficulty,
        verify={"kind": "solve_logarithmic"},
    )


@register("exponential_logarithms", "condense_log")
def condense_log(rng: random.Random, difficulty: str) -> Problem:
    """``log_b(x) + log_b(y) = log_b(xy)`` -- the product rule."""
    b = pick(rng, BASES)
    hi = {"easy": 6, "medium": 9, "hard": 12}[difficulty]
    x_val = rng.randint(2, hi)
    y_val = rng.randint(2, hi)

    return Problem(
        question_latex=rf"$\log_{{{b}}}({x_val}) + \log_{{{b}}}({y_val})$",
        answer_latex=rf"$\log_{{{b}}}({x_val * y_val})$",
        answer_expr=None,
        topic="exponential_logarithms",
        subskill="condense_log",
        difficulty=difficulty,
        verify={"kind": "condense_log"},
    )
