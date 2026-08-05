"""Quadratic equations, built backwards from their roots (or their vertex).

Choosing the roots -- or the vertex -- first and expanding to standard form
keeps every answer exact: no accidental repeated roots, no float arithmetic
anywhere. ``quadratic_formula`` deliberately rejects perfect-square
discriminants so its roots are genuinely irrational, the case that makes the
formula necessary rather than factoring.
"""

from __future__ import annotations

import random

import sympy as sp

from ..core.latexfmt import poly
from ..core.problem import Problem
from ..core.registry import register
from ..core.sampling import nonzero_int, pick

RANGES = {"easy": (1, 8), "medium": (2, 10), "hard": (2, 12)}
X = sp.Symbol("x")


def _mk_roots(a: int, b: int, c: int, r1, r2, subskill: str, difficulty: str) -> Problem:
    roots = sorted((sp.nsimplify(r1), sp.nsimplify(r2)), key=lambda v: sp.N(v))
    return Problem(
        question_latex=f"${poly([a, b, c])} = 0$",
        answer_latex=rf"$x = {sp.latex(roots[0])} \text{{ or }} x = {sp.latex(roots[1])}$",
        answer_expr=roots,
        topic="quadratics",
        subskill=subskill,
        difficulty=difficulty,
        verify={"kind": "solve_quadratic"},
    )


@register("quadratics", "solve_by_factoring")
def solve_by_factoring(rng: random.Random, difficulty: str) -> Problem:
    """``a*x^2 + b*x + c = 0``, factored from two chosen integer roots."""
    _, hi = RANGES[difficulty]
    r1 = nonzero_int(rng, -hi, hi)
    r2 = nonzero_int(rng, -hi, hi)
    while r2 == r1:
        r2 = nonzero_int(rng, -hi, hi)
    a = pick(rng, (1, 2, 3)) if difficulty != "easy" else 1

    b = -a * (r1 + r2)
    c = a * r1 * r2
    return _mk_roots(a, b, c, r1, r2, "solve_by_factoring", difficulty)


@register("quadratics", "quadratic_formula")
def quadratic_formula(rng: random.Random, difficulty: str) -> Problem:
    """``a*x^2 + b*x + c = 0`` with a non-perfect-square discriminant."""
    _, hi = RANGES[difficulty]
    a = pick(rng, (1, 2, 3))
    while True:
        b = nonzero_int(rng, -hi, hi)
        c = nonzero_int(rng, -hi, hi)
        disc = b * b - 4 * a * c
        if disc > 0 and not sp.sqrt(disc).is_integer:
            break
    roots = sp.solve(sp.Eq(a * X**2 + b * X + c, 0), X)
    return _mk_roots(a, b, c, roots[0], roots[1], "quadratic_formula", difficulty)


@register("quadratics", "find_vertex")
def find_vertex(rng: random.Random, difficulty: str) -> Problem:
    """``y = a(x - h)^2 + k`` expanded to standard form; find the vertex ``(h, k)``."""
    _, hi = RANGES[difficulty]
    a = pick(rng, (-3, -2, -1, 1, 2, 3))
    h = nonzero_int(rng, -hi, hi)
    k = nonzero_int(rng, -hi, hi)

    b = -2 * a * h
    c = a * h * h + k
    return Problem(
        question_latex=f"$y = {poly([a, b, c])}$",
        answer_latex=f"$({h}, {k})$",
        answer_expr=(sp.Integer(h), sp.Integer(k)),
        topic="quadratics",
        subskill="find_vertex",
        difficulty=difficulty,
        verify={"kind": "quadratic_vertex"},
    )
