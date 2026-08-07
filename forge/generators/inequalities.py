"""Linear inequalities, including the sign-flip on multiplying by a negative."""

from __future__ import annotations

import random
from fractions import Fraction

import sympy as sp

from ..core.latexfmt import coeff, dnum, linear, num, terms
from ..core.problem import Problem
from ..core.registry import register
from ..core.sampling import nonzero_int, pick

NICE_DENOMS = {"easy": (2, 3, 4), "medium": (2, 3, 4), "hard": (2, 3, 4, 5, 6)}

X = sp.Symbol("x")
RANGES = {"easy": (1, 9), "medium": (2, 12), "hard": (3, 20)}

# Probability the leading coefficient is negative, which is what forces the
# sign flip. Left to an even coin the flip shows up in half the problems at
# every tier, so the tiers taught the same thing at different magnitudes;
# weighting it is what actually makes hard harder here.
NEG_LEAD_P = {"easy": 0.35, "medium": 0.5, "hard": 0.75}
RELS = {"<": r"<", "<=": r"\le", ">": r">", ">=": r"\ge"}
FLIP = {"<": ">", ">": "<", "<=": ">=", ">=": "<="}


def _mk(lhs: str, rel: str, rhs: str, subskill: str, difficulty: str) -> Problem:
    l_expr = sp.sympify(_p(lhs))
    r_expr = sp.sympify(_p(rhs))
    stated = {"<": sp.Lt, "<=": sp.Le, ">": sp.Gt, ">=": sp.Ge}[rel](l_expr, r_expr)
    solution_set = sp.solve_univariate_inequality(stated, X, relational=False)
    boundary, direction = _describe(l_expr, r_expr, rel)
    return Problem(
        question_latex=f"${lhs} {RELS[rel]} {rhs}$",
        answer_latex=f"$x {RELS[direction]} {sp.latex(boundary)}$",
        answer_expr=solution_set,
        topic="inequalities",
        subskill=subskill,
        difficulty=difficulty,
        verify={
            "kind": "inequality",
            "var": "x",
            "lhs": lhs,
            "rhs": rhs,
            "rel": rel,
            "solution_set": solution_set,
        },
    )


def _p(latex: str) -> str:
    from ..core.verify import latex_to_sympy

    return str(latex_to_sympy(latex))


def _lead(rng: random.Random, difficulty: str, hi: int) -> int:
    """A nonzero leading coefficient, signed negative at the tier's rate."""
    sign = -1 if rng.random() < NEG_LEAD_P[difficulty] else 1
    return nonzero_int(rng, 2, hi) * sign


def _describe(l_expr, r_expr, rel: str):
    """Reduce ``ax + b REL c`` to ``x REL' k``, flipping when a < 0."""
    diff = sp.expand(l_expr - r_expr)
    a = diff.coeff(X, 1)
    b = diff.coeff(X, 0)
    boundary = sp.Rational(-b, a) if a != 0 else sp.nan
    direction = FLIP[rel] if a < 0 else rel
    return boundary, direction


@register("inequalities", "one_step")
def one_step(rng: random.Random, difficulty: str) -> Problem:
    lo, hi = RANGES[difficulty]
    rel = rng.choice(list(RELS))
    if rng.random() < 0.5:
        b = nonzero_int(rng, -hi, hi)
        return _mk(terms("x", num(b)), rel, str(nonzero_int(rng, -hi, hi)),
                   "one_step", difficulty)
    m = _lead(rng, difficulty, hi)
    k = nonzero_int(rng, 2, hi) * m
    return _mk(coeff(m, "x"), rel, str(k), "one_step", difficulty)


@register("inequalities", "two_step")
def two_step(rng: random.Random, difficulty: str) -> Problem:
    lo, hi = RANGES[difficulty]
    rel = rng.choice(list(RELS))
    x_bound = nonzero_int(rng, -hi, hi)
    m = _lead(rng, difficulty, hi)
    b = nonzero_int(rng, -hi, hi)
    return _mk(linear(m, b), rel, str(m * x_bound + b), "two_step", difficulty)


@register("inequalities", "multi_step_both_sides")
def multi_step_both_sides(rng: random.Random, difficulty: str) -> Problem:
    lo, hi = RANGES[difficulty]
    rel = rng.choice(list(RELS))
    x_bound = nonzero_int(rng, -hi, hi)
    m1 = nonzero_int(rng, -hi, hi)
    m2 = nonzero_int(rng, -hi, hi)
    while m2 == m1:
        m2 = nonzero_int(rng, -hi, hi)
    b1 = nonzero_int(rng, -hi, hi)
    b2 = (m1 - m2) * x_bound + b1
    return _mk(linear(m1, b1), rel, linear(m2, b2), "multi_step_both_sides", difficulty)


