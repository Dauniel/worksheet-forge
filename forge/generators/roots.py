"""Square roots, cube roots, and simplifying radicals (pre-algebra level).

Radicands stay in the low triple digits (<= 225, i.e. nothing past 15^2 or
6^3) so every value here is either a standard memorized square/cube or a
small radical simplification a student can sanity-check by hand.

``square_root`` and ``cube_root`` each draw from three structural forms:

  - bare:        sqrt(n^2) = n                    (no coefficient)
  - coefficient: k * sqrt(n^2) = k*n               (k >= 2, a minority case)
  - fraction:    sqrt(p^2/q^2) = p/q, p/q reduced  (no coefficient)

A leading coefficient is drawn on roughly 1/3 of items, never the majority --
bare and fraction forms (both "no leading coefficient") together make up
about 2/3. The fraction form is a real, standard pre-algebra root skill
(perfect-square/perfect-cube fractions), not padding: it is also what makes
the ~2/3-bare weighting possible without violating the anti-hardcoding
invariant. The base/radicand ranges alone are tiny -- only 4-5 memorable
perfect-cube bases exist under 216 -- so a naive "mostly bare" weighting would
dump most draws into an 8-10-item bucket and collide immediately. Splitting
the "no coefficient" 2/3 across two structurally different forms (bare
integer, reduced fraction) keeps the total reachable space wide even though
each individual bucket stays small. See the ranges below for the exact
reachable-space accounting.
"""

from __future__ import annotations

import math
import random

import sympy as sp

from ..core.latexfmt import coeff
from ..core.problem import Problem
from ..core.registry import register
from ..core.sampling import pick

# Bases square to at most 15^2 = 225 and cube to at most 6^3 = 216 -- both
# comfortably "low triple digits", per the standard memorized square/cube
# tables. Only the upper bound grows with difficulty; the coefficient and
# fraction forms below are what actually vary the challenge.
SQUARE_BASE = {"easy": (2, 12), "medium": (2, 14), "hard": (2, 15)}
CUBE_BASE = {"easy": (2, 5), "medium": (2, 5), "hard": (2, 6)}

# Style weights, shared by square_root and cube_root: P(bare) + P(coefficient)
# + P(fraction) = 1. Coefficient is deliberately the minority (~1/3); bare is
# kept a *smaller* share than "1 - coefficient" would suggest and fraction
# gets the rest, because the bare bucket (base x sign only, no coefficient or
# denominator to vary it) is the smallest reachable subspace of the three --
# weighting it any higher collides against the anti-hardcoding floor despite
# the total space being large enough on paper.
BARE_PROB = {"square_root": 0.22, "cube_root": 0.20}
COEF_PROB = 1 / 3  # same for both; the remainder goes to the fraction form

SQUARE_COEF_RANGE = {"easy": (2, 6), "medium": (2, 8), "hard": (2, 10)}
CUBE_COEF_RANGE = {"easy": (2, 9), "medium": (2, 10), "hard": (2, 12)}

# Fraction form: sqrt(p^2/q^2) = p/q (reduced), cbrt(p^3/q^3) = p/q (reduced).
# p and q are each bounded well inside the cap on their own (p^2, q^2 <= 225;
# p^3, q^3 <= 216), same discipline as the whole-number forms.
SQUARE_FRAC_Q = {"easy": (2, 3, 4), "medium": (2, 3, 4, 5), "hard": (2, 3, 4, 5, 6)}
SQUARE_FRAC_P_MAX = {"easy": 9, "medium": 11, "hard": 13}
CUBE_FRAC_Q = {"easy": (2, 3, 4), "medium": (2, 3, 4), "hard": (2, 3, 4, 5)}
# p^3 must stay <= 216 too, same as the whole-number cube base -- p can never
# exceed 6 regardless of tier (6^3 = 216 is already the ceiling).
CUBE_FRAC_P_MAX = {"easy": 5, "medium": 6, "hard": 6}

# sqrt(a^2 * b) -> a*sqrt(b): the PRODUCT a^2*b is capped, not the factors
# independently -- the coefficient bound is derived from whichever squarefree
# radicand b was drawn, so a^2*b can never land outside the cap regardless of
# how b and a combine.
#
# Note on variance: capping the product at 225 caps the *number of distinct
# products* too -- only 69 values of a^2*b with a >= 2 exist under 225 at
# all. A leading +/- sign (a real structural difficulty knob) doubles the
# reachable space per tier; without it, the medium tier's own bounds only
# reach ~40 distinct products, under the 50-distinct-in-100-seeds
# anti-hardcoding floor, and no amount of RNG tuning fixes a ceiling that's
# lower than the floor.
PRODUCT_CAP = 225
SQUAREFREE_MAX = {"easy": 18, "medium": 20, "hard": 24}
COEF_TIER_MAX = {"easy": 8, "medium": 9, "hard": 11}


