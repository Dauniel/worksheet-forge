"""Linear equations, always constructed backwards from a chosen solution.

Choosing ``x_sol`` first and deriving a constant from it makes no-solution and
infinite-solution cases structurally impossible, and keeps the answer clean.
"""

from __future__ import annotations

import random
from fractions import Fraction

import sympy as sp

from ..core.latexfmt import coeff, dnum, linear, num, terms
from ..core.problem import Problem
from ..core.registry import register
from ..core.sampling import nonzero_int, pick

RANGES = {"easy": (1, 9), "medium": (2, 12), "hard": (3, 20)}

# Denominators widen with difficulty: thirds and quarters clear in one step,
# while fifths and sixths force a real LCD before the equation moves.
NICE_DENOMS = {"easy": (2, 3, 4), "medium": (2, 3, 4), "hard": (2, 3, 4, 5, 6)}

# How often the solution itself is a fraction rather than an integer. This is
# the difficulty that actually bites -- a student who can solve 3x+5=20 often
# stalls when x lands on -7/4 -- so it is the axis that separates the tiers,
# not just the size of the coefficients.
FRACTION_P = {"easy": 0.0, "medium": 0.2, "hard": 0.35}


def _solution(rng: random.Random, difficulty: str) -> Fraction:
    """Integer solutions by default; a tidy fraction at the rate set by tier.

    Redraws when the numerator happens to divide the denominator: Fraction()
    reduces, so 8/4 would silently come back as the integer 2 and the measured
    fraction rate would read well under FRACTION_P (0.27 against a configured
    0.35). Same reduction trap that fractional_both_sides guards against in
    inequalities.py.
    """
    lo, hi = RANGES[difficulty]
    whole = nonzero_int(rng, -hi, hi)
    if rng.random() >= FRACTION_P[difficulty]:
        return Fraction(whole)
    for _ in range(20):
        candidate = Fraction(whole, pick(rng, NICE_DENOMS[difficulty]))
        if candidate.denominator > 1:
            return candidate
        whole = nonzero_int(rng, -hi, hi)
    return candidate  # pathological rng: fall back rather than loop forever


def _mk(lhs: str, rhs: str, x_sol, subskill: str, difficulty: str) -> Problem:
    value = sp.Rational(x_sol.numerator, x_sol.denominator)
    return Problem(
        question_latex=f"${lhs} = {rhs}$",
        answer_latex=f"$x = {sp.latex(value)}$",
        answer_expr=value,
        topic="linear_equations",
        subskill=subskill,
        difficulty=difficulty,
        verify={"kind": "solve", "var": "x", "lhs": lhs, "rhs": rhs},
    )


@register("linear_equations", "one_step")
def one_step(rng: random.Random, difficulty: str) -> Problem:
    lo, hi = RANGES[difficulty]
    x_sol = Fraction(nonzero_int(rng, -hi, hi))
    if rng.random() < 0.5:
        b = nonzero_int(rng, -hi, hi)
        return _mk(terms("x", num(b)), num(x_sol + b), x_sol, "one_step", difficulty)
    m = nonzero_int(rng, 2, hi)
    return _mk(coeff(m, "x"), num(m * x_sol), x_sol, "one_step", difficulty)


@register("linear_equations", "two_step")
def two_step(rng: random.Random, difficulty: str) -> Problem:
    lo, hi = RANGES[difficulty]
    x_sol = _solution(rng, difficulty)
    m = nonzero_int(rng, 2, hi)
    b = nonzero_int(rng, -hi, hi)
    # rhs derived from the chosen solution, so it is exact by construction.
    # dnum, not num: _solution can return a fraction, and a question body is
    # display-style -- an inline \frac renders shrunken next to the equation.
    return _mk(linear(m, b), dnum(m * x_sol + b), x_sol, "two_step", difficulty)


