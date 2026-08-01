"""Square roots, cube roots, and simplifying radicals (pre-algebra level).

Radicands stay in the low triple digits (<= 225, i.e. nothing past 15^2 or
6^3) so every value here is either a standard memorized square/cube or a
small radical simplification a student can sanity-check by hand.

``square_root`` and ``cube_root`` are deliberately plain: a bare radical of a
perfect square/cube, positive base only, no leading coefficient, no fraction
radicand, no sign. That is the whole problem -- nothing else is sampled.

This is a *known, accepted* small reachable space. Perfect squares <= 225
give only 14 possible bases (2..15) and perfect cubes <= 216 give only 5
(2..6); restricting further per difficulty tier (see the ranges below) makes
each tier's space smaller still. This intrinsically cannot clear the
generic anti-hardcoding variance floor (`tests/test_variance.py` normally
wants >=60% distinct values across 50 draws) -- no RNG tuning fixes a
ceiling that low. `square_root` and `cube_root` are listed in that test's
`SMALL_REACHABLE_SPACE` exemption table with their exact reachable counts;
the test still asserts they reach at/near that true ceiling and that no
single value dominates, so a generator that collapses onto a few favorites
is still caught.

``simplify_radical`` stays a wide, ordinary-variance generator: it draws a
squarefree radicand b and a coefficient a (a >= 2) with the product a^2*b
capped at 225, producing sqrt(a^2*b) -> a*sqrt(b). No sign, no fraction, no
leading coefficient beyond the structural `a` -- positive-only throughout.
"""

from __future__ import annotations

import math
import random

import sympy as sp

from ..core.problem import Problem
from ..core.registry import register

# Bases square to at most 15^2 = 225 and cube to at most 6^3 = 216 -- both
# comfortably "low triple digits", per the standard memorized square/cube
# tables. This is the *entire* sample space for these two subskills now
# that no coefficient/fraction/sign forms remain -- see the module
# docstring and tests/test_variance.py's SMALL_REACHABLE_SPACE table for the
# exact reachable-count accounting this implies.
SQUARE_BASE = {"easy": (2, 12), "medium": (2, 14), "hard": (2, 15)}
CUBE_BASE = {"easy": (2, 5), "medium": (2, 5), "hard": (2, 6)}

# sqrt(a^2 * b) -> a*sqrt(b): the PRODUCT a^2*b is capped, not the factors
# independently -- the coefficient bound is derived from whichever squarefree
# radicand b was drawn, so a^2*b can never land outside the cap regardless of
# how b and a combine.
# bmax/amax here are deliberately pushed close to what the 225 cap allows at
# all (72 distinct a^2*b products is the absolute ceiling for any a>=2,
# squarefree b -- see tests/test_generators.py's SMALL_REACHABLE_SPACE) so
# the fuzz/variance tests have the widest possible space to draw from.
PRODUCT_CAP = 225
SQUAREFREE_MAX = {"easy": 30, "medium": 45, "hard": 56}
COEF_TIER_MAX = {"easy": 8, "medium": 10, "hard": 11}


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
    lo, hi = SQUARE_BASE[difficulty]
    n = rng.randint(lo, hi)
    question = rf"\sqrt{{{n * n}}}"
    return _mk(question, sp.Integer(n), "square_root", difficulty)


@register("roots", "cube_root")
def cube_root(rng: random.Random, difficulty: str) -> Problem:
    lo, hi = CUBE_BASE[difficulty]
    n = rng.randint(lo, hi)
    question = rf"\sqrt[3]{{{n ** 3}}}"
    return _mk(question, sp.Integer(n), "cube_root", difficulty)


@register("roots", "simplify_radical")
def simplify_radical(rng: random.Random, difficulty: str) -> Problem:
    b = _squarefree(rng, SQUAREFREE_MAX[difficulty])
    a_max = min(COEF_TIER_MAX[difficulty], math.isqrt(PRODUCT_CAP // b))
    a_max = max(a_max, 2)  # b's own range guarantees this in practice
    a = rng.randint(2, a_max)
    k = a * a * b
    question = rf"\sqrt{{{k}}}"
    value = a * sp.sqrt(b)
    return _mk(question, value, "simplify_radical", difficulty)
