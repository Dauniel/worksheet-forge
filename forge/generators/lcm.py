"""Least common multiple, and prime factorization.

The natural twin of ``gcf``: same shape, same exact-integer answers. LCM is
built from a shared factor and two coprime cofactors, so the answer is
predictable and never accidentally equal to one of the inputs.
"""
from __future__ import annotations

import math
import random

import sympy as sp

from ..core.latexfmt import coeff
from ..core.problem import Problem
from ..core.registry import register

X = sp.Symbol("x")
SHARED = {"easy": (2, 8), "medium": (2, 12), "hard": (3, 18)}
COFACTOR = {"easy": (2, 9), "medium": (2, 14), "hard": (3, 20)}
# Numbers to factor into primes. Kept modest so the factor tree stays short.
FACTOR_TARGET = {"easy": (12, 140), "medium": (40, 400), "hard": (120, 1200)}


def _coprime_pair(rng: random.Random, difficulty: str):
    lo, hi = COFACTOR[difficulty]
    while True:
        a, b = rng.randint(lo, hi), rng.randint(lo, hi)
        if a != b and math.gcd(a, b) == 1:
            return a, b


def _mk(question, answer, subskill, difficulty, kind):
    return Problem(
        question_latex=f"${question}$",
        answer_latex=f"${sp.latex(answer)}$",
        answer_expr=answer,
        topic="lcm",
        subskill=subskill,
        difficulty=difficulty,
        verify={"kind": kind},
    )


@register("lcm", "numerical")
def numerical(rng: random.Random, difficulty: str) -> Problem:
    g = rng.randint(*SHARED[difficulty])
    a, b = _coprime_pair(rng, difficulty)
    return _mk(rf"\operatorname{{LCM}}\left({g * a}, {g * b}\right)",
               sp.Integer(g * a * b), "numerical", difficulty, "lcm")


@register("lcm", "monomial")
def monomial(rng: random.Random, difficulty: str) -> Problem:
    """LCM of two monomials: the larger power of x, times the numeric LCM."""
    g = rng.randint(*SHARED[difficulty])
    a, b = _coprime_pair(rng, difficulty)
    p, q = rng.randint(1, 4), rng.randint(1, 4)
    if p == q:
        q = p + 1
    left, right = coeff(g * a, rf"x^{{{p}}}"), coeff(g * b, rf"x^{{{q}}}")
    return _mk(rf"\operatorname{{LCM}}\left({left}, {right}\right)",
               sp.Integer(g * a * b) * X**max(p, q), "monomial", difficulty, "lcm")


@register("lcm", "prime_factorization")
def prime_factorization(rng: random.Random, difficulty: str) -> Problem:
    """Write a number as a product of primes, in exponent form.

    The target is sampled and then rejected unless it is composite -- a prime
    would make the answer the number itself, which teaches nothing.
    """
    lo, hi = FACTOR_TARGET[difficulty]
    n = rng.randint(lo, hi)
    while sp.isprime(n):
        n = rng.randint(lo, hi)
    factors = sp.factorint(n)
    parts = [
        f"{base}" if power == 1 else f"{base}^{{{power}}}"
        for base, power in sorted(factors.items())
    ]
    answer_text = r" \times ".join(parts)
    return Problem(
        question_latex=f"${n}$",
        answer_latex=f"${answer_text}$",
        answer_expr=sp.Integer(n),
        topic="lcm",
        subskill="prime_factorization",
        difficulty=difficulty,
        verify={"kind": "prime_factorization"},
    )
