"""Square roots, cube roots, and simplifying radicals (pre-algebra level).

Square radicands stay at <= 150 (nothing past 12^2 for a perfect square), and
cube radicands stay in the low triple digits (<= 216, i.e. nothing past 6^3),
so every value here is either a standard memorized square/cube or a small
radical simplification a student can sanity-check by hand. The square side is
deliberately weighted low -- most simplify_radical draws land at or under 108
even at the hard tier -- because a radicand in the 200s reads as arithmetic
busywork rather than factoring practice.

``square_root`` and ``cube_root`` are deliberately plain: a bare radical of a
perfect square/cube, positive base only, no leading coefficient, no fraction
radicand, no sign. That is the whole problem -- nothing else is sampled.

This is a *known, accepted* small reachable space. Perfect squares <= 144
give only 11 possible bases (2..12) and perfect cubes <= 216 give only 5
(2..6); restricting further per difficulty tier (see the ranges below) makes
each tier's space smaller still. This intrinsically cannot clear the
generic anti-hardcoding variance floor (`tests/test_variance.py` normally
wants >=60% distinct values across 50 draws) -- no RNG tuning fixes a
ceiling that low. `square_root` and `cube_root` are listed in that test's
`SMALL_REACHABLE_SPACE` exemption table with their exact reachable counts;
the test still asserts they reach at/near that true ceiling and that no
single value dominates, so a generator that collapses onto a few favorites
is still caught.

``simplify_radical`` is also a small-reachable-space generator now: it draws
a squarefree radicand b and a coefficient a (a >= 2) with the product a^2*b
capped at <= 150 (per tier, see `PRODUCT_CAP`), producing
sqrt(a^2*b) -> a*sqrt(b). No sign, no fraction, no leading coefficient beyond
the structural `a` -- positive-only throughout. It is listed in both tests'
`SMALL_REACHABLE_SPACE` tables with its exact reachable counts per tier.

``simplify_cube_radical`` is the cube-root analogue of ``simplify_radical``:
it draws a cube-free radicand b and a coefficient a (a >= 2), caps the
product a^3*b (not the factors independently, per tier -- see
`PRODUCT_CAP_CUBE`), and produces cbrt(a^3*b) -> a*cbrt(b). Cube-free means no
prime divides b three or more times, so b may still be divisible by a square
(cbrt(4) and cbrt(9) are already fully simplified), which is what keeps the
radicand space as wide as it is.

It is a small-reachable-space generator too, and for a sharper reason than
the square case: a^3 consumes the product budget so fast that capping the
radicand at 150 leaves the coefficient almost no room (a is effectively
2..4, and a = 4 already forces b = 2). The floor is unusually high as well
-- the smallest cube radical that simplifies at all is cbrt(16) = 2*cbrt(2)
-- so the whole reachable range is 16..144, only 20 values at the hard tier.
Keeping radicands small is the pedagogical priority (cbrt(680) is arithmetic
busywork, not factoring practice), so this generator is listed in both
tests' `SMALL_REACHABLE_SPACE` tables with its exact brute-forced counts
rather than having its cap raised to satisfy the generic floor. The
practical cost is real: cube-simplifying problems repeat across worksheets
sooner than any other subskill here.

Small coefficients dominate every tier here (roughly 80% land on a = 2)
for the same reason: the count of legal b values collapses as a grows.
Drawing a first to even that out was tried and reverted -- it starves b's
range and drops the generator under the variance floor outright.
"""

from __future__ import annotations

import math
import random

import sympy as sp

from ..core.problem import Problem
from ..core.registry import register
from ..core.sampling import pick

# Bases square to at most 12^2 = 144 and cube to at most 6^3 = 216 -- the
# square side capped tighter than "low triple digits", cube side left as-is.
# This is the *entire* sample space for these two subskills now that no
# coefficient/fraction/sign forms remain -- see the module docstring and
# tests/test_variance.py's SMALL_REACHABLE_SPACE table for the exact
# reachable-count accounting this implies.
SQUARE_BASE = {"easy": (2, 9), "medium": (2, 10), "hard": (2, 12)}
# Easy narrowed rather than medium widened: tests/test_variance.py pins the
# exact reachable count at medium, and that pin is the useful one.
CUBE_BASE = {"easy": (2, 4), "medium": (2, 5), "hard": (2, 6)}

