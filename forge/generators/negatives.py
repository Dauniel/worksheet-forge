"""Signed-number arithmetic.

Every operand is sampled from the rng within difficulty-scaled ranges. There is
no list of problems anywhere in this module.
"""

from __future__ import annotations

import random

import sympy as sp

from ..core.problem import Problem
from ..core.registry import register
from ..core.sampling import nonzero_int, pick, signed

# Magnitude ranges per difficulty. Widening these is the intended way to add
# variance; adding a hardcoded problem is not.
RANGES = {
    "easy": (1, 12),
    "medium": (2, 20),
    "hard": (3, 40),
}
FACTOR_RANGES = {
    "easy": (2, 9),
    "medium": (2, 12),
    "hard": (3, 15),
}


def _operand(rng: random.Random, difficulty: str) -> int:
    lo, hi = RANGES[difficulty]
    return signed(rng, lo, hi)


def _paren(n: int) -> str:
    """Wrap negatives so ``a - (-b)`` reads correctly."""
    return f"({n})" if n < 0 else str(n)


def _mk(question: str, value, subskill: str, difficulty: str, kind: str = "evaluate") -> Problem:
    value = sp.nsimplify(value)
    return Problem(
        question_latex=f"${question}$",
        answer_latex=f"${sp.latex(value)}$",
        answer_expr=value,
        topic="negatives",
        subskill=subskill,
        difficulty=difficulty,
        verify={"kind": kind, "expr": question},
    )


@register("negatives", "add_sub_integers")
def add_sub_integers(rng: random.Random, difficulty: str) -> Problem:
    a = _operand(rng, difficulty)
    b = _operand(rng, difficulty)
    op = pick(rng, "+-")
    n_terms = 3 if (difficulty == "hard" and rng.random() < 0.5) else 2

    question = f"{a} {op} {_paren(b)}"
    value = a + b if op == "+" else a - b
    if n_terms == 3:
        c = _operand(rng, difficulty)
        op2 = pick(rng, "+-")
        question += f" {op2} {_paren(c)}"
        value = value + c if op2 == "+" else value - c
    return _mk(question, value, "add_sub_integers", difficulty)


@register("negatives", "mul_div_integers")
def mul_div_integers(rng: random.Random, difficulty: str) -> Problem:
    lo, hi = FACTOR_RANGES[difficulty]
    if rng.random() < 0.5:
        a = signed(rng, lo, hi)
        b = signed(rng, lo, hi)
        # At least one operand negative -- that is the skill being drilled.
        if a > 0 and b > 0:
            b = -b
        return _mk(rf"{a} \cdot {_paren(b)}", a * b, "mul_div_integers", difficulty)

    # Build division backwards from the quotient so it is always exact.
    divisor = signed(rng, lo, hi)
    quotient = signed(rng, 2, hi)
    if divisor > 0 and quotient > 0:
        quotient = -quotient
    dividend = divisor * quotient
    return _mk(
        rf"{dividend} \div {_paren(divisor)}", quotient, "mul_div_integers", difficulty
    )


@register("negatives", "mixed_operations")
def mixed_operations(rng: random.Random, difficulty: str) -> Problem:
    lo, hi = FACTOR_RANGES[difficulty]
    a = _operand(rng, difficulty)
    b = signed(rng, lo, hi)
    c = signed(rng, lo, hi)
    if rng.random() < 0.5:
        question = rf"{a} + {_paren(b)} \cdot {_paren(c)}"
        value = a + b * c
    else:
        product = b * c
        question = rf"{product} \div {_paren(b)} - {_paren(a)}"
        value = c - a
    return _mk(question, value, "mixed_operations", difficulty)


@register("negatives", "order_of_operations")
def order_of_operations(rng: random.Random, difficulty: str) -> Problem:
    lo, hi = FACTOR_RANGES[difficulty]
    base = signed(rng, 2, 6 if difficulty == "easy" else 9)
    power = 2 if difficulty == "easy" else rng.randint(2, 3)
    a = _operand(rng, difficulty)
    b = nonzero_int(rng, lo, hi)

    style = rng.randrange(3)
    if style == 0:
        question = rf"{_paren(base)}^{{{power}}} - {_paren(a)} \cdot {b}"
        value = base**power - a * b
    elif style == 1:
        question = rf"{a} - {b} \cdot ({_paren(base)} + {_paren(a)})"
        value = a - b * (base + a)
    else:
        # Backwards construction: choose a divisor of the square so the
        # quotient is an integer rather than an accidental fraction.
        inner = base + a
        if inner == 0:
            inner = base or 1
            a = inner - base
        divisors = [d for d in sp.divisors(inner**2) if d <= max(hi, 2)]
        b = pick(rng, divisors) * rng.choice((-1, 1))
        question = rf"({base} + {_paren(a)})^{{2}} \div {_paren(b)}"
        value = sp.Integer(inner**2) / b
    return _mk(question, value, "order_of_operations", difficulty)
