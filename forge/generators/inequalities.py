"""Linear inequalities, including the sign-flip on multiplying by a negative."""

from __future__ import annotations

import random
from fractions import Fraction

import sympy as sp

from ..core.latexfmt import coeff, linear, num, terms
from ..core.problem import Problem
from ..core.registry import register
from ..core.sampling import nonzero_int

X = sp.Symbol("x")
RANGES = {"easy": (1, 9), "medium": (2, 12), "hard": (2, 15)}
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
    m = nonzero_int(rng, 2, hi) * rng.choice((1, -1))
    k = nonzero_int(rng, 2, hi) * m
    return _mk(coeff(m, "x"), rel, str(k), "one_step", difficulty)


@register("inequalities", "two_step")
def two_step(rng: random.Random, difficulty: str) -> Problem:
    lo, hi = RANGES[difficulty]
    rel = rng.choice(list(RELS))
    x_bound = nonzero_int(rng, -hi, hi)
    m = nonzero_int(rng, 2, hi) * rng.choice((1, -1))
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
