"""Slope and linear graphs.

Always constructed backwards: choose ``m`` and ``b`` first, then pick lattice
``x`` values and compute their ``y``. Guarantees clean slopes, integer points,
and never a vertical line.
"""

from __future__ import annotations

import random
from fractions import Fraction

import sympy as sp

from ..core.latexfmt import coeff, dnum, linear, num, terms
from ..core.problem import Problem
from ..core.registry import register
from ..core.sampling import distinct, nonzero_int, pick

SLOPE_DENOMS = {"easy": (1,), "medium": (1, 1, 2), "hard": (1, 2, 3, 4)}
RANGES = {"easy": (1, 6), "medium": (1, 9), "hard": (2, 12)}


def _line(rng: random.Random, difficulty: str, allow_zero_slope: bool = True):
    lo, hi = RANGES[difficulty]
    d = pick(rng, SLOPE_DENOMS[difficulty])
    n = nonzero_int(rng, lo, hi)
    m = Fraction(n, d)
    if allow_zero_slope and rng.random() < 0.08:
        m = Fraction(0)
    b = rng.randint(-hi, hi)
    return m, b


def _points(rng: random.Random, m: Fraction, difficulty: str, b: int):
    """Two distinct x values whose y values are integers."""
    lo, hi = RANGES[difficulty]
    span = max(hi, 6)
    step = m.denominator
    while True:
        xs = distinct(rng, -span, span, 2)
        x1, x2 = sorted(xs)
        if x1 % step == 0 and x2 % step == 0:
            return (x1, int(m * x1 + b)), (x2, int(m * x2 + b))


@register("slope", "slope_from_two_points")
def slope_from_two_points(rng: random.Random, difficulty: str) -> Problem:
    m, b = _line(rng, difficulty)
    (x1, y1), (x2, y2) = _points(rng, m, difficulty, b)
    value = sp.Rational(m.numerator, m.denominator)
    return Problem(
        question_latex=f"$({x1}, {y1})$ and $({x2}, {y2})$",
        answer_latex=f"$m = {sp.latex(value)}$",
        answer_expr=value,
        topic="slope",
        subskill="slope_from_two_points",
        difficulty=difficulty,
        verify={"kind": "slope_from_points"},
    )


@register("slope", "equation_from_two_points")
def equation_from_two_points(rng: random.Random, difficulty: str) -> Problem:
    m, b = _line(rng, difficulty)
    (x1, y1), (x2, y2) = _points(rng, m, difficulty, b)
    return Problem(
        question_latex=f"$({x1}, {y1})$ and $({x2}, {y2})$",
        answer_latex=f"$y = {linear(m, b)}$",
        answer_expr=(sp.Rational(m.numerator, m.denominator), sp.Integer(b)),
        topic="slope",
        subskill="equation_from_two_points",
        difficulty=difficulty,
        verify={"kind": "line_through_points"},
    )


def _line_with_x_intercept(rng: random.Random, difficulty: str):
    """Choose ``m`` and the x-intercept ``x0`` first, then derive ``b``.

    Built backwards so the x-intercept comes out exact: ``x0`` is drawn as a
    multiple of ``m``'s denominator, so ``b = -m*x0`` is always an integer
    and ``-b/m`` reproduces ``x0`` exactly.
    """
    lo, hi = RANGES[difficulty]
    d = pick(rng, SLOPE_DENOMS[difficulty])
    n = nonzero_int(rng, lo, hi)
    m = Fraction(n, d)
    k = nonzero_int(rng, 1, max(2, hi // max(d, 1))) * rng.choice((-1, 1))
    x0 = d * k
    b = -n * k
    return m, b, x0


@register("slope", "identify_slope_intercept")
def identify_slope_intercept(rng: random.Random, difficulty: str) -> Problem:
    m, b, x0 = _line_with_x_intercept(rng, difficulty)
    ms = sp.Rational(m.numerator, m.denominator)
    return Problem(
        question_latex=f"$y = {linear(m, b, display=True)}$",
        answer_latex=(
            rf"$m = {sp.latex(ms)}$, \quad $b = {b}$, \quad "
            rf"$x\text{{-intercept}} = ({x0}, 0)$, \quad "
            rf"$y\text{{-intercept}} = (0, {b})$"
        ),
        answer_expr=(ms, sp.Integer(b), sp.Integer(x0)),
        topic="slope",
        subskill="identify_slope_intercept",
        difficulty=difficulty,
        verify={"kind": "slope_intercept"},
    )


@register("slope", "slope_and_equation")
def slope_and_equation(rng: random.Random, difficulty: str) -> Problem:
    m, b = _line(rng, difficulty)
    (x1, y1), (x2, y2) = _points(rng, m, difficulty, b)
    ms = sp.Rational(m.numerator, m.denominator)
    return Problem(
        question_latex=f"$({x1}, {y1})$ and $({x2}, {y2})$",
        answer_latex=rf"$m = {sp.latex(ms)}$, \quad $y = {linear(m, b)}$",
        answer_expr=(ms, sp.Integer(b)),
        topic="slope",
        subskill="slope_and_equation",
        difficulty=difficulty,
        verify={"kind": "slope_and_line"},
    )


@register("slope", "identify_from_standard")
def identify_from_standard(rng: random.Random, difficulty: str) -> Problem:
    m, b, x0 = _line_with_x_intercept(rng, difficulty)
    ms = sp.Rational(m.numerator, m.denominator)
    d = m.denominator
    if d == 1:
        k = d * rng.randint(2, 4)
    else:
        k = d * rng.randint(1, 3)
    A = int(k * m)
    C_const = k * b

    form = rng.choice((1, 2))
    if form == 1:
        # A*x - k*y = -k*b  ->  Ax + By = C
        B = -k
        C = -C_const
        if rng.random() < 0.5:
            A, B, C = -A, -B, -C
        lhs = terms(coeff(A, "x"), coeff(B, "y"))
        rhs = num(C)
    else:
        # k*y = A*x + k*b -> By = Ax + C
        B = k
        lhs = coeff(B, "y")
        rhs = linear(A, C_const)

    return Problem(
        question_latex=f"${lhs} = {rhs}$",
        answer_latex=(
            rf"$m = {sp.latex(ms)}$, \quad $b = {sp.latex(sp.Integer(b))}$, \quad "
            rf"$x\text{{-intercept}} = ({x0}, 0)$, \quad "
            rf"$y\text{{-intercept}} = (0, {sp.latex(sp.Integer(b))})$"
        ),
        answer_expr=(ms, sp.Integer(b), sp.Integer(x0)),
        topic="slope",
        subskill="identify_from_standard",
        difficulty=difficulty,
        verify={"kind": "slope_intercept_standard"},
    )


@register("slope", "point_slope_to_equation")
def point_slope_to_equation(rng: random.Random, difficulty: str) -> Problem:
    """Given a slope and one point, write slope-intercept form."""
    m, b = _line(rng, difficulty, allow_zero_slope=False)
    (x1, y1), _ = _points(rng, m, difficulty, b)
    ms = sp.Rational(m.numerator, m.denominator)
    return Problem(
        # dnum, not sp.latex: a question body is display-style, and a fractional
        # slope printed with inline \frac renders shrunken beside the point.
        question_latex=f"$m = {dnum(m)}$ through $({x1}, {y1})$",
        answer_latex=f"$y = {linear(m, b)}$",
        answer_expr=(ms, sp.Integer(b)),
        topic="slope",
        subskill="point_slope_to_equation",
        difficulty=difficulty,
        verify={"kind": "point_slope"},
    )