@register("linear_equations", "multi_step_both_sides")
def multi_step_both_sides(rng: random.Random, difficulty: str) -> Problem:
    lo, hi = RANGES[difficulty]
    x_sol = _solution(rng, difficulty)
    m1 = nonzero_int(rng, -hi, hi)
    m2 = nonzero_int(rng, -hi, hi)
    while m2 == m1:  # equal slopes would give no solution or infinitely many
        m2 = nonzero_int(rng, -hi, hi)
    b1 = nonzero_int(rng, -hi, hi)
    b2 = (m1 - m2) * x_sol + b1
    # b2 carries the fraction when x_sol is fractional, so render display-style.
    return _mk(
        linear(m1, b1, display=True), linear(m2, b2, display=True),
        x_sol, "multi_step_both_sides", difficulty,
    )


@register("linear_equations", "fractional")
def fractional(rng: random.Random, difficulty: str) -> Problem:
    """Equations with a fractional coefficient or a variable over a denominator.

    Three shapes, drawn backwards from ``x_sol`` like every other generator
    here: ``(a/n)x + b = c``, ``x/d + b = c``, and a two-step form that needs
    the denominator cleared, ``(x + a)/d + b = c``.
    """
    lo, hi = RANGES[difficulty]
    x_sol = _solution(rng, difficulty)
    style = rng.randrange(3)

    if style == 0:
        n = pick(rng, NICE_DENOMS[difficulty])
        m = Fraction(nonzero_int(rng, -min(hi, 9), min(hi, 9)), n)
        b = nonzero_int(rng, -hi, hi)
        lhs = linear(m, b, display=True)
        rhs = dnum(m * x_sol + b)
    elif style == 1:
        d = pick(rng, NICE_DENOMS[difficulty])
        b = nonzero_int(rng, -hi, hi)
        lhs = terms(rf"\dfrac{{x}}{{{d}}}", num(b))
        rhs = dnum(x_sol / d + b)
    else:
        a = nonzero_int(rng, -hi, hi)
        d = pick(rng, NICE_DENOMS[difficulty])
        b = nonzero_int(rng, -hi, hi)
        inner = linear(1, a)
        lhs = terms(rf"\dfrac{{{inner}}}{{{d}}}", num(b))
        rhs = dnum((x_sol + a) / d + b)

    return _mk(lhs, rhs, x_sol, "fractional", difficulty)


@register("linear_equations", "proportion")
def proportion(rng: random.Random, difficulty: str) -> Problem:
    """Fraction-equals-fraction equations solved by cross-multiplying.

    Every numerator/constant is built backwards from an integer ``x_sol`` so
    both sides land on exact, integer-coefficient terms -- only the
    denominators carry the fraction, which is what makes cross-multiplying
    the natural move.
    """
    lo, hi = RANGES[difficulty]
    x_sol = Fraction(nonzero_int(rng, -hi, hi))
    style = rng.randrange(3)

    if style == 0:
        # (a*x + b)/d = p/q, where p/q is n/d scaled up so it isn't already
        # in lowest terms matching the left denominator.
        a = nonzero_int(rng, 1, min(hi, 9))
        d = pick(rng, NICE_DENOMS[difficulty])
        # p/q below is always n/d scaled, so a radicand-free n divisible by d
        # would print a right side that reduces to a whole number (8/8 = 1),
        # collapsing the cross-multiplication into a one-step equation.
        n = nonzero_int(rng, -hi, hi)  # numerator of the left side
        while n % d == 0:
            n = nonzero_int(rng, -hi, hi)
        b = n - a * x_sol
        s = pick(rng, (1, 2, 3))
        p, q = n * s, d * s
        lhs = rf"\dfrac{{{linear(a, b, display=True)}}}{{{d}}}"
        rhs = rf"\dfrac{{{p}}}{{{q}}}"
    elif style == 1:
        # p / x = a / q  (x sits in a denominator)
        q = pick(rng, (2, 3, 4, 5, 6))
        # Same trap on this side: a divisible by q prints 4/2 or 6/6.
        a = nonzero_int(rng, 1, min(hi, 9))
        while a % q == 0:
            a = nonzero_int(rng, 1, min(hi, 9))
        p = nonzero_int(rng, -min(hi, 9), min(hi, 9))
        x_sol = Fraction(p * q, a)
        lhs = rf"\dfrac{{{p}}}{{x}}"
        rhs = rf"\dfrac{{{a}}}{{{q}}}"
    else:
        # (a1*x + b1)/d1 = (a2*x + b2)/d2, with d2 a small integer multiple
        # of d1 (or vice versa) so the matching numerators stay exact ints.
        d_base = pick(rng, NICE_DENOMS[difficulty])
        k = pick(rng, (2, 3))
        n_base = nonzero_int(rng, -hi, hi)
        n_other = n_base * k
        d_other = d_base * k
        if rng.random() < 0.5:
            d1, n1, d2, n2 = d_base, n_base, d_other, n_other
        else:
            d1, n1, d2, n2 = d_other, n_other, d_base, n_base
        a1 = nonzero_int(rng, 1, min(hi, 9))
        a2 = nonzero_int(rng, 1, min(hi, 9))
        while a1 * d2 == a2 * d1:  # equal slopes -> identity, not one solution
            a2 = nonzero_int(rng, 1, min(hi, 9))
        b1 = n1 - a1 * x_sol
        b2 = n2 - a2 * x_sol
        lhs = rf"\dfrac{{{linear(a1, b1, display=True)}}}{{{d1}}}"
        rhs = rf"\dfrac{{{linear(a2, b2, display=True)}}}{{{d2}}}"

    return _mk(lhs, rhs, x_sol, "proportion", difficulty)