@register("inequalities", "fractional")
def fractional(rng: random.Random, difficulty: str) -> Problem:
    """Inequalities with a fractional coefficient or a variable over a denominator.

    Same three shapes as ``linear_equations.fractional`` -- ``(a/n)x + b REL c``,
    ``x/d + b REL c``, and ``(x + a)/d + b REL c`` -- drawn backwards from an
    integer boundary ``x_bound`` so the answer stays clean even though the
    problem itself carries a fraction. ``_describe`` (shared with every other
    subskill here) already handles the sign-flip correctly for a negative
    fractional coefficient, since it reasons about the coefficient's sign,
    not its denominator.
    """
    lo, hi = RANGES[difficulty]
    rel = rng.choice(list(RELS))
    x_bound = nonzero_int(rng, -hi, hi)
    style = rng.randrange(3)

    if style == 0:
        n = pick(rng, NICE_DENOMS[difficulty])
        m = Fraction(nonzero_int(rng, -min(hi, 9), min(hi, 9)), n)
        b = nonzero_int(rng, -hi, hi)
        lhs = linear(m, b, display=True)
        rhs = dnum(m * x_bound + b)
    elif style == 1:
        d = pick(rng, NICE_DENOMS[difficulty])
        b = nonzero_int(rng, -hi, hi)
        lhs = terms(rf"\dfrac{{x}}{{{d}}}", num(b))
        rhs = dnum(Fraction(x_bound, d) + b)
    else:
        a = nonzero_int(rng, -hi, hi)
        d = pick(rng, NICE_DENOMS[difficulty])
        b = nonzero_int(rng, -hi, hi)
        inner = linear(1, a)
        lhs = terms(rf"\dfrac{{{inner}}}{{{d}}}", num(b))
        rhs = dnum(Fraction(x_bound + a, d) + b)

    return _mk(lhs, rel, rhs, "fractional", difficulty)


@register("inequalities", "fractional_both_sides")
def fractional_both_sides(rng: random.Random, difficulty: str) -> Problem:
    """Fractional coefficients on both sides of the inequality."""
    lo, hi = RANGES[difficulty]
    rel = rng.choice(list(RELS))
    x_bound = nonzero_int(rng, -hi, hi)
    cap = min(hi, 9)
    # Fraction() reduces, so drawing a numerator that happens to be a multiple
    # of its denominator yields an integer coefficient. Redraw until at least
    # one side survives reduction with a real denominator -- otherwise this
    # subskill degenerates into multi_step_both_sides with no fraction in sight.
    while True:
        m1 = Fraction(nonzero_int(rng, -cap, cap), pick(rng, NICE_DENOMS[difficulty]))
        m2 = Fraction(nonzero_int(rng, -cap, cap), pick(rng, NICE_DENOMS[difficulty]))
        if m1 != m2 and (m1.denominator > 1 or m2.denominator > 1):
            break
    b1 = nonzero_int(rng, -hi, hi)
    b2 = (m1 - m2) * x_bound + b1
    lhs = linear(m1, b1, display=True)
    rhs = linear(m2, b2, display=True)
    return _mk(lhs, rel, rhs, "fractional_both_sides", difficulty)


COMPOUND_WIDTH = {"easy": (3, 8), "medium": (4, 14), "hard": (5, 22)}


@register("inequalities", "compound_and")
def compound_and(rng: random.Random, difficulty: str) -> Problem:
    """A conjunction written as one three-part inequality: a < mx + b < c.

    Built backwards from the two bounds so both edges are integers. A
    negative m flips *both* relations, which is the case this subskill
    exists to drill -- ``_describe`` handles one relation at a time, so the
    flip is applied here explicitly and checked by the verifier against the
    printed form.
    """
    lo, hi = COMPOUND_WIDTH[difficulty]
    m = _lead(rng, difficulty, hi)
    b = nonzero_int(rng, -hi, hi)
    low_x = nonzero_int(rng, -hi, hi)
    high_x = low_x + rng.randint(*COMPOUND_WIDTH[difficulty])

    left, right = m * low_x + b, m * high_x + b
    if left > right:  # negative coefficient reverses which edge is smaller
        left, right = right, left
    strict_l = rng.random() < 0.5
    strict_r = rng.random() < 0.5
    rel_l = "<" if strict_l else "\\le"
    rel_r = "<" if strict_r else "\\le"

    middle = linear(m, b)
    question = f"${left} {rel_l} {middle} {rel_r} {right}$"

    lo_b, hi_b = (low_x, high_x)
    left_closed = not strict_l if m > 0 else not strict_r
    right_closed = not strict_r if m > 0 else not strict_l
    solution = sp.Interval(lo_b, hi_b, left_open=not left_closed, right_open=not right_closed)

    bound_l = f"{'\\le' if left_closed else '<'}"
    bound_r = f"{'\\le' if right_closed else '<'}"
    answer = f"${lo_b} {bound_l} x {bound_r} {hi_b}$"
    return Problem(
        question_latex=question,
        answer_latex=answer,
        answer_expr=solution,
        topic="inequalities",
        subskill="compound_and",
        difficulty=difficulty,
        verify={"kind": "compound_inequality"},
    )
