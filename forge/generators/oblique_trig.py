"""Law of sines and law of cosines, restricted to the exact cases.

A triangle with arbitrary angles has irrational sides that only a calculator
can produce, and an answer key full of 12.437 cannot be verified exactly.
Both subskills here follow the same restriction ``right_triangle_trig``
already documents: use only the configurations whose ratios stay exact.

- *Law of cosines* uses an included angle of 60 or 120 degrees, where
  ``cos`` is exactly 1/2 or -1/2, so ``c^2 = a^2 + b^2 -/+ ab`` is an
  integer and ``c`` is an integer or a clean radical.
- *Law of sines* uses angle pairs whose sines are in rational proportion --
  30/90, 30/150, 45/135 and their reverses -- so the unknown side is exact.

Answers are left symbolic (``7\\sqrt{3}``), never decimalised.
"""

from __future__ import annotations

import random

import sympy as sp

from ..core.problem import Problem
from ..core.registry import register
from ..core.sampling import pick

SIDE = {"easy": (2, 10), "medium": (3, 16), "hard": (4, 24)}
# Included angles with an exact cosine of +/- 1/2.
COS_ANGLES = (60, 120)
# (angle_A, angle_B) pairs whose sines are in exact rational proportion, so
# b = a * sin(B) / sin(A) stays exact.
SINE_PAIRS = ((30, 90), (90, 30), (30, 150), (150, 30), (45, 135), (135, 45))


def _mk(question: str, value, subskill: str, difficulty: str, kind: str) -> Problem:
    return Problem(
        question_latex=question,
        answer_latex=f"${sp.latex(value)}$",
        answer_expr=value,
        topic="oblique_trig",
        subskill=subskill,
        difficulty=difficulty,
        verify={"kind": kind},
    )


@register("oblique_trig", "law_of_cosines")
def law_of_cosines(rng: random.Random, difficulty: str) -> Problem:
    """Two sides and the included angle; find the third side."""
    lo, hi = SIDE[difficulty]
    a = rng.randint(lo, hi)
    b = rng.randint(lo, hi)
    angle = pick(rng, COS_ANGLES)
    cos_c = sp.Rational(1, 2) if angle == 60 else sp.Rational(-1, 2)

    c_squared = sp.Integer(a) ** 2 + sp.Integer(b) ** 2 - 2 * a * b * cos_c
    c = sp.sqrt(c_squared)

    question = (
        f"In triangle $ABC$, $a = {a}$, $b = {b}$, and the included angle "
        f"$C = {angle}^\\circ$. Find $c$."
    )
    return _mk(question, sp.nsimplify(c), "law_of_cosines", difficulty,
               "trig_law_of_cosines")


@register("oblique_trig", "law_of_sines")
def law_of_sines(rng: random.Random, difficulty: str) -> Problem:
    """One side and two angles; find the side opposite the second angle."""
    lo, hi = SIDE[difficulty]
    angle_a, angle_b = pick(rng, SINE_PAIRS)
    a = rng.randint(lo, hi)

    sin_a = sp.sin(sp.rad(angle_a))
    sin_b = sp.sin(sp.rad(angle_b))
    b = sp.nsimplify(a * sin_b / sin_a)

    question = (
        f"In triangle $ABC$, $A = {angle_a}^\\circ$, $B = {angle_b}^\\circ$, "
        f"and $a = {a}$. Find $b$."
    )
    return _mk(question, b, "law_of_sines", difficulty, "trig_law_of_sines")
