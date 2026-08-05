"""Absolute value equations and evaluation, built backwards from the roots.

``|ax + b| = c`` has two solutions ``s1 < s2``. Choosing the solutions first
and deriving ``b`` and ``c`` from them (rather than picking ``b``/``c`` and
solving) guarantees clean integer roots and rules out the degenerate
``c < 0`` (no solution) case entirely.
"""

from __future__ import annotations

import random
from fractions import Fraction

import sympy as sp

from ..core.latexfmt import dnum, linear, num, terms
from ..core.problem import Problem
from ..core.registry import register
from ..core.sampling import nonzero_int

X = sp.Symbol("x")
RANGES = {"easy": (1, 9), "medium": (2, 14), "hard": (3, 18)}
EVAL_HI = {"easy": 9, "medium": 14, "hard": 20}
INEQ_HI = {"easy": (1, 9), "medium": (2, 12), "hard": (2, 15)}


def _same_parity_pair(rng: random.Random, hi: int) -> tuple[int, int]:
    """Two distinct integers of matching parity in [-hi, hi] \\ {0}, sorted.

    Matching parity keeps ``(s1 + s2) / 2`` and ``(s2 - s1) / 2`` exact
    integers, so ``b`` and ``c`` never come out fractional.
    """
    while True:
        s1 = nonzero_int(rng, -hi, hi)
        s2 = nonzero_int(rng, -hi, hi)
        if s1 != s2 and (s1 + s2) % 2 == 0:
            return tuple(sorted((s1, s2)))


def _mk_general(lhs: str, rhs: str, subskill: str, difficulty: str,
                 s1: int, s2: int) -> Problem:
    return Problem(
        question_latex=f"${lhs} = {rhs}$",
        answer_latex=rf"$x = {s1} \text{{ or }} x = {s2}$",
        answer_expr=[sp.Integer(s1), sp.Integer(s2)],
        topic="absolute_value",
        subskill=subskill,
        difficulty=difficulty,
        verify={
            "kind": "abs_solve",
            "var": "x",
            "lhs": lhs,
            "rhs": rhs,
        },
    )


def _mk_solve(a: int, b: int, c: int, subskill: str, difficulty: str,
              s1: int, s2: int) -> Problem:
    body = linear(a, b)
    return _mk_general(f"|{body}|", str(c), subskill, difficulty, s1, s2)


@register("absolute_value", "solve_basic")
def solve_basic(rng: random.Random, difficulty: str) -> Problem:
    _, hi = RANGES[difficulty]
    s1, s2 = _same_parity_pair(rng, hi)
    b = -(s1 + s2) // 2
    c = (s2 - s1) // 2
    return _mk_solve(1, b, c, "solve_basic", difficulty, s1, s2)


@register("absolute_value", "solve_with_coefficient")
def solve_with_coefficient(rng: random.Random, difficulty: str) -> Problem:
    _, hi = RANGES[difficulty]
    s1, s2 = _same_parity_pair(rng, hi)
    a = rng.randint(2, 5)
    b = -a * (s1 + s2) // 2
    c = a * (s2 - s1) // 2
    return _mk_solve(a, b, c, "solve_with_coefficient", difficulty, s1, s2)


@register("absolute_value", "multi_step")
def multi_step(rng: random.Random, difficulty: str) -> Problem:
    """``|x + b|`` wrapped in an outer term that must be undone first.

    Two shapes: ``k|x + b| + m = RHS`` (undo the added/subtracted ``m``, then
    divide out ``k``) and ``|x + b|/d + m = RHS`` (undo ``m``, then multiply
    out the denominator) -- either way ``|x + b| = c`` only appears after an
    extra step, unlike solve_basic/solve_with_coefficient where the bars are
    already isolated.
    """
    _, hi = RANGES[difficulty]
    s1, s2 = _same_parity_pair(rng, hi)
    b = -(s1 + s2) // 2
    c = (s2 - s1) // 2
    inner = linear(1, b)
    m = nonzero_int(rng, -hi, hi)

    if rng.random() < 0.5:
        k = rng.randint(2, 5)
        lhs = terms(f"{k}|{inner}|", num(m))
        rhs = num(k * c + m)
    else:
        d = rng.randint(2, 5)
        lhs = terms(rf"\dfrac{{|{inner}|}}{{{d}}}", num(m))
        rhs = dnum(Fraction(c, d) + m)

    return _mk_general(lhs, rhs, "multi_step", difficulty, s1, s2)


@register("absolute_value", "evaluate")
def evaluate(rng: random.Random, difficulty: str) -> Problem:
    hi = EVAL_HI[difficulty]
    a1, b1 = nonzero_int(rng, -hi, hi), nonzero_int(rng, -hi, hi)
    a2, b2 = nonzero_int(rng, -hi, hi), nonzero_int(rng, -hi, hi)
    inner1 = terms(num(a1), num(b1))
    inner2 = terms(num(a2), num(b2))
    coef2 = rng.randint(1, 3)
    coef_txt = "" if coef2 == 1 else str(coef2)
    op = rng.choice(("+", "-"))

    value1 = abs(a1 + b1)
    value2 = abs(a2 + b2)
    result = value1 + coef2 * value2 if op == "+" else value1 - coef2 * value2

    return Problem(
        question_latex=f"$|{inner1}| {op} {coef_txt}|{inner2}|$",
        answer_latex=f"${result}$",
        answer_expr=sp.Integer(result),
        topic="absolute_value",
        subskill="evaluate",
        difficulty=difficulty,
        verify={"kind": "evaluate"},
    )


@register("absolute_value", "solve_inequality")
def solve_inequality(rng: random.Random, difficulty: str) -> Problem:
    """``|a x + b| REL c`` (``a > 0``), with ``b`` and ``c`` chosen as
    multiples of ``a`` so the solution boundaries are always clean integers,
    never a fraction.
    """
    _, hi = INEQ_HI[difficulty]
    a = rng.randint(1, 3) if difficulty != "easy" else 1
    p = nonzero_int(rng, -hi, hi)
    q = rng.randint(1, hi)
    b, c = a * p, a * q
    rel = rng.choice(("<", "<=", ">", ">="))
    rel_latex = {"<": "<", "<=": r"\le", ">": ">", ">=": r"\ge"}[rel]

    lo, hi_bound = -(p + q), q - p  # both plain integers by construction
    body = linear(a, b)
    question = f"|{body}| {rel_latex} {c}"

    if rel in ("<", "<="):
        cmp = "<" if rel == "<" else r"\le"
        answer = f"{lo} {cmp} x {cmp} {hi_bound}"
    else:
        lt = "<" if rel == ">" else r"\le"
        gt = ">" if rel == ">" else r"\ge"
        answer = rf"x {lt} {lo} \text{{ or }} x {gt} {hi_bound}"

    return Problem(
        question_latex=f"${question}$",
        answer_latex=f"${answer}$",
        answer_expr=None,
        topic="absolute_value",
        subskill="solve_inequality",
        difficulty=difficulty,
        verify={"kind": "abs_inequality", "var": "x", "answer_check": None},
    )
