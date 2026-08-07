"""Polynomial multiplication and factoring.

Verified by re-expanding the printed question and the printed answer with
sympy and requiring they're algebraically identical -- the existing
``simplify`` strategy already does exactly that, so no new verify code is
needed here.
"""

from __future__ import annotations

import random

import sympy as sp

from ..core.latexfmt import coeff, linear, num, poly, terms
from ..core.problem import Problem
from ..core.registry import register
from ..core.sampling import nonzero_int, pick

RANGES = {"easy": (1, 6), "medium": (2, 9), "hard": (2, 12)}
X = sp.Symbol("x")


def _mk(question: str, answer: str, answer_expr, subskill: str, difficulty: str) -> Problem:
    return Problem(
        question_latex=f"${question}$",
        answer_latex=f"${answer}$",
        answer_expr=answer_expr,
        topic="polynomials",
        subskill=subskill,
        difficulty=difficulty,
        verify={"kind": "simplify"},
    )


@register("polynomials", "multiply_binomials")
def multiply_binomials(rng: random.Random, difficulty: str) -> Problem:
    """``(a1 x + b1)(a2 x + b2)``, expanded via FOIL."""
    _, hi = RANGES[difficulty]
    a1 = nonzero_int(rng, 1, min(hi, 5))
    a2 = nonzero_int(rng, 1, min(hi, 5))
    b1 = nonzero_int(rng, -hi, hi)
    b2 = nonzero_int(rng, -hi, hi)

    question = f"({linear(a1, b1)})({linear(a2, b2)})"
    c2, c1, c0 = a1 * a2, a1 * b2 + a2 * b1, b1 * b2
    answer_expr = c2 * X**2 + c1 * X + c0
    return _mk(question, poly([c2, c1, c0]), answer_expr, "multiply_binomials", difficulty)


@register("polynomials", "factor_trinomial")
def factor_trinomial(rng: random.Random, difficulty: str) -> Problem:
    """``x^2 + bx + c``, factored from two chosen integer roots ``p, q``."""
    _, hi = RANGES[difficulty]
    p = nonzero_int(rng, -hi, hi)
    q = nonzero_int(rng, -hi, hi)
    while q == p:
        q = nonzero_int(rng, -hi, hi)
    p, q = sorted((p, q))

    b, c = p + q, p * q
    question = poly([1, b, c])
    answer = f"({linear(1, p)})({linear(1, q)})"
    answer_expr = (X + p) * (X + q)
    return _mk(question, answer, answer_expr, "factor_trinomial", difficulty)


DIFF_SQ_HI = {"easy": 50, "medium": 55, "hard": 65}


@register("polynomials", "difference_of_squares")
def difference_of_squares(rng: random.Random, difficulty: str) -> Problem:
    """``(sx)^2 - r^2``, factored as ``(sx - r)(sx + r)``.

    ``s`` is locked to 1 at "easy" so the leading coefficient stays plain
    while a student is first learning the pattern; ``r``'s range is widened
    well past the other subskills' to compensate, since it's then the only
    degree of freedom left at that tier.
    """
    hi = DIFF_SQ_HI[difficulty]
    r = nonzero_int(rng, 1, hi)
    s = pick(rng, (1, 2, 3)) if difficulty != "easy" else 1

    question = poly([s * s, 0, -r * r])
    lead = coeff(s, "x")
    answer = f"({terms(lead, num(-r))})({terms(lead, num(r))})"
    answer_expr = (s * X - r) * (s * X + r)
    return _mk(question, answer, answer_expr, "difference_of_squares", difficulty)


@register("polynomials", "synthetic_division")
def synthetic_division(rng: random.Random, difficulty: str) -> Problem:
    """Divide a cubic (or quartic at hard) by ``x - r``, exactly.

    Built backwards: pick the quotient and the root, multiply to get the
    dividend. That forces a zero remainder, which keeps the answer a clean
    polynomial -- and lets the existing ``simplify`` strategy verify it, since
    the printed question is then a rational expression algebraically equal to
    the printed quotient.
    """
    _, hi = RANGES[difficulty]
    degree = 3 if difficulty == "hard" else 2
    quotient = [nonzero_int(rng, 1, min(hi, 4))]
    quotient += [nonzero_int(rng, -hi, hi) for _ in range(degree)]
    r = nonzero_int(rng, -min(hi, 6), min(hi, 6))

    q_expr = sum(c * X ** (degree - i) for i, c in enumerate(quotient))
    dividend = sp.expand((X - r) * q_expr)
    dividend_coeffs = [int(dividend.coeff(X, k)) for k in range(degree + 1, -1, -1)]

    question = rf"\dfrac{{{poly(dividend_coeffs)}}}{{{linear(1, -r)}}}"
    return _mk(question, poly(quotient), q_expr, "synthetic_division", difficulty)


@register("polynomials", "factor_by_grouping")
def factor_by_grouping(rng: random.Random, difficulty: str) -> Problem:
    """``x^3 + ax^2 + bx + ab`` factors as ``(x + a)(x^2 + b)``.

    Built from the two factors outward, so the grouping always works -- a
    randomly drawn cubic almost never factors over the integers.
    """
    _, hi = RANGES[difficulty]
    a = nonzero_int(rng, -hi, hi)
    # b may be negative: x^3 + ax^2 - bx - ab groups just as cleanly, and
    # allowing the sign doubles a space that was small enough to make the
    # same first problem recur across seeds.
    b = nonzero_int(rng, -hi, hi)
    lead = nonzero_int(rng, 2, 3) if difficulty == "hard" else 1

    expanded = sp.expand((X + a) * (lead * X**2 + b))
    coeffs = [int(expanded.coeff(X, k)) for k in range(3, -1, -1)]
    answer = f"({linear(1, a)})({poly([lead, 0, b])})"
    return _mk(poly(coeffs), answer, expanded, "factor_by_grouping", difficulty)
