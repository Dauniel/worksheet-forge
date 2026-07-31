"""Square roots, cube roots, and simplifying radicals (pre-algebra level)."""

from __future__ import annotations

import random

import sympy as sp

from ..core.problem import Problem
from ..core.registry import register
from ..core.sampling import pick

SQUARE_BASE = {"easy": (2, 35), "medium": (2, 50), "hard": (2, 70)}
CUBE_BASE = {"easy": (2, 30), "medium": (2, 45), "hard": (2, 60)}
# sqrt(a^2 * b) -> a*sqrt(b): sample a squarefree radicand b and a coefficient a.
RADICAND_MAX = {"easy": 20, "medium": 30, "hard": 45}
COEF_MAX = {"easy": (2, 6), "medium": (2, 8), "hard": (2, 10)}


def _is_squarefree(n: int) -> bool:
    i = 2
    while i * i <= n:
        if n % i == 0:
            n //= i
            if n % i == 0:
                return False
        i += 1
    return True


def _squarefree(rng: random.Random, hi: int) -> int:
    while True:
        n = rng.randint(2, hi)
        if _is_squarefree(n):
            return n


def _mk(question: str, value, subskill: str, difficulty: str) -> Problem:
    return Problem(
        question_latex=f"${question}$",
        answer_latex=f"${sp.latex(value)}$",
        answer_expr=value,
        topic="roots",
        subskill=subskill,
        difficulty=difficulty,
        verify={"kind": "evaluate"},
    )


@register("roots", "square_root")
def square_root(rng: random.Random, difficulty: str) -> Problem:
    lo, hi = SQUARE_BASE[difficulty]
    n = rng.randint(lo, hi)
    sign = pick(rng, (1, -1))
    question = rf"{'-' if sign < 0 else ''}\sqrt{{{n * n}}}"
    return _mk(question, sp.Integer(sign * n), "square_root", difficulty)


@register("roots", "cube_root")
def cube_root(rng: random.Random, difficulty: str) -> Problem:
    lo, hi = CUBE_BASE[difficulty]
    n = rng.randint(lo, hi) * pick(rng, (1, -1))
    question = rf"\sqrt[3]{{{n ** 3}}}"
    return _mk(question, sp.Integer(n), "cube_root", difficulty)


@register("roots", "simplify_radical")
def simplify_radical(rng: random.Random, difficulty: str) -> Problem:
    b = _squarefree(rng, RADICAND_MAX[difficulty])
    a = rng.randint(*COEF_MAX[difficulty])
    k = a * a * b
    question = rf"\sqrt{{{k}}}"
    value = a * sp.sqrt(b)
    return _mk(question, value, "simplify_radical", difficulty)
