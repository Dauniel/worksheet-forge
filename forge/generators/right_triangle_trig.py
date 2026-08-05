"""Special right triangles (30-60-90, 45-45-90) and inverse-trig angle finding.

Every triangle is built from an integer scale factor applied to the
triangle's fixed side ratio, so every side length is exact -- an integer or a
clean radical, never a decimal requiring a calculator. ``find_angle`` is
restricted to the three (ratio, angle) pairs among 30/45/60 degrees whose
side ratio is itself a ratio of small integers -- tan(45)=1, sin(30)=1/2,
cos(60)=1/2 -- every other pairing (e.g. tan(30), sin(60)) is irrational and
would need a radical side length, which isn't worth the formatting
complexity for this subskill.
"""

from __future__ import annotations

import random

import sympy as sp

from ..core.problem import Problem
from ..core.registry import register
from ..core.sampling import pick

SCALE = {"easy": (1, 25), "medium": (1, 35), "hard": (1, 45)}
ANGLE_SCALE = {"easy": (1, 20), "medium": (1, 35), "hard": (1, 50)}


@register("right_triangle_trig", "special_triangle_hypotenuse")
def special_triangle_hypotenuse(rng: random.Random, difficulty: str) -> Problem:
    """Given the reference leg of a 30-60-90 or 45-45-90 triangle, find the
    hypotenuse -- an integer for 30-60-90, a clean radical for 45-45-90."""
    _, hi = SCALE[difficulty]
    k = rng.randint(1, hi)
    kind = rng.choice(("30-60-90", "45-45-90"))

    if kind == "30-60-90":
        leg = k
        hyp_latex = str(2 * k)
        hyp_expr = sp.Integer(2 * k)
        text = (
            rf"A right triangle is a $30$-$60$-$90$ triangle. The side "
            rf"opposite the $30^\circ$ angle has length ${leg}$. Find the "
            rf"length of the hypotenuse."
        )
    else:
        leg = k
        hyp_expr = sp.sqrt(2) * k
        hyp_latex = sp.latex(hyp_expr)
        text = (
            rf"A right triangle is a $45$-$45$-$90$ triangle. A leg has "
            rf"length ${leg}$. Find the length of the hypotenuse."
        )

    return Problem(
        question_latex=text,
        answer_latex=f"${hyp_latex}$",
        answer_expr=hyp_expr,
        topic="right_triangle_trig",
        subskill="special_triangle_hypotenuse",
        difficulty=difficulty,
        verify={"kind": "special_triangle_hypotenuse"},
    )


_CLEAN_RATIOS = (
    ("tan", 45, 1, 1),  # opposite : adjacent = 1 : 1
    ("sin", 30, 1, 2),  # opposite : hypotenuse = 1 : 2
    ("cos", 60, 1, 2),  # adjacent : hypotenuse = 1 : 2
)


@register("right_triangle_trig", "find_angle")
def find_angle(rng: random.Random, difficulty: str) -> Problem:
    """Two sides in exactly a 1:1 or 1:2 ratio matching tan(45), sin(30), or
    cos(60); find that angle."""
    ratio_kind, angle, num_ratio, den_ratio = pick(rng, _CLEAN_RATIOS)
    lo, hi = ANGLE_SCALE[difficulty]
    k = rng.randint(lo, hi)
    a, b = num_ratio * k, den_ratio * k

    if ratio_kind == "tan":
        text = (
            f"A right triangle has legs of length ${a}$ (opposite) and "
            f"${b}$ (adjacent). Find the angle opposite the first leg, "
            f"in degrees."
        )
    elif ratio_kind == "sin":
        text = (
            f"A right triangle has a leg of length ${a}$ opposite an angle, "
            f"and a hypotenuse of length ${b}$. Find that angle, in degrees."
        )
    else:
        text = (
            f"A right triangle has a leg of length ${a}$ adjacent to an "
            f"angle, and a hypotenuse of length ${b}$. Find that angle, "
            f"in degrees."
        )

    return Problem(
        question_latex=text,
        answer_latex=f"${angle}^\\circ$",
        answer_expr=sp.Integer(angle),
        topic="right_triangle_trig",
        subskill="find_angle",
        difficulty=difficulty,
        verify={"kind": "right_triangle_find_angle"},
    )
