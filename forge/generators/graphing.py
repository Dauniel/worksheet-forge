"""Graphing linear inequalities and systems of inequalities.

Verified by point-testing rather than by rendering a shaded region: a printed
worksheet is graphed by hand, so there is no pixel output to check against.
Both subskills ask whether a given point lies in the solution set of one
inequality (or, for systems, of both at once) -- exactly the reasoning a
student uses to decide which side of the boundary line to shade.
"""

from __future__ import annotations

import random

from ..core.latexfmt import linear
from ..core.problem import Problem
from ..core.registry import register
from ..core.sampling import nonzero_int, pick

RANGES = {"easy": (1, 6), "medium": (2, 9), "hard": (2, 12)}
RELS = {"<": "<", "<=": r"\le", ">": ">", ">=": r"\ge"}
_TEST = {
    "<": lambda l, r: l < r,
    "<=": lambda l, r: l <= r,
    ">": lambda l, r: l > r,
    ">=": lambda l, r: l >= r,
}


@register("graphing", "point_in_solution")
def point_in_solution(rng: random.Random, difficulty: str) -> Problem:
    _, hi = RANGES[difficulty]
    m = nonzero_int(rng, -hi, hi)
    b = nonzero_int(rng, -hi, hi)
    rel = pick(rng, ("<", "<=", ">", ">="))
    px = nonzero_int(rng, -hi, hi)
    py = nonzero_int(rng, -hi, hi)

    is_sol = _TEST[rel](py, m * px + b)
    question = rf"$y {RELS[rel]} {linear(m, b)}$; is $({px}, {py})$ a solution?"
    answer = "Yes" if is_sol else "No"

    return Problem(
        question_latex=question,
        answer_latex=f"${answer}$",
        answer_expr="Yes" if is_sol else "No",
        topic="graphing",
        subskill="point_in_solution",
        difficulty=difficulty,
        verify={"kind": "point_in_inequality"},
    )


@register("graphing", "system_point_in_solution")
def system_point_in_solution(rng: random.Random, difficulty: str) -> Problem:
    _, hi = RANGES[difficulty]
    m1, b1 = nonzero_int(rng, -hi, hi), nonzero_int(rng, -hi, hi)
    m2, b2 = nonzero_int(rng, -hi, hi), nonzero_int(rng, -hi, hi)
    rel1 = pick(rng, ("<", "<=", ">", ">="))
    rel2 = pick(rng, ("<", "<=", ">", ">="))
    px = nonzero_int(rng, -hi, hi)
    py = nonzero_int(rng, -hi, hi)

    is_sol = _TEST[rel1](py, m1 * px + b1) and _TEST[rel2](py, m2 * px + b2)
    question = (
        rf"$\begin{{cases}} y {RELS[rel1]} {linear(m1, b1)} \\ "
        rf"y {RELS[rel2]} {linear(m2, b2)} \end{{cases}}$; is $({px}, {py})$ a solution?"
    )
    answer = "Yes" if is_sol else "No"

    return Problem(
        question_latex=question,
        answer_latex=f"${answer}$",
        answer_expr="Yes" if is_sol else "No",
        topic="graphing",
        subskill="system_point_in_solution",
        difficulty=difficulty,
        verify={"kind": "system_point_in_inequality"},
    )
