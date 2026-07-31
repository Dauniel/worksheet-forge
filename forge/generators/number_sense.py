"""Classifying numbers: rational, irrational, whole, integer."""

from __future__ import annotations

import math
import random
from fractions import Fraction

import sympy as sp

from ..core.latexfmt import mixed
from ..core.problem import Problem
from ..core.registry import register
from ..core.sampling import nonzero_int, pick

RANGE = {"easy": 20, "medium": 40, "hard": 100}
KINDS = ("whole", "negative_integer", "fraction", "sqrt_perfect", "sqrt_nonperfect")


def _is_perfect_square(n: int) -> bool:
    r = math.isqrt(n)
    return r * r == n


def _labels(value) -> set:
    labels: set = set()
    if bool(value.is_rational):
        labels.add("rational")
        if bool(value.is_integer):
            labels.add("integer")
            if value >= 0:
                labels.add("whole")
    else:
        labels.add("irrational")
    return labels


_ORDER = ("rational", "irrational", "integer", "whole")


@register("number_sense", "classify")
def classify(rng: random.Random, difficulty: str) -> Problem:
    hi = RANGE[difficulty]
    kind = pick(rng, KINDS)

    if kind == "whole":
        n = rng.randint(0, hi)
        latex, value = str(n), sp.Integer(n)
    elif kind == "negative_integer":
        n = -rng.randint(1, hi)
        latex, value = str(n), sp.Integer(n)
    elif kind == "fraction":
        while True:
            numer = nonzero_int(rng, -hi, hi)
            denom = rng.randint(2, 12)
            if math.gcd(abs(numer), denom) == 1 and numer % denom != 0:
                break
        value = sp.Rational(numer, denom)
        latex = mixed(Fraction(numer, denom), display=True)
    elif kind == "sqrt_perfect":
        base = rng.randint(2, 12)
        n = base * base
        latex, value = rf"\sqrt{{{n}}}", sp.sqrt(n)
    else:  # sqrt_nonperfect
        while True:
            n = rng.randint(2, hi)
            if not _is_perfect_square(n):
                break
        latex, value = rf"\sqrt{{{n}}}", sp.sqrt(n)

    labels = _labels(value)
    answer_latex = ", ".join(l.capitalize() for l in _ORDER if l in labels)
    return Problem(
        question_latex=f"${latex}$",
        answer_latex=answer_latex,
        answer_expr=frozenset(labels),
        topic="number_sense",
        subskill="classify",
        difficulty=difficulty,
        verify={"kind": "classify", "answer_check": None},
    )
