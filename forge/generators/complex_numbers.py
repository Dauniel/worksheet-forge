"""Complex number arithmetic and powers of i.

Verified by independently re-parsing the printed "a + bi" text on both sides
of the question -- not trusting the generator's own arithmetic -- and
recomputing over sympy's imaginary unit ``I``.
"""

from __future__ import annotations

import random

import sympy as sp

from ..core.latexfmt import coeff, num, terms
from ..core.problem import Problem
from ..core.registry import register
from ..core.sampling import nonzero_int

RANGES = {"easy": (1, 9), "medium": (2, 12), "hard": (2, 15)}


def _fmt(a: int, b: int) -> str:
    """``a + bi`` (or ``a - bi``), reusing the linear-term join logic."""
    return terms(num(a), coeff(b, "i"))


@register("complex_numbers", "add_subtract")
def add_subtract(rng: random.Random, difficulty: str) -> Problem:
    _, hi = RANGES[difficulty]
    a, b = nonzero_int(rng, -hi, hi), nonzero_int(rng, -hi, hi)
    c, d = nonzero_int(rng, -hi, hi), nonzero_int(rng, -hi, hi)
    op = rng.choice(("+", "-"))
    ra, rb = (a + c, b + d) if op == "+" else (a - c, b - d)

    question = f"({_fmt(a, b)}) {op} ({_fmt(c, d)})"
    return Problem(
        question_latex=f"${question}$",
        answer_latex=f"${_fmt(ra, rb)}$",
        answer_expr=None,
        topic="complex_numbers",
        subskill="add_subtract",
        difficulty=difficulty,
        verify={"kind": "complex_arith", "answer_check": None},
    )


@register("complex_numbers", "multiply")
def multiply(rng: random.Random, difficulty: str) -> Problem:
    _, hi = RANGES[difficulty]
    a, b = nonzero_int(rng, -hi, hi), nonzero_int(rng, -hi, hi)
    c, d = nonzero_int(rng, -hi, hi), nonzero_int(rng, -hi, hi)
    ra, rb = a * c - b * d, a * d + b * c  # (a+bi)(c+di)

    question = f"({_fmt(a, b)})({_fmt(c, d)})"
    return Problem(
        question_latex=f"${question}$",
        answer_latex=f"${_fmt(ra, rb)}$",
        answer_expr=None,
        topic="complex_numbers",
        subskill="multiply",
        difficulty=difficulty,
        verify={"kind": "complex_arith", "answer_check": None},
    )


@register("complex_numbers", "powers_of_i")
def powers_of_i(rng: random.Random, difficulty: str) -> Problem:
    """``i^n``, n reduced mod 4; n drawn large enough to require the reduction."""
    hi = {"easy": 60, "medium": 100, "hard": 200}[difficulty]
    n = rng.randint(5, hi)
    value = (sp.Integer(1), sp.I, sp.Integer(-1), -sp.I)[n % 4]

    return Problem(
        question_latex=f"$i^{{{n}}}$",
        answer_latex=f"${sp.latex(value)}$",
        answer_expr=None,
        topic="complex_numbers",
        subskill="powers_of_i",
        difficulty=difficulty,
        verify={"kind": "power_of_i", "answer_check": None},
    )
