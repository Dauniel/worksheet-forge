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

from ..core.latexfmt import coeff, linear, num, poly, terms
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
    """``a*x^2 + b*x + c = 0`` with a non-perfect-square discriminant.

    At the "hard" tier, roughly 30% of draws instead pick a *negative*
    discriminant -- the case where the formula reports "no real solutions"
    rather than a pair of irrational roots.
    """
    _, hi = RANGES[difficulty]
    a = pick(rng, (1, 2, 3))
    if difficulty == "hard" and rng.random() < 0.3:
        while True:
            b = nonzero_int(rng, -hi, hi)
            c = nonzero_int(rng, -hi, hi)
            if b * b - 4 * a * c < 0:
                break
        return Problem(
            question_latex=f"${poly([a, b, c])} = 0$",
            answer_latex=r"$\text{no real solutions}$",
            answer_expr="no real solutions",
            topic="quadratics",
            subskill="quadratic_formula",
            difficulty=difficulty,
            verify={"kind": "solve_quadratic_no_real"},
        )
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


@register("quadratics", "vertex_and_direction")
def vertex_and_direction(rng: random.Random, difficulty: str) -> Problem:
    """Like ``find_vertex``, but also states whether the parabola opens up
    (minimum) or down (maximum)."""
    _, hi = RANGES[difficulty]
    a = pick(rng, (-3, -2, -1, 1, 2, 3))
    h = nonzero_int(rng, -hi, hi)
    k = nonzero_int(rng, -hi, hi)
    b = -2 * a * h
    c = a * h * h + k
    direction = "maximum" if a < 0 else "minimum"
    return Problem(
        question_latex=f"$y = {poly([a, b, c])}$",
        answer_latex=rf"$({h}, {k})$, {direction}",
        answer_expr=(sp.Integer(h), sp.Integer(k), direction),
        topic="quadratics",
        subskill="vertex_and_direction",
        difficulty=difficulty,
        verify={"kind": "vertex_and_direction"},
    )


VFCS_A = {"easy": (-3, -2, 2, 3), "medium": (-4, -3, -2, 2, 3, 4),
          "hard": (-6, -5, -4, -3, 2, 3, 4, 5, 6)}
VFCS_HK = {"easy": (1, 6), "medium": (2, 9), "hard": (2, 12)}


@register("quadratics", "vertex_form_complete_square")
def vertex_form_complete_square(rng: random.Random, difficulty: str) -> Problem:
    """Standard form -> vertex form, built backwards from ``a``, ``h``, ``k``
    so the expansion is always exact: ``f(x) = -4x^2+24x-10 -> -4(x-3)^2+26``.
    """
    a = pick(rng, VFCS_A[difficulty])
    lo, hi = VFCS_HK[difficulty]
    h = nonzero_int(rng, -hi, hi)
    k = nonzero_int(rng, -hi, hi)
    b = -2 * a * h
    c = a * h * h + k

    inner = linear(1, -h)
    vertex = terms(f"{num(a)}({inner})^{{2}}", num(k))
    return Problem(
        question_latex=f"$f(x) = {poly([a, b, c])}$",
        answer_latex=f"$f(x) = {vertex}$",
        answer_expr=(sp.Integer(a), sp.Integer(h), sp.Integer(k)),
        topic="quadratics",
        subskill="vertex_form_complete_square",
        difficulty=difficulty,
        verify={"kind": "vertex_form_complete_square"},
    )


CTS_A = {"easy": (2, 3), "medium": (2, 3, 4, 5), "hard": (2, 3, 4, 5, 6)}
CTS_M = {"easy": (1, 5), "medium": (1, 8), "hard": (1, 10)}


@register("quadratics", "complete_the_square_blank")
def complete_the_square_blank(rng: random.Random, difficulty: str) -> Problem:
    """``ax^2+bx+c=0 -> a(x^2+(b/a)x+___) = -c+___``; state the pair of
    blanks. ``a`` and the linear coefficient are chosen so ``b/a`` is an even
    integer, which keeps the first blank an integer.
    """
    a = pick(rng, CTS_A[difficulty])
    mlo, mhi = CTS_M[difficulty]
    m = nonzero_int(rng, mlo, mhi) * rng.choice((-1, 1))
    b = 2 * a * m
    c = nonzero_int(rng, -10 * a, 10 * a)
    k = m * m
    right_blank = a * k

    inner_x = terms(r"x^{2}", coeff(2 * m, "x"))
    question = (
        rf"{poly([a, b, c])} = 0 \quad\Rightarrow\quad "
        rf"{a}\left({inner_x} + \_\_\_\_\right) = {num(-c)}+\_\_\_\_"
    )
    answer = rf"{k} \text{{ and }} {right_blank}"
    return Problem(
        question_latex=f"${question}$",
        answer_latex=f"${answer}$",
        answer_expr=(sp.Integer(k), sp.Integer(right_blank)),
        topic="quadratics",
        subskill="complete_the_square_blank",
        difficulty=difficulty,
        verify={"kind": "complete_square_blanks"},
    )
