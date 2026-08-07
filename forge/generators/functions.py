"""Inverse functions, composition, and transformations of a parent function.

Every problem is built from the pieces that make the answer exact: an inverse
is drawn from a slope that divides cleanly, a composition is expanded by
sympy, and a transformation is applied to a named parent function rather than
described in prose.

Transformations are stated as an equation to write, not a sentence to
describe. "Shifted right 3 and up 2" as an *answer* cannot be checked
symbolically; ``g(x) = (x - 3)^2 + 2`` can.
"""

from __future__ import annotations

import random

import sympy as sp

from ..core.latexfmt import coeff, linear, num, poly, terms
from ..core.problem import Problem
from ..core.registry import register
from ..core.sampling import nonzero_int, pick

X = sp.Symbol("x")
RANGES = {"easy": (1, 6), "medium": (2, 9), "hard": (2, 12)}
# Explicit per-tier bands rather than min(hi, N) caps: a cap that is smaller
# than both medium and hard silently collapses the two tiers into one, which
# is exactly what tests/test_variance.py's tier-collapse guard catches.
SLOPE = {"easy": (2, 7), "medium": (2, 10), "hard": (3, 14)}
INTERCEPT = {"easy": 7, "medium": 10, "hard": 14}
SHIFT = {"easy": 5, "medium": 9, "hard": 14}
STRETCH = {"easy": (1, 1), "medium": (2, 4), "hard": (2, 7)}
# Parent functions a transformation can act on, as (name, expression builder).
PARENTS = {
    "x^{2}": lambda e: e**2,
    "x^{3}": lambda e: e**3,
    "|x|": lambda e: sp.Abs(e),
}


def _mk(question: str, answer: str, answer_expr, subskill: str, difficulty: str,
        kind: str = "simplify") -> Problem:
    return Problem(
        question_latex=f"${question}$",
        answer_latex=f"${answer}$",
        answer_expr=answer_expr,
        topic="functions",
        subskill=subskill,
        difficulty=difficulty,
        verify={"kind": kind},
    )


@register("functions", "inverse_linear")
def inverse_linear(rng: random.Random, difficulty: str) -> Problem:
    """``f(x) = mx + b`` -> ``f^-1(x) = (x - b)/m``.

    ``b`` is drawn as a multiple of ``m`` so the inverse has integer
    coefficients: (x - b)/m stays tidy and the answer needs no nested
    fraction.
    """
    m = nonzero_int(rng, *SLOPE[difficulty])
    span = INTERCEPT[difficulty]
    b = m * nonzero_int(rng, -span, span)

    question = f"f(x) = {linear(m, b)}"
    # f^-1(x) = x/m - b/m, with b/m an exact integer by construction
    inverse = X / m - sp.Integer(b) / m
    answer = rf"f^{{-1}}(x) = \dfrac{{{linear(1, -b)}}}{{{m}}}"
    return Problem(
        question_latex=f"${question}$",
        answer_latex=f"${answer}$",
        answer_expr=inverse,
        topic="functions",
        subskill="inverse_linear",
        difficulty=difficulty,
        verify={"kind": "inverse_function"},
    )


@register("functions", "composition")
def composition(rng: random.Random, difficulty: str) -> Problem:
    """``f(g(x))`` for two linear functions, expanded.

    At hard the inner function is quadratic, which is where students stop
    being able to do it by inspection.
    """
    _, hi = RANGES[difficulty]
    a, b = nonzero_int(rng, 1, min(hi, 6)), nonzero_int(rng, -hi, hi)
    c, d = nonzero_int(rng, 1, min(hi, 6)), nonzero_int(rng, -hi, hi)

    if difficulty == "hard":
        g_expr = c * X**2 + d
        g_text = poly([c, 0, d])
    else:
        g_expr = c * X + d
        g_text = linear(c, d)

    f_text = linear(a, b)
    result = sp.expand(a * g_expr + b)
    degree = sp.degree(result, X)
    coeffs = [int(result.coeff(X, k)) for k in range(degree, -1, -1)]

    question = rf"f(x) = {f_text}, \quad g(x) = {g_text}, \quad f(g(x))"
    return _mk(question, poly(coeffs), result, "composition", difficulty,
               kind="composition")


@register("functions", "transformation_equation")
def transformation_equation(rng: random.Random, difficulty: str) -> Problem:
    """Apply a stated shift/stretch/reflection to a parent function.

    The answer is the transformed *equation*, which sympy can check, rather
    than a sentence describing the motion, which it cannot.
    """
    name = pick(rng, tuple(PARENTS))
    build = PARENTS[name]

    span = SHIFT[difficulty]
    h = nonzero_int(rng, -span, span)   # horizontal shift
    k = nonzero_int(rng, -span, span)   # vertical shift
    a = 1
    lo_a, hi_a = STRETCH[difficulty]
    if hi_a > 1:
        a = nonzero_int(rng, lo_a, hi_a)
        if rng.random() < 0.4:
            a = -a

    inner = X - h
    expr = sp.expand(a * build(inner) + k)

    inner_text = linear(1, -h)
    body = name.replace("x", f"({inner_text})")
    scaled = body if a == 1 else f"{coeff(a, '')}{body}"
    answer = terms(scaled, num(k))

    moves = []
    moves.append(f"shifted right {h}" if h > 0 else f"shifted left {-h}")
    if a != 1:
        if a < 0:
            moves.append("reflected over the $x$-axis")
        if abs(a) != 1:
            moves.append(f"vertically stretched by {abs(a)}")
    moves.append(f"shifted up {k}" if k > 0 else f"shifted down {-k}")
    description = ", ".join(moves)

    question = (
        f"The parent function ${name}$ is transformed as follows: "
        f"{description}. "
        f"Write the equation of the transformed function."
    )
    return Problem(
        question_latex=question,
        answer_latex=f"$g(x) = {answer}$",
        answer_expr=expr,
        topic="functions",
        subskill="transformation_equation",
        difficulty=difficulty,
        verify={"kind": "transformation"},
    )