def _is_squarefree(n: int) -> bool:
    i = 2
    while i * i <= n:
        if n % i == 0:
            n //= i
            if n % i == 0:
                return False
        i += 1
    return True


def _squarefree(rng: random.Random, hi: int) -> int:
    while True:
        n = rng.randint(2, hi)
        if _is_squarefree(n):
            return n


def _reduced_fraction(rng: random.Random, q_choices, p_max: int) -> tuple:
    """A reduced positive fraction p/q with q drawn from ``q_choices``."""
    q = pick(rng, q_choices)
    while True:
        p = rng.randint(1, p_max)
        if math.gcd(p, q) == 1:
            return p, q


def _mk(question: str, value, subskill: str, difficulty: str) -> Problem:
    return Problem(
        question_latex=f"${question}$",
        answer_latex=f"${sp.latex(value)}$",
        answer_expr=value,
        topic="roots",
        subskill=subskill,
        difficulty=difficulty,
        verify={"kind": "evaluate"},
    )


@register("roots", "square_root")
def square_root(rng: random.Random, difficulty: str) -> Problem:
    style = rng.random()
    lo, hi = SQUARE_BASE[difficulty]

    if style < BARE_PROB["square_root"]:
        n = rng.randint(lo, hi)
        sign = pick(rng, (1, -1))
        prefix = coeff(sign, "")
        question = rf"{prefix}\sqrt{{{n * n}}}"
        return _mk(question, sp.Integer(sign * n), "square_root", difficulty)

    if style < BARE_PROB["square_root"] + COEF_PROB:
        n = rng.randint(lo, hi)
        sign = pick(rng, (1, -1))
        k = rng.randint(*SQUARE_COEF_RANGE[difficulty])
        overall = sign * k
        prefix = coeff(overall, "")
        question = rf"{prefix}\sqrt{{{n * n}}}"
        return _mk(question, sp.Integer(overall * n), "square_root", difficulty)

    p, q = _reduced_fraction(rng, SQUARE_FRAC_Q[difficulty], SQUARE_FRAC_P_MAX[difficulty])
    sign = pick(rng, (1, -1))
    prefix = "-" if sign < 0 else ""
    question = rf"{prefix}\sqrt{{\dfrac{{{p * p}}}{{{q * q}}}}}"
    return _mk(question, sign * sp.Rational(p, q), "square_root", difficulty)


@register("roots", "cube_root")
def cube_root(rng: random.Random, difficulty: str) -> Problem:
    style = rng.random()
    lo, hi = CUBE_BASE[difficulty]

    if style < BARE_PROB["cube_root"]:
        n = rng.randint(lo, hi) * pick(rng, (1, -1))
        question = rf"\sqrt[3]{{{n ** 3}}}"
        return _mk(question, sp.Integer(n), "cube_root", difficulty)

    if style < BARE_PROB["cube_root"] + COEF_PROB:
        n = rng.randint(lo, hi) * pick(rng, (1, -1))
        k = rng.randint(*CUBE_COEF_RANGE[difficulty])
        prefix = coeff(k, "")
        question = rf"{prefix}\sqrt[3]{{{n ** 3}}}"
        return _mk(question, sp.Integer(k * n), "cube_root", difficulty)

    p, q = _reduced_fraction(rng, CUBE_FRAC_Q[difficulty], CUBE_FRAC_P_MAX[difficulty])
    p_signed = p * pick(rng, (1, -1))  # cube roots of negatives are real
    question = rf"\sqrt[3]{{\dfrac{{{p_signed ** 3}}}{{{q ** 3}}}}}"
    return _mk(question, sp.Rational(p_signed, q), "cube_root", difficulty)


@register("roots", "simplify_radical")
def simplify_radical(rng: random.Random, difficulty: str) -> Problem:
    b = _squarefree(rng, SQUAREFREE_MAX[difficulty])
    a_max = min(COEF_TIER_MAX[difficulty], math.isqrt(PRODUCT_CAP // b))
    a_max = max(a_max, 2)  # b's own range guarantees this in practice
    a = rng.randint(2, a_max)
    sign = pick(rng, (1, -1))
    k = a * a * b
    prefix = "-" if sign < 0 else ""
    question = rf"{prefix}\sqrt{{{k}}}"
    value = sign * a * sp.sqrt(b)
    return _mk(question, value, "simplify_radical", difficulty)
