"""Coordinate geometry: distance, midpoint, and transformations of a point.

Distance uses Pythagorean triples for the leg differences, so the result is a
whole number rather than a radical -- the same restriction the Pythagorean
subskills in ``geometry`` use, and for the same reason.

Midpoints are drawn from endpoints of matching parity so the answer never
lands on a half. Transformations are exact integer arithmetic.
"""

from __future__ import annotations

import random

import sympy as sp

from ..core.problem import Problem
from ..core.registry import register
from ..core.sampling import nonzero_int, pick

SPAN = {"easy": 8, "medium": 14, "hard": 20}
TRIPLES = ((3, 4, 5), (6, 8, 10), (5, 12, 13), (8, 15, 17), (20, 21, 29), (7, 24, 25))


def _mk(question: str, answer_latex: str, answer_expr, subskill: str,
        difficulty: str, kind: str) -> Problem:
    return Problem(
        question_latex=question,
        answer_latex=answer_latex,
        answer_expr=answer_expr,
        topic="coordinate",
        subskill=subskill,
        difficulty=difficulty,
        verify={"kind": kind},
    )


@register("coordinate", "distance")
def distance(rng: random.Random, difficulty: str) -> Problem:
    """Whole-number distance: the leg differences form a Pythagorean triple."""
    a, b, c = pick(rng, TRIPLES)
    if rng.random() < 0.5:
        a, b = b, a
    span = SPAN[difficulty]
    x1, y1 = rng.randint(-span, span), rng.randint(-span, span)
    x2 = x1 + (a if rng.random() < 0.5 else -a)
    y2 = y1 + (b if rng.random() < 0.5 else -b)

    question = f"$({x1}, {y1})$ and $({x2}, {y2})$"
    return _mk(question, f"${c}$", sp.Integer(c), "distance", difficulty,
               "coord_distance")


@register("coordinate", "midpoint")
def midpoint(rng: random.Random, difficulty: str) -> Problem:
    """Endpoints share parity per axis, so the midpoint stays an integer."""
    span = SPAN[difficulty]
    x1, y1 = rng.randint(-span, span), rng.randint(-span, span)
    x2 = x1 + 2 * nonzero_int(rng, -span // 2, span // 2)
    y2 = y1 + 2 * nonzero_int(rng, -span // 2, span // 2)
    mx, my = (x1 + x2) // 2, (y1 + y2) // 2

    question = f"$({x1}, {y1})$ and $({x2}, {y2})$"
    return _mk(question, f"$({mx}, {my})$", (mx, my), "midpoint", difficulty,
               "coord_midpoint")


@register("coordinate", "translate_point")
def translate_point(rng: random.Random, difficulty: str) -> Problem:
    span = SPAN[difficulty]
    x, y = rng.randint(-span, span), rng.randint(-span, span)
    dx, dy = nonzero_int(rng, -span, span), nonzero_int(rng, -span, span)
    horizontal = f"right {dx}" if dx > 0 else f"left {-dx}"
    vertical = f"up {dy}" if dy > 0 else f"down {-dy}"

    question = f"Translate $({x}, {y})$ {horizontal} and {vertical}."
    return _mk(question, f"$({x + dx}, {y + dy})$", (x + dx, y + dy),
               "translate_point", difficulty, "coord_translate")


@register("coordinate", "reflect_point")
def reflect_point(rng: random.Random, difficulty: str) -> Problem:
    """Reflect over the x-axis, the y-axis, or (at hard) the line y = x."""
    span = SPAN[difficulty]
    x, y = nonzero_int(rng, -span, span), nonzero_int(rng, -span, span)
    axes = ["the $x$-axis", "the $y$-axis"]
    if difficulty == "hard":
        axes.append("the line $y = x$")
    axis = pick(rng, tuple(axes))

    if "x$-axis" in axis:
        image = (x, -y)
    elif "y$-axis" in axis:
        image = (-x, y)
    else:
        image = (y, x)

    question = f"Reflect $({x}, {y})$ over {axis}."
    return _mk(question, f"$({image[0]}, {image[1]})$", image, "reflect_point",
               difficulty, "coord_reflect")
