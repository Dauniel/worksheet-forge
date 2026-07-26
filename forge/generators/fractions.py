"""Fraction arithmetic.

Denominators are sampled from difficulty-scaled small sets so the LCD stays
something a student can find by hand.
"""

from __future__ import annotations

import random
from fractions import Fraction

import sympy as sp

from ..core.latexfmt import mixed
from ..core.problem import Problem
from ..core.registry import register
from ..core.sampling import pick

DENOMS = {
    "easy": (2, 3, 4, 5, 6),
    "medium": (2, 3, 4, 5, 6, 8, 9, 10, 12),
    "hard": (3, 4, 6, 7, 8, 9, 10, 12, 15, 16),
}
NUM_RANGE = {"easy": 5, "medium": 11, "hard": 19}


def _proper(rng: random.Random, difficulty: str, allow_negative: bool = False) -> Fraction:
    d = pick(rng, DENOMS[difficulty])
    n = rng.randint(1, max(d - 1, 1) if difficulty == "easy" else NUM_RANGE[difficulty])
    f = Fraction(n, d)
    if allow_negative and rng.random() < 0.35:
        f = -f
    return f


def _mk(question: str, value, subskill: str, difficulty: str, kind: str = "evaluate") -> Problem:
    value = sp.Rational(value.numerator, value.denominator) if isinstance(value, Fraction) else sp.nsimplify(value)
    return Problem(
        question_latex=f"${question}$",
        answer_latex=f"${mixed(Fraction(int(value.p), int(value.q)))}$",
        answer_expr=value,
        topic="fractions",
        subskill=subskill,
        difficulty=difficulty,
        verify={"kind": kind, "expr": question},
    )


def _disp(f: Fraction) -> str:
    """A fraction as it appears inside a question body."""
    return mixed(f, display=True)


@register("fractions", "add_sub_fractions")
def add_sub_fractions(rng: random.Random, difficulty: str) -> Problem:
    a = _proper(rng, difficulty)
    b = _proper(rng, difficulty)
    if a.denominator == b.denominator and difficulty != "easy":
        b = Fraction(b.numerator, pick(rng, DENOMS[difficulty]))
    op = pick(rng, "+-")
    value = a + b if op == "+" else a - b
    return _mk(f"{_disp(a)} {op} {_disp(b)}", value, "add_sub_fractions", difficulty)


@register("fractions", "mul_div_fractions")
def mul_div_fractions(rng: random.Random, difficulty: str) -> Problem:
    a = _proper(rng, difficulty)
    b = _proper(rng, difficulty)
    if rng.random() < 0.5:
        return _mk(rf"{_disp(a)} \cdot {_disp(b)}", a * b, "mul_div_fractions", difficulty)
    return _mk(rf"{_disp(a)} \div {_disp(b)}", a / b, "mul_div_fractions", difficulty)


@register("fractions", "mixed_numbers")
def mixed_numbers(rng: random.Random, difficulty: str) -> Problem:
    hi = {"easy": 3, "medium": 5, "hard": 9}[difficulty]
    a = Fraction(rng.randint(1, hi)) + _proper(rng, difficulty)
    b = Fraction(rng.randint(1, hi)) + _proper(rng, difficulty)
    op = pick(rng, "+-")
    value = a + b if op == "+" else a - b
    return _mk(f"{_disp(a)} {op} {_disp(b)}", value, "mixed_numbers", difficulty)


@register("fractions", "simplify_fractions")
def simplify_fractions(rng: random.Random, difficulty: str) -> Problem:
    """Built backwards: choose the reduced form, then scale it up."""
    d = pick(rng, [v for v in DENOMS[difficulty] if v > 1])
    # The target must already be in lowest terms, or "simplify" is degenerate
    # (a target of 3/3 prints as "simplify 9/9").
    candidates = [
        n for n in range(1, max(NUM_RANGE[difficulty], d) + 1)
        if sp.igcd(n, d) == 1 and n != d
    ]
    n = pick(rng, candidates)
    target = Fraction(n, d)
    scale = rng.randint(2, {"easy": 4, "medium": 7, "hard": 11}[difficulty])
    # Fraction() would reduce this straight back, so carry the raw integers.
    shown_n = target.numerator * scale
    shown_d = target.denominator * scale
    question = rf"\dfrac{{{shown_n}}}{{{shown_d}}}"
    return _mk(question, target, "simplify_fractions", difficulty)