# sqrt(a^2 * b) -> a*sqrt(b): the PRODUCT a^2*b is capped (per tier, never
# past 108), not the factors independently -- the coefficient bound is
# derived from whichever squarefree radicand b was drawn, so a^2*b can never
# land outside the cap regardless of how b and a combine.
# b is drawn no larger than cap // 4 so that the smallest legal coefficient
# (a = 2) always fits under the cap -- mirrors the cube-root analogue's
# `cap // 8` bound below. This means a_max is never clamped up past the cap;
# it holds by construction. See tests/test_variance.py and
# tests/test_generators.py's SMALL_REACHABLE_SPACE entries for the exact
# reachable-count accounting this implies at each tier.
PRODUCT_CAP = {"easy": 72, "medium": 108, "hard": 150}
SQUAREFREE_MAX = {"easy": 18, "medium": 27, "hard": 37}
COEF_TIER_MAX = {"easy": 8, "medium": 9, "hard": 10}

# cbrt(a^3 * b) -> a*cbrt(b): the PRODUCT a^3*b is capped, not the factors
# independently -- the radicand b is drawn no larger than cap//8 so that the
# smallest legal coefficient (a = 2) already fits under the cap, and a's upper
# bound is then derived from whichever b came out. The cap therefore holds for
# every (a, b) pair the generator can produce; it is never clamped past.
# Radicands stay in the low hundreds so the prime factorization is work a
# student can do by hand.
PRODUCT_CAP_CUBE = {"easy": 100, "medium": 125, "hard": 150}
CUBEFREE_MAX = {"easy": 12, "medium": 15, "hard": 18}
COEF_TIER_MAX_CUBE = {"easy": 3, "medium": 3, "hard": 4}


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
    cap = PRODUCT_CAP[difficulty]
    # cap // 4 keeps a = 2 (the smallest legal coefficient) inside the cap for
    # every b that can be drawn, so a_max is never clamped up past it.
    b = _squarefree(rng, min(SQUAREFREE_MAX[difficulty], cap // 4))
    a_max = min(COEF_TIER_MAX[difficulty], math.isqrt(cap // b))
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


# --------------------------------------------------------------------------
# simplify_radical_variables: multi-variable radicals (square/cube/4th root,
# including quotient radicands), assuming all variables are positive.
#
# Built entirely backwards -- the outside factor and the leftover radicand
# are chosen first, then multiplied out into the printed radicand -- so the
# "remainder" exponent under the root is always capped at 1 (never allowed to
# reach n-1) purely to keep it renderable as a bare variable with no braces:
# the printed answer's radical content must stay brace-free for the shared
# LaTeX->sympy parser's ``\sqrt{...}`` regex (which does not handle nested
# braces) to read it back for the generic printed-key check.
# --------------------------------------------------------------------------

_RV_VARS = ("x", "y", "z")
_RV_SQFREE = (1, 2, 3, 5, 6, 7, 10, 11, 13)
_RV_CUBEFREE = (1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12)
_RV_FOURFREE = (1, 2, 3, 5, 6, 7, 9, 10, 11, 13)
_RV_A = {2: (2, 3, 4), 3: (2, 3), 4: (2, 3)}
_RV_REM = {2: _RV_SQFREE, 3: _RV_CUBEFREE, 4: _RV_FOURFREE}
_RV_Q = {"easy": (1, 2), "medium": (1, 3), "hard": (1, 4)}


def _rv_to_plain(expr):
    """Swap positive-assumption symbols back to plain ones (matching what
    the shared LaTeX->sympy parser produces), so the generic printed-key
    check compares like with like instead of two symbols that merely share
    a name."""
    subs = {s: sp.Symbol(s.name) for s in expr.free_symbols}
    return expr.subs(subs)


def _rv_mono(coefficient: int, exps: dict, order) -> str:
    """A coefficient times variable powers, e.g. ``4x^{2}y``.

    Two adjacent *bare* (exponent-1) variables would otherwise glue into one
    multi-letter token (``xy``) that the shared LaTeX->sympy parser reads back
    as a single symbol, not ``x*y`` -- implicit multiplication only splits on
    a digit/brace boundary, never letter-letter. A thin space between two
    letter-starting parts sidesteps that without changing how it prints.
    """
    parts = [] if coefficient == 1 else [str(coefficient)]
    for v in order:
        e = exps.get(v, 0)
        if e == 0:
            continue
        parts.append(v if e == 1 else f"{v}^{{{e}}}")
    if not parts:
        return str(coefficient)
    out = parts[0]
    for part in parts[1:]:
        if out[-1].isalpha() and part[0].isalpha():
            out += r"\,"
        out += part
    return out


def _rv_build(rng: random.Random, n: int, nvars: int, difficulty: str,
              force_perfect: bool = False, force_odd: bool = False):
    """Backwards construction: choose the answer's outside/inside parts
    first. Returns ``(radicand_str, answer_expr, answer_str)``."""
    order = list(_RV_VARS[:nvars])
    qlo, qhi = _RV_Q[difficulty]
    A = pick(rng, _RV_A[n])
    r = 1 if force_perfect else pick(rng, _RV_REM[n])
    q, s = {}, {}
    for i, v in enumerate(order):
        q[v] = rng.randint(qlo, qhi)
        if force_perfect:
            s[v] = 0
        elif force_odd and i == 0:
            s[v] = 1
        else:
            s[v] = rng.randint(0, 1)
    full_exps = {v: q[v] * n + s[v] for v in order}
    full_coef = A**n * r
    radicand = _rv_mono(full_coef, full_exps, order)

    symbols = {v: sp.Symbol(v, positive=True) for v in order}
    remainder_expr = sp.Integer(r)
    outside_expr = sp.Integer(A)
    for v in order:
        remainder_expr *= symbols[v] ** s[v]
        outside_expr *= symbols[v] ** q[v]
    answer_expr = _rv_to_plain(outside_expr * sp.root(remainder_expr, n))

    outside_str = _rv_mono(A, q, order)
    if r == 1 and all(s[v] == 0 for v in order):
        answer_str = outside_str
    else:
        inner = _rv_mono(r, s, order)
        rad = rf"\sqrt{{{inner}}}" if n == 2 else rf"\sqrt[{n}]{{{inner}}}"
        answer_str = outside_str + (r"\," if outside_str[-1].isalpha() else "") + rad
    return radicand, answer_expr, answer_str


def _rv_build_quotient(rng: random.Random, n: int, nvars: int, difficulty: str):
    order = list(_RV_VARS[:nvars])
    qlo, qhi = _RV_Q[difficulty]
    A = pick(rng, _RV_A[n])
    r = pick(rng, tuple(v for v in _RV_REM[n] if v != 1))
    q = {v: rng.randint(qlo, qhi) for v in order}
    s = {v: rng.randint(0, 1) for v in order}
    full_exps = {v: q[v] * n + s[v] for v in order}
    full_coef = A**n * r
    D = pick(rng, (2, 3, 4) if n == 2 else (2, 3))
    numer = _rv_mono(full_coef * D, full_exps, order)
    denom = str(D)
    radicand = rf"\dfrac{{{numer}}}{{{denom}}}"

    symbols = {v: sp.Symbol(v, positive=True) for v in order}
    remainder_expr = sp.Integer(r)
    outside_expr = sp.Integer(A)
    for v in order:
        remainder_expr *= symbols[v] ** s[v]
        outside_expr *= symbols[v] ** q[v]
    answer_expr = _rv_to_plain(outside_expr * sp.root(remainder_expr, n))
    outside_str = _rv_mono(A, q, order)
    inner = _rv_mono(r, s, order)
    rad = rf"\sqrt{{{inner}}}" if n == 2 else rf"\sqrt[{n}]{{{inner}}}"
    answer_str = outside_str + (r"\," if outside_str[-1].isalpha() else "") + rad
    return radicand, answer_expr, answer_str


@register("roots", "simplify_radical_variables")
def simplify_radical_variables(rng: random.Random, difficulty: str) -> Problem:
    shape = rng.randrange(5)
    if shape == 0:  # perfect square with variables, e.g. sqrt(16x^8)
        n = 2
        radicand, answer_expr, answer_str = _rv_build(
            rng, n, pick(rng, (1, 2)), difficulty, force_perfect=True
        )
    elif shape == 1:  # non-perfect square, several vars, mixed even/odd exps
        n = 2
        radicand, answer_expr, answer_str = _rv_build(
            rng, n, pick(rng, (2, 3)), difficulty, force_odd=True
        )
    elif shape == 2:  # cube root
        n = 3
        radicand, answer_expr, answer_str = _rv_build(rng, n, pick(rng, (2, 3)), difficulty)
    elif shape == 3:  # fourth root
        n = 4
        radicand, answer_expr, answer_str = _rv_build(rng, n, 3, difficulty)
    else:  # quotient radicand
        n = pick(rng, (2, 3))
        radicand, answer_expr, answer_str = _rv_build_quotient(
            rng, n, pick(rng, (1, 2)), difficulty
        )

    question = rf"\sqrt{{{radicand}}}" if n == 2 else rf"\sqrt[{n}]{{{radicand}}}"
    return Problem(
        question_latex=f"${question}$",
        answer_latex=f"${answer_str}$",
        answer_expr=answer_expr,
        topic="roots",
        subskill="simplify_radical_variables",
        difficulty=difficulty,
        # The generic printed-key re-check compares with plain (non-positive)
        # symbols, which can't prove e.g. sqrt(x*y) == sqrt(x)*sqrt(y) even
        # though it holds for positive reals. _v_simplify_radical_vars above
        # already re-derives and compares this correctly with positive
        # symbols, so the generic check is redundant here -- opt out of it.
        verify={"kind": "simplify_radical_vars", "answer_check": None},
    )
