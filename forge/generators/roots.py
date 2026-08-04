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

``simplify_cube_radical`` is the cube-root analogue of ``simplify_radical``:
it draws a cube-free radicand b and a coefficient a (a >= 2), caps the
product a^3*b (not the factors independently, per tier -- see
`PRODUCT_CAP_CUBE`), and produces cbrt(a^3*b) -> a*cbrt(b). Cube-free means no
prime divides b three or more times, so b may still be divisible by a square
(cbrt(4) and cbrt(9) are already fully simplified) -- that is what keeps the
radicand space wide enough to clear the ordinary 60%-distinct variance floor
at every tier with no `SMALL_REACHABLE_SPACE` exemption.
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

# cbrt(a^3 * b) -> a*cbrt(b): the PRODUCT a^3*b is capped, not the factors
# independently -- the radicand b is drawn no larger than cap//8 so that the
# smallest legal coefficient (a = 2) already fits under the cap, and a's upper
# bound is then derived from whichever b came out. The cap therefore holds for
# every (a, b) pair the generator can produce; it is never clamped past.
# Radicands stay in the low hundreds so the prime factorization is work a
# student can do by hand.
PRODUCT_CAP_CUBE = {"easy": 400, "medium": 550, "hard": 700}
CUBEFREE_MAX = {"easy": 80, "medium": 120, "hard": 180}
COEF_TIER_MAX_CUBE = {"easy": 7, "medium": 9, "hard": 11}


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


def _is_cubefree(n: int) -> bool:
    """No prime divides ``n`` three or more times.

    Weaker than :func:`_is_squarefree` on purpose -- 4, 9, 12 and 50 are all
    legal cube-radicands (``cbrt(4)`` cannot be simplified further), and
    excluding them would throw away most of the sample space.
    """
    i = 2
    while i * i <= n:
        count = 0
        while n % i == 0:
            n //= i
            count += 1
            if count >= 3:
                return False
        i += 1
    return True


def _cubefree(rng: random.Random, hi: int) -> int:
    while True:
        n = rng.randint(2, hi)
        if _is_cubefree(n):
            return n


def _icbrt(n: int) -> int:
    """Integer cube root: largest r with r**3 <= n (n >= 0)."""
    if n < 0:
        raise ValueError("n must be non-negative")
    r = round(n ** (1 / 3))
    while r ** 3 > n:
        r -= 1
    while (r + 1) ** 3 <= n:
        r += 1
    return r


def _mk(question: str, value, subskill: str, difficulty: str,
        answer_latex: str | None = None) -> Problem:
    """``answer_latex`` overrides sp.latex when it would leave radical form."""
    return Problem(
        question_latex=f"${question}$",
        answer_latex=f"${answer_latex if answer_latex is not None else sp.latex(value)}$",
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


@register("roots", "simplify_cube_radical")
def simplify_cube_radical(rng: random.Random, difficulty: str) -> Problem:
    cap = PRODUCT_CAP_CUBE[difficulty]
    # cap // 8 keeps a = 2 (the smallest legal coefficient) inside the cap for
    # every b that can be drawn, so a_max is never clamped up past it.
    # b is drawn first on purpose: bounding b by cap // a^3 instead spreads the
    # coefficient evenly but starves b's range, dropping the generator under
    # the variance floor in tests/test_variance.py. Small coefficients
    # dominating is inherent -- a^3 eats the product budget fast.
    b = _cubefree(rng, min(CUBEFREE_MAX[difficulty], cap // 8))
    a_max = min(COEF_TIER_MAX_CUBE[difficulty], _icbrt(cap // b))
    a = rng.randint(2, a_max)
    k = a ** 3 * b
    question = rf"\sqrt[3]{{{k}}}"
    value = sp.Integer(a) * sp.cbrt(b)
    # sp.latex would turn cbrt(9) into 3^{2/3} -- correct, but not radical
    # notation a student is being asked to produce. Render the radical
    # ourselves and keep `value` as the thing verification re-derives.
    answer = rf"{a} \sqrt[3]{{{b}}}"
    return _mk(question, value, "simplify_cube_radical", difficulty, answer_latex=answer)
