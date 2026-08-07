"""Rational expressions, built backwards from the factor meant to cancel.

Every problem starts from the piece that survives simplification, then
multiplies in a shared factor -- so the intended cancellation always exists
and is exact, never approximate or accidental.
"""

from __future__ import annotations

import random

from ..core.latexfmt import coeff, linear, poly
from ..core.problem import Problem
from ..core.registry import register
from ..core.sampling import nonzero_int, pick

RANGES = {"easy": (1, 6), "medium": (2, 9), "hard": (2, 12)}


def _factor(k: int, root: int) -> str:
    """``k*(x - root)``, with ``k`` folded away when it's 1."""
    body = linear(1, -root)
    if k == 1:
        return body
    prefix = coeff(k, "")
    return f"{prefix}({body})"


@register("rational_expressions", "simplify")
def simplify(rng: random.Random, difficulty: str) -> Problem:
    """``k(x-m)(x-p)`` over ``k(x-m)`` -- the shared factor cancels."""
    _, hi = RANGES[difficulty]
    m = nonzero_int(rng, -hi, hi)
    p = nonzero_int(rng, -hi, hi)
    while p == m:
        p = nonzero_int(rng, -hi, hi)
    k = pick(rng, (1, 2, 3)) if difficulty != "easy" else 1

    numer_str = poly([k, -k * (m + p), k * m * p])
    denom_str = _factor(k, m)
    answer = linear(1, -p)

    return Problem(
        question_latex=rf"$\dfrac{{{numer_str}}}{{{denom_str}}}$",
        answer_latex=rf"${answer}, \ x \neq {m}$",
        answer_expr=None,
        topic="rational_expressions",
        subskill="simplify",
        difficulty=difficulty,
        verify={"kind": "simplify_rational", "answer_check": None},
    )


@register("rational_expressions", "multiply")
def multiply(rng: random.Random, difficulty: str) -> Problem:
    """``(x-m)/[k(x-n)] * [k(x-n)]/(x-p)`` -- both ``k`` and ``(x-n)`` cancel,
    leaving ``(x-m)/(x-p)`` exactly."""
    _, hi = RANGES[difficulty]
    m = nonzero_int(rng, -hi, hi)
    n = nonzero_int(rng, -hi, hi)
    p = nonzero_int(rng, -hi, hi)
    while len({m, n, p}) < 3:
        m = nonzero_int(rng, -hi, hi)
        n = nonzero_int(rng, -hi, hi)
        p = nonzero_int(rng, -hi, hi)
    k = pick(rng, (1, 2, 3)) if difficulty != "easy" else 1

    num1, den1 = linear(1, -m), _factor(k, n)
    num2, den2 = _factor(k, n), linear(1, -p)
    answer = rf"\dfrac{{{linear(1, -m)}}}{{{linear(1, -p)}}}"

    return Problem(
        question_latex=rf"$\dfrac{{{num1}}}{{{den1}}} \cdot \dfrac{{{num2}}}{{{den2}}}$",
        answer_latex=f"${answer}$",
        answer_expr=None,
        topic="rational_expressions",
        subskill="multiply",
        difficulty=difficulty,
        verify={"kind": "multiply_rational", "answer_check": None},
    )


X = __import__("sympy").Symbol("x")


@register("rational_expressions", "solve_rational_equation")
def solve_rational_equation(rng: random.Random, difficulty: str) -> Problem:
    """``a/(x - p) = b/(x - q)``, cross-multiplied to a linear equation.

    Built backwards from the solution: pick ``x_sol`` and the two excluded
    values, then derive coefficients that make ``x_sol`` satisfy the equation.
    ``x_sol`` is kept clear of both excluded values, so no problem is secretly
    an extraneous-solution trap -- that case needs its own directions and its
    own key ("no solution"), which is a different subskill.
    """
    import sympy as sp

    _, hi = RANGES[difficulty]
    p_ex = nonzero_int(rng, -hi, hi)
    q_ex = nonzero_int(rng, -hi, hi)
    while q_ex == p_ex:
        q_ex = nonzero_int(rng, -hi, hi)

    x_sol = nonzero_int(rng, -hi, hi)
    while x_sol in (p_ex, q_ex):
        x_sol = nonzero_int(rng, -hi, hi)

    # a*(x_sol - q) = b*(x_sol - p) is satisfied by a = k*(x_sol - p),
    # b = k*(x_sol - q) -- exact integers, no fractions introduced.
    k = nonzero_int(rng, 1, min(hi, 4))
    a = k * (x_sol - p_ex)
    b = k * (x_sol - q_ex)
    if a == 0 or b == 0:  # would collapse a side to zero
        a, b = a or k, b or k

    lhs = rf"\dfrac{{{a}}}{{{linear(1, -p_ex)}}}"
    rhs = rf"\dfrac{{{b}}}{{{linear(1, -q_ex)}}}"
    return Problem(
        question_latex=f"${lhs} = {rhs}$",
        answer_latex=f"$x = {x_sol}$",
        answer_expr=sp.Integer(x_sol),
        topic="rational_expressions",
        subskill="solve_rational_equation",
        difficulty=difficulty,
        verify={"kind": "solve", "var": "x", "lhs": lhs, "rhs": rhs},
    )
