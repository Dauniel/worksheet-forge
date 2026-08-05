"""Arithmetic and geometric sequences, plus an arithmetic series sum.

Every value a student needs is printed as a bare ``$n$`` in the prose, so the
verifier can pull them back out in reading order (the same convention
``percent_apps``/``geometry`` use) and recompute the formula independently,
rather than trusting whatever the generator plugged in.
"""

from __future__ import annotations

import random

import sympy as sp

from ..core.problem import Problem
from ..core.registry import register

SCALE = {"easy": (2, 9), "medium": (2, 12), "hard": (2, 15)}


def _ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
N_RANGE = {"easy": (2, 8), "medium": (3, 12), "hard": (4, 20)}


@register("sequences_series", "arithmetic_nth_term")
def arithmetic_nth_term(rng: random.Random, difficulty: str) -> Problem:
    _, hi = SCALE[difficulty]
    a1 = rng.randint(-hi, hi) or 1
    d = rng.randint(-hi, hi) or 1
    n = rng.randint(*N_RANGE[difficulty])
    value = a1 + (n - 1) * d

    text = (
        f"An arithmetic sequence has first term ${a1}$ and common "
        f"difference ${d}$. Find the ${n}${_ordinal(n)} term."
    )
    return Problem(
        question_latex=text,
        answer_latex=f"${value}$",
        answer_expr=sp.Integer(value),
        topic="sequences_series",
        subskill="arithmetic_nth_term",
        difficulty=difficulty,
        verify={"kind": "arithmetic_nth_term"},
    )


@register("sequences_series", "geometric_nth_term")
def geometric_nth_term(rng: random.Random, difficulty: str) -> Problem:
    a1 = rng.randint(1, 5)
    r = rng.choice([v for v in range(-4, 5) if v not in (0, 1)])
    n = rng.randint(*{"easy": (2, 5), "medium": (2, 6), "hard": (2, 7)}[difficulty])
    value = a1 * r ** (n - 1)

    text = (
        f"A geometric sequence has first term ${a1}$ and common ratio "
        f"${r}$. Find the ${n}${_ordinal(n)} term."
    )
    return Problem(
        question_latex=text,
        answer_latex=f"${value}$",
        answer_expr=sp.Integer(value),
        topic="sequences_series",
        subskill="geometric_nth_term",
        difficulty=difficulty,
        verify={"kind": "geometric_nth_term"},
    )


@register("sequences_series", "arithmetic_series_sum")
def arithmetic_series_sum(rng: random.Random, difficulty: str) -> Problem:
    _, hi = SCALE[difficulty]
    a1 = rng.randint(-hi, hi) or 1
    d = rng.randint(-hi, hi) or 1
    n = rng.randint(*N_RANGE[difficulty])
    value = sp.Rational(n, 2) * (2 * a1 + (n - 1) * d)

    text = (
        f"An arithmetic sequence has first term ${a1}$ and common "
        f"difference ${d}$. Find the sum of the first ${n}$ terms."
    )
    return Problem(
        question_latex=text,
        answer_latex=f"${sp.latex(value)}$",
        answer_expr=value,
        topic="sequences_series",
        subskill="arithmetic_series_sum",
        difficulty=difficulty,
        verify={"kind": "arithmetic_series_sum"},
    )
