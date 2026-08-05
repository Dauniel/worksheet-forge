"""Degree/radian conversion and exact trig values at standard angles.

Both subskills draw from a small, fixed set of "nice" angles (multiples of
30 or 45 degrees) so every conversion and every trig value is exact -- never
a decimal approximation.
"""

from __future__ import annotations

import random
from fractions import Fraction

import sympy as sp

from ..core.problem import Problem
from ..core.registry import register
from ..core.sampling import pick

DEGREES = (0, 30, 45, 60, 90, 120, 135, 150, 180, 210, 225, 240, 270, 300, 315, 330, 360)
TRIG_ANGLES = (0, 30, 45, 60, 90, 120, 135, 150, 180, 210, 225, 240, 270, 300, 315, 330)
FUNCS = {"sin": sp.sin, "cos": sp.cos, "tan": sp.tan}


@register("unit_circle", "degree_radian_conversion")
def degree_radian_conversion(rng: random.Random, difficulty: str) -> Problem:
    deg = pick(rng, DEGREES)
    frac = Fraction(deg, 180)
    direction = rng.choice(("to_radians", "to_degrees"))

    rad_latex = _pi_fraction_latex(frac)
    if direction == "to_radians":
        question = f"${deg}^\\circ$"
        answer = rad_latex
        answer_expr = sp.Rational(frac.numerator, frac.denominator) * sp.pi
    else:
        question = f"${rad_latex}$"
        answer = f"{deg}^\\circ"
        answer_expr = sp.Integer(deg)

    return Problem(
        question_latex=question,
        answer_latex=f"${answer}$",
        answer_expr=answer_expr,
        topic="unit_circle",
        subskill="degree_radian_conversion",
        difficulty=difficulty,
        verify={"kind": "degree_radian_conversion", "direction": direction},
    )


def _pi_fraction_latex(frac: Fraction) -> str:
    if frac == 0:
        return "0"
    n, d = frac.numerator, frac.denominator
    coef = "" if n == 1 else ("-" if n == -1 else str(n))
    pi = r"\pi"
    return rf"\dfrac{{{coef}{pi}}}{{{d}}}" if d != 1 else f"{coef}{pi}"


@register("unit_circle", "exact_trig_value")
def exact_trig_value(rng: random.Random, difficulty: str) -> Problem:
    angle = pick(rng, TRIG_ANGLES)
    func = pick(rng, ("sin", "cos", "tan"))
    while func == "tan" and angle in (90, 270):  # undefined
        angle = pick(rng, TRIG_ANGLES)

    value = sp.nsimplify(FUNCS[func](sp.rad(angle)))
    question = rf"\{func}({angle}^\circ)"

    return Problem(
        question_latex=f"${question}$",
        answer_latex=f"${sp.latex(value)}$",
        answer_expr=value,
        topic="unit_circle",
        subskill="exact_trig_value",
        difficulty=difficulty,
        verify={"kind": "exact_trig_value"},
    )
