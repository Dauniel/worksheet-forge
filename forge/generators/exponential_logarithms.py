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


GROWTH_BASE = {"easy": (2, 3), "medium": (2, 5), "hard": (2, 8)}
GROWTH_START = {"easy": (2, 20), "medium": (3, 60), "hard": (5, 200)}
GROWTH_STEPS = {"easy": (2, 4), "medium": (2, 6), "hard": (3, 8)}


@register("exponential_logarithms", "growth_decay")
def growth_decay(rng: random.Random, difficulty: str) -> Problem:
    """Whole-number exponential growth or decay after n steps.

    Growth multiplies by an integer factor; decay halves (or thirds) from a
    starting amount chosen as an exact multiple of the factor to the power of
    n, so the answer is a whole number rather than a rounded decimal.
    """
    import sympy as _sp

    factor = rng.randint(*GROWTH_BASE[difficulty])
    steps = rng.randint(*GROWTH_STEPS[difficulty])
    unit = pick(rng, ("hours", "days", "weeks", "years"))
    thing = pick(rng, ("bacteria", "cells", "users", "followers", "plants"))

    if rng.random() < 0.5:
        start = rng.randint(*GROWTH_START[difficulty])
        value = start * factor**steps
        question = (
            f"A population of ${start}$ {thing} multiplies by ${factor}$ every "
            f"{unit[:-1]}. How many are there after ${steps}$ {unit}?"
        )
    else:
        # Decay: start from a multiple of factor^steps so every step is exact.
        end = rng.randint(1, max(2, GROWTH_START[difficulty][1] // 4))
        start = end * factor**steps
        value = end
        question = (
            f"A sample of ${start}$ {thing} is divided by ${factor}$ every "
            f"{unit[:-1]}. How many remain after ${steps}$ {unit}?"
        )
    return Problem(
        question_latex=question,
        answer_latex=f"${value}$",
        answer_expr=_sp.Integer(value),
        topic="exponential_logarithms",
        subskill="growth_decay",
        difficulty=difficulty,
        verify={"kind": "growth_decay"},
    )
