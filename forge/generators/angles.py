"""Angle relationships: complementary, supplementary, vertical, triangles,
polygon interior sums, and parallel lines cut by a transversal.

Every answer is an exact integer in degrees. Angles are sampled and the
missing one derived, so no problem can state an impossible figure -- a
triangle whose given angles already exceed 180, say.
"""

from __future__ import annotations

import random

import sympy as sp

from ..core.problem import Problem
from ..core.registry import register
from ..core.sampling import pick

# Keep angles off the degenerate ends so no missing angle lands on 0.
COMP_RANGE = {"easy": (10, 80), "medium": (5, 85), "hard": (1, 89)}
SUPP_RANGE = {"easy": (20, 160), "medium": (10, 170), "hard": (5, 175)}
SIDES = {"easy": (3, 12), "medium": (5, 18), "hard": (7, 30)}
# The third angle's range -- without this the subskill accepted a difficulty
# and ignored it.
THIRD = {"easy": (30, 90), "medium": (20, 120), "hard": (10, 150)}


def _mk(question: str, value, subskill: str, difficulty: str, kind: str) -> Problem:
    value = sp.Integer(value)
    return Problem(
        question_latex=question,
        answer_latex=f"${value}^\\circ$",
        answer_expr=value,
        topic="angles",
        subskill=subskill,
        difficulty=difficulty,
        verify={"kind": kind},
    )


@register("angles", "complementary")
def complementary(rng: random.Random, difficulty: str) -> Problem:
    a = rng.randint(*COMP_RANGE[difficulty])
    question = (
        f"Two angles are complementary. One measures ${a}^\\circ$. "
        f"Find the other."
    )
    return _mk(question, 90 - a, "complementary", difficulty, "angle_complementary")


@register("angles", "supplementary")
def supplementary(rng: random.Random, difficulty: str) -> Problem:
    a = rng.randint(*SUPP_RANGE[difficulty])
    question = (
        f"Two angles are supplementary. One measures ${a}^\\circ$. "
        f"Find the other."
    )
    return _mk(question, 180 - a, "supplementary", difficulty, "angle_supplementary")


@register("angles", "triangle_missing_angle")
def triangle_missing_angle(rng: random.Random, difficulty: str) -> Problem:
    """Two angles given; the third follows from the 180-degree sum.

    Drawn backwards from the answer so the two given angles can never sum
    past 180 and produce an impossible triangle.
    """
    third = rng.randint(*THIRD[difficulty])
    remaining = 180 - third
    a = rng.randint(5, remaining - 5)
    b = remaining - a
    question = (
        f"Two angles of a triangle measure ${a}^\\circ$ and ${b}^\\circ$. "
        f"Find the third angle."
    )
    return _mk(question, third, "triangle_missing_angle", difficulty,
               "angle_triangle")


@register("angles", "polygon_interior_sum")
def polygon_interior_sum(rng: random.Random, difficulty: str) -> Problem:
    n = rng.randint(*SIDES[difficulty])
    # Bare item: the section directions already say "find the sum", and
    # repeating them per item is exactly what the LaTeX conventions forbid.
    question = f"A polygon with ${n}$ sides."
    return _mk(question, 180 * (n - 2), "polygon_interior_sum", difficulty,
               "angle_polygon_sum")


@register("angles", "vertical_and_transversal")
def vertical_and_transversal(rng: random.Random, difficulty: str) -> Problem:
    """Parallel lines cut by a transversal: corresponding/alternate angles are
    equal, co-interior angles are supplementary."""
    a = rng.randint(*SUPP_RANGE[difficulty])
    relation = pick(rng, (
        ("vertical to", a),
        ("corresponding with", a),
        ("an alternate interior angle with", a),
        ("a co-interior (same-side interior) angle with", 180 - a),
    ))
    name, value = relation
    question = (
        f"Two parallel lines are cut by a transversal. One angle measures "
        f"${a}^\\circ$. Find the angle that is {name} it."
    )
    return _mk(question, value, "vertical_and_transversal", difficulty,
               "angle_transversal")
