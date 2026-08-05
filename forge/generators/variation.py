"""Direct and inverse variation word problems.

Built backwards from the constant of variation: for direct variation,
``y1 = k*x1`` and ``y2 = k*x2`` are both exact by construction. For inverse
variation, ``x2`` is drawn from the actual divisors of ``x1*y1`` so
``y2 = (x1*y1)/x2`` is always a whole number, never a rounded answer.
"""

from __future__ import annotations

import random

import sympy as sp

from ..core.problem import Problem
from ..core.registry import register
from ..core.sampling import pick

SCALE = {"easy": (2, 9), "medium": (3, 12), "hard": (4, 18)}


def _mk(text: str, lhs: str, rhs: str, value, subskill: str, difficulty: str, quantities) -> Problem:
    value = sp.nsimplify(value)
    return Problem(
        question_latex=text,
        answer_latex=f"$y = {sp.latex(value)}$",
        answer_expr=value,
        topic="variation",
        subskill=subskill,
        difficulty=difficulty,
        verify={
            "kind": "word",
            "var": "x",
            "lhs": lhs,
            "rhs": rhs,
            "quantities": quantities,
            "prose": True,
        },
    )


@register("variation", "direct_variation")
def direct_variation(rng: random.Random, difficulty: str) -> Problem:
    _, hi = SCALE[difficulty]
    k = rng.randint(2, hi)
    x1 = rng.randint(2, hi)
    x2 = x1
    while x2 == x1:
        x2 = rng.randint(2, hi)
    y1, y2 = k * x1, k * x2

    text = (
        rf"$y$ varies directly with $x$. If $y = {y1}$ when $x = {x1}$, "
        rf"find $y$ when $x = {x2}$."
    )
    return _mk(text, f"{x1}*x", str(y1 * x2), y2, "direct_variation", difficulty, [x1, y1, x2])


def _divisors_excluding(n: int, exclude: int):
    return [d for d in range(1, n + 1) if n % d == 0 and d != exclude]


@register("variation", "inverse_variation")
def inverse_variation(rng: random.Random, difficulty: str) -> Problem:
    _, hi = SCALE[difficulty]
    x1 = rng.randint(2, hi)
    y1 = rng.randint(2, hi)
    k = x1 * y1
    x2 = pick(rng, _divisors_excluding(k, x1))
    y2 = k // x2

    text = (
        rf"$y$ varies inversely with $x$. If $y = {y1}$ when $x = {x1}$, "
        rf"find $y$ when $x = {x2}$."
    )
    return _mk(text, f"{x2}*x", str(k), y2, "inverse_variation", difficulty, [x1, y1, x2])