@register("linear_equations", "combine_then_solve")
def combine_then_solve(rng: random.Random, difficulty: str) -> Problem:
    """Equations that need like terms collected on one side before solving.

    Two families, both built backwards from ``x_sol``:

    - two variable terms, no constant: ``m1*x + m2*x = c``
    - one variable term, two constants: ``m*x + b1 + b2 = c``

    The side carrying the un-combined expression is randomized, matching the
    reference worksheet's mix of ``-6p + 3p = 12`` and ``-16 = p + 7p``.
    """
    lo, hi = RANGES[difficulty]
    x_sol = _solution(rng, difficulty)

    if rng.random() < 0.5:
        m1 = nonzero_int(rng, -hi, hi)
        m2 = nonzero_int(rng, -hi, hi)
        while m1 + m2 == 0:  # vanishing variable -> degenerate equation
            m2 = nonzero_int(rng, -hi, hi)
        expr = terms(coeff(m1, "x"), coeff(m2, "x"))
        c = (m1 + m2) * x_sol
    else:
        m = nonzero_int(rng, -hi, hi)
        b1 = nonzero_int(rng, -hi, hi)
        b2 = nonzero_int(rng, -hi, hi)
        expr = terms(coeff(m, "x"), num(b1), num(b2))
        c = m * x_sol + b1 + b2

    const_side = dnum(c)
    if rng.random() < 0.5:
        lhs, rhs = expr, const_side
    else:
        lhs, rhs = const_side, expr

    return _mk(lhs, rhs, x_sol, "combine_then_solve", difficulty)


@register("linear_equations", "with_distribution")
def with_distribution(rng: random.Random, difficulty: str) -> Problem:
    lo, hi = RANGES[difficulty]
    x_sol = Fraction(nonzero_int(rng, -hi, hi))
    k = nonzero_int(rng, 2, min(hi, 9))
    a = nonzero_int(rng, 1, min(hi, 9))
    b = nonzero_int(rng, -hi, hi)
    c = nonzero_int(rng, -hi, hi)

    inner = linear(a, b)
    prefix = coeff(k, "")
    lhs = terms(f"{prefix}({inner})", num(c))
    rhs = num(k * (a * x_sol + b) + c)
    return _mk(lhs, rhs, x_sol, "with_distribution", difficulty)
