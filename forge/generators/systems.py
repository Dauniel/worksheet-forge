"""Systems of two linear equations, built backwards from the intersection point.

Choosing ``(x_sol, y_sol)`` first and deriving every constant from it keeps
every system's solution exact by construction, and lets the "classify" cases
(no solution / infinitely many) be built exactly rather than stumbled into.
"""

from __future__ import annotations

import random

import sympy as sp

from ..core.latexfmt import coeff, linear, num, terms
from ..core.problem import Problem
from ..core.registry import register
from ..core.sampling import nonzero_int

RANGES = {"easy": (1, 6), "medium": (2, 9), "hard": (2, 12)}


def _std_form(a: int, b: int, c: int) -> str:
    """``a*x + b*y = c`` with correctly signed, never-``1x``/``1y`` terms."""
    return f"{terms(coeff(a, 'x'), coeff(b, 'y'))} = {num(c)}"


def _cases(eq1: str, eq2: str) -> str:
    return rf"$\begin{{cases}} {eq1} \\ {eq2} \end{{cases}}$"


def _mk(eq1: str, eq2: str, x_sol: int, y_sol: int, subskill: str, difficulty: str) -> Problem:
    return Problem(
        question_latex=_cases(eq1, eq2),
        answer_latex=rf"$x = {x_sol}, \ y = {y_sol}$",
        answer_expr=(sp.Integer(x_sol), sp.Integer(y_sol)),
        topic="systems",
        subskill=subskill,
        difficulty=difficulty,
        verify={"kind": "solve_system"},
    )


@register("systems", "substitution")
def substitution(rng: random.Random, difficulty: str) -> Problem:
    """One equation pre-solved for ``y``; the other in standard form."""
    _, hi = RANGES[difficulty]
    x_sol = nonzero_int(rng, -hi, hi)
    y_sol = nonzero_int(rng, -hi, hi)

    m1 = nonzero_int(rng, -min(hi, 6), min(hi, 6))
    b1 = y_sol - m1 * x_sol
    eq1 = f"y = {linear(m1, b1)}"

    a2 = nonzero_int(rng, 1, hi)
    b2 = nonzero_int(rng, -hi, hi)
    while a2 + b2 * m1 == 0:  # same slope as eq1 -> no unique solution
        b2 = nonzero_int(rng, -hi, hi)
    c2 = a2 * x_sol + b2 * y_sol
    eq2 = _std_form(a2, b2, c2)

    return _mk(eq1, eq2, x_sol, y_sol, "substitution", difficulty)


@register("systems", "elimination")
def elimination(rng: random.Random, difficulty: str) -> Problem:
    """Both equations in standard form; coefficients are unconstrained beyond
    guaranteeing a unique solution, so a student picks whichever variable
    eliminates more cleanly after scaling."""
    _, hi = RANGES[difficulty]
    x_sol = nonzero_int(rng, -hi, hi)
    y_sol = nonzero_int(rng, -hi, hi)

    a1 = nonzero_int(rng, 1, hi)
    b1 = nonzero_int(rng, -hi, hi)
    a2 = nonzero_int(rng, -hi, hi)
    b2 = nonzero_int(rng, -hi, hi)
    while a1 * b2 == a2 * b1:  # dependent/parallel -> not a unique solution
        a2 = nonzero_int(rng, -hi, hi)
        b2 = nonzero_int(rng, -hi, hi)

    c1 = a1 * x_sol + b1 * y_sol
    c2 = a2 * x_sol + b2 * y_sol
    eq1 = _std_form(a1, b1, c1)
    eq2 = _std_form(a2, b2, c2)

    return _mk(eq1, eq2, x_sol, y_sol, "elimination", difficulty)


@register("systems", "classify")
def classify(rng: random.Random, difficulty: str) -> Problem:
    """Decide whether a system has one solution, no solution, or infinitely
    many -- each case built exactly, never inferred after the fact.

    The no-solution and infinite-solution cases both scale equation 1 by an
    integer ``k`` to get equation 2's left side; they differ only in whether
    the constant is scaled by the same ``k`` (infinite, same line) or offset
    (none, parallel but distinct).
    """
    _, hi = RANGES[difficulty]
    hi = min(hi, 6)  # keeps post-scaling coefficients on a worksheet-sized scale
    kind = rng.choice(("one", "none", "infinite"))

    a1 = nonzero_int(rng, 1, hi)
    b1 = nonzero_int(rng, -hi, hi)

    if kind == "one":
        x_sol = nonzero_int(rng, -hi, hi)
        y_sol = nonzero_int(rng, -hi, hi)
        a2 = nonzero_int(rng, -hi, hi)
        b2 = nonzero_int(rng, -hi, hi)
        while a1 * b2 == a2 * b1:
            a2 = nonzero_int(rng, -hi, hi)
            b2 = nonzero_int(rng, -hi, hi)
        c1 = a1 * x_sol + b1 * y_sol
        c2 = a2 * x_sol + b2 * y_sol
        answer = rf"$\text{{One solution: }} ({x_sol}, {y_sol})$"
    else:
        k = rng.choice((-3, -2, 2, 3))
        a2, b2 = k * a1, k * b1
        c1 = nonzero_int(rng, -hi, hi)
        if kind == "none":
            offset = nonzero_int(rng, 1, hi)
            c2 = k * c1 + offset
            answer = r"$\text{No solution}$"
        else:
            c2 = k * c1
            answer = r"$\text{Infinitely many solutions}$"

    eq1 = _std_form(a1, b1, c1)
    eq2 = _std_form(a2, b2, c2)

    return Problem(
        question_latex=_cases(eq1, eq2),
        answer_latex=answer,
        answer_expr=kind,
        topic="systems",
        subskill="classify",
        difficulty=difficulty,
        verify={"kind": "classify_system"},
    )
