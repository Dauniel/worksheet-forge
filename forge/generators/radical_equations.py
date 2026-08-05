"""Radical equations, solved by isolating the radical and squaring.

Every problem is built backwards from a chosen non-negative value for the
radical itself, so the intended solution is always exact. ``check_extraneous``
is the one case where squaring can introduce a second algebraic root that
fails the original equation -- sympy's own ``solve`` already filters those
out, so construction retries until exactly one root survives, guaranteeing
the printed answer is unambiguous.
"""

from __future__ import annotations

import random

import sympy as sp

from ..core.latexfmt import linear, num, terms
from ..core.problem import Problem
from ..core.registry import register
from ..core.sampling import nonzero_int

RANGES = {"easy": (1, 8), "medium": (2, 10), "hard": (2, 12)}
X = sp.Symbol("x")


def _mk(question: str, x_sol, subskill: str, difficulty: str) -> Problem:
    value = sp.nsimplify(x_sol)
    lhs, rhs = question.split("=", 1)
    return Problem(
        question_latex=f"${question}$",
        answer_latex=f"$x = {sp.latex(value)}$",
        answer_expr=value,
        topic="radical_equations",
        subskill=subskill,
        difficulty=difficulty,
        verify={"kind": "solve", "var": "x", "lhs": lhs.strip(), "rhs": rhs.strip()},
    )


@register("radical_equations", "basic")
def basic(rng: random.Random, difficulty: str) -> Problem:
    """``sqrt(a x + b) = c``, with ``c`` non-negative so there's always
    exactly one solution."""
    _, hi = RANGES[difficulty]
    x_sol = nonzero_int(rng, -hi, hi)
    c = rng.randint(1, hi)
    a = nonzero_int(rng, 1, min(hi, 9))
    b = c * c - a * x_sol
    question = rf"\sqrt{{{linear(a, b)}}} = {c}"
    return _mk(question, x_sol, "basic", difficulty)


@register("radical_equations", "multi_step")
def multi_step(rng: random.Random, difficulty: str) -> Problem:
    """``k*sqrt(a x + b) + m = c`` -- the radical must be isolated before squaring."""
    _, hi = RANGES[difficulty]
    x_sol = nonzero_int(rng, -hi, hi)
    t = rng.randint(1, min(hi, 9))  # value of the radical itself
    k = nonzero_int(rng, 1, min(hi, 5))
    m = nonzero_int(rng, -hi, hi)
    c = k * t + m
    a = nonzero_int(rng, 1, min(hi, 9))
    b = t * t - a * x_sol

    prefix = "" if k == 1 else str(k)
    lhs = terms(rf"{prefix}\sqrt{{{linear(a, b)}}}", num(m))
    question = f"{lhs} = {c}"
    return _mk(question, x_sol, "multi_step", difficulty)


@register("radical_equations", "check_extraneous")
def check_extraneous(rng: random.Random, difficulty: str) -> Problem:
    """``sqrt(a x + b) = m x + k`` -- squaring can introduce an extraneous
    root; retry until exactly one algebraic solution survives sympy's own
    domain check."""
    _, hi = RANGES[difficulty]
    while True:
        t = rng.randint(0, hi)
        m = nonzero_int(rng, -hi, hi)
        x_sol = nonzero_int(rng, -hi, hi)
        k = t - m * x_sol
        a = nonzero_int(rng, 1, min(hi, 9))
        b = t * t - a * x_sol
        sols = sp.solve(sp.Eq(sp.sqrt(a * X + b), m * X + k), X)
        if len(sols) == 1 and sols[0] == x_sol:
            break

    question = rf"\sqrt{{{linear(a, b)}}} = {linear(m, k)}"
    return _mk(question, x_sol, "check_extraneous", difficulty)
