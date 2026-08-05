"""Quadratic equations, built backwards from their roots (or their vertex).

Choosing the roots -- or the vertex -- first and expanding to standard form
keeps every answer exact: no accidental repeated roots, no float arithmetic
anywhere. ``quadratic_formula`` deliberately rejects perfect-square
discriminants so its roots are genuinely irrational, the case that makes the
formula necessary rather than factoring.
"""

from __future__ import annotations

import random
from math import gcd

import sympy as sp

from ..core.latexfmt import poly
from ..core.problem import Problem
from ..core.registry import register
from ..core.sampling import nonzero_int, pick

RANGES = {"easy": (1, 8), "medium": (2, 10), "hard": (2, 12)}

# Denominator pairs for solve_by_factoring, giving a = m*p. Easy stays monic.
# Medium introduces a genuinely non-monic leading coefficient; hard raises it
# to at most 6. Six is the ceiling because the work the AC method actually
# does is scanning the factor pairs of a*c -- past |a*c| in the high hundreds
# the failure mode stops being "doesn't understand factoring" and becomes
# "miscounted a factor pair", which teaches nothing.
DENOMS = {
    "easy": ((1, 1),),
    "medium": ((1, 2), (1, 3), (2, 1), (3, 1)),
    "hard": ((1, 4), (2, 2), (1, 5), (1, 6), (2, 3), (3, 2), (4, 1), (6, 1)),
}
# Root numerators shrink as the denominators grow, so that c = n*q stays in
# the same range across tiers -- otherwise "hard" would just mean bigger
# arithmetic on top of the harder factorization.
NUMER_MAX = {"easy": 8, "medium": 7, "hard": 6}
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
    """``a*x^2 + b*x + c = 0``, expanded from ``(m*x - n)(p*x - q)``.

    The roots ``n/m`` and ``q/p`` are chosen first, then multiplied out, so
    every equation factors exactly over the rationals.

    Picking the two *denominators* rather than a bare leading coefficient is
    what makes a non-monic problem genuinely non-monic. Scaling a monic
    trinomial by ``a`` -- the obvious construction -- puts ``a`` into ``b``
    and ``c`` as well, so ``3x^2 - 15x - 72`` is just ``3(x^2 - 5x - 24)``
    and a student divides it away without ever using the AC method. Here
    ``a = m*p`` while ``c = n*q``, and the ``gcd`` check below rejects the
    draws where a common factor shows up anyway.
    """
    hi = NUMER_MAX[difficulty]
    while True:
        m, p = pick(rng, DENOMS[difficulty])
        n = nonzero_int(rng, -hi, hi)
        q = nonzero_int(rng, -hi, hi)
        # Roots must already be in lowest terms, or the printed leading
        # coefficient is not the one the student has to factor around.
        if gcd(abs(n), m) != 1 or gcd(abs(q), p) != 1:
            continue
        # (m*x - n)(p*x - q)
        a, b, c = m * p, -(m * q + n * p), n * q
        if sp.Rational(n, m) == sp.Rational(q, p):
            continue  # distinct roots only: no repeated-root factoring
        if gcd(a, gcd(abs(b), abs(c))) != 1:
            continue  # a common factor would collapse this back to monic
        return _mk_roots(
            a, b, c, sp.Rational(n, m), sp.Rational(q, p),
            "solve_by_factoring", difficulty,
        )


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
