"""Area, and volume/surface area of rectangular and triangular prisms only.

Every dimension is sampled from ``rng``; the figure is rendered by
``forge/core/tikz.py`` directly from those same sampled numbers, so the
picture and the answer key can never disagree. Verification
(`forge/core/verify.py`) re-reads the printed *labels* out of the rendered
LaTeX (the ``$n$`` tokens drawn on the figure) and re-applies the formula
independently of whatever the generator computed.
"""

from __future__ import annotations

import random

import sympy as sp

from ..core import tikz
from ..core.problem import Problem
from ..core.registry import register
from ..core.sampling import pick

UNITS = ("units", "cm", "in", "ft", "m")

# area_square samples a single dimension, so it needs a slightly wider range
# on its own to stay varied; the other shapes combine 2-4 independent samples
# and stay in a modest, legible, grade-appropriate range. The bands still
# overlap for that reason -- but they do have to differ, or the subskill
# accepts a difficulty and ignores it.
SQUARE_SIZE = {"easy": (2, 12), "medium": (4, 18), "hard": (6, 25)}
SIZE = {"easy": (3, 10), "medium": (4, 14), "hard": (6, 18)}
LENGTH = {"easy": (2, 6), "medium": (3, 8), "hard": (4, 10)}
# Radii stay small: the answer is an exact multiple of pi (r^2 for area), so
# hard already reaches 225*pi without the arithmetic leaving mental range.
RADIUS = {"easy": (1, 8), "medium": (2, 12), "hard": (3, 15)}
# Small, well-proportioned Pythagorean triples only -- nothing that draws as
# an unusable sliver.
_PRIMITIVE_TRIPLES = ((3, 4, 5), (6, 8, 10), (5, 12, 13), (8, 15, 17))
# medium and hard were identical here, so the two triangular-prism subskills
# accepted a difficulty and ignored it -- the same latent bug exponents.py:19
# records. Magnitude is free to grow: tikz._scale normalizes every figure to a
# fixed target size, so only the triple's aspect ratio affects drawability and
# scaling it uniformly leaves that untouched. Hard always scales up, so its
# smallest base is 6-8-10 rather than 3-4-5.
SCALE = {"easy": (1,), "medium": (1, 2), "hard": (2, 3)}


def _triple(rng: random.Random, difficulty: str):
    a, b, c = pick(rng, _PRIMITIVE_TRIPLES)
    k = pick(rng, SCALE[difficulty])
    return a * k, b * k, c * k


def _proportioned_even(rng: random.Random, base: int, lo_ratio: float, hi_ratio: float) -> int:
    """An even integer within [base*lo_ratio, base*hi_ratio] (at least 2).

    Keeps a drawn height in reasonable proportion to its base -- no more
    towers or slivers -- while still landing on an exact half-integer area.
    """
    lo = max(2, round(base * lo_ratio))
    hi = max(lo, round(base * hi_ratio))
    lo += lo % 2
    hi -= hi % 2
    if hi < lo:
        hi = lo
    return rng.randrange(lo, hi + 1, 2)


def _proportioned(rng: random.Random, base: int, lo_ratio: float, hi_ratio: float) -> int:
    """An integer with value/base in [lo_ratio, hi_ratio]."""
    lo = max(1, round(base * lo_ratio))
    hi = max(lo, round(base * hi_ratio))
    return rng.randint(lo, hi)


def _circle_dims(rng: random.Random, difficulty: str):
    """Return ``(radius, labeled_value, is_diameter)`` for a circle figure.

    Half the time the figure is labeled with a diameter instead of a radius,
    which is the step students actually miss -- halving before squaring. The
    diameter case draws an even value so the radius stays a whole number and
    the answer stays an exact multiple of pi.
    """
    lo, hi = RADIUS[difficulty]
    r = rng.randint(lo, hi)
    if rng.random() < 0.5:
        return r, 2 * r, True
    return r, r, False


def _mk(question: str, value, subskill: str, difficulty: str, kind: str, unit_word: str) -> Problem:
    value = sp.nsimplify(value)
    answer_latex = f"${sp.latex(value)}$ {unit_word}"
    return Problem(
        question_latex=question,
        answer_latex=answer_latex,
        answer_expr=value,
        topic="geometry",
        subskill=subskill,
        difficulty=difficulty,
        verify={"kind": kind},
    )


def _caption(unit: str, note: str = "") -> str:
    """The only authored text on a geometry problem: names the solid (when it
    isn't obvious from the section) and states the unit -- never a dimension,
    since every dimension is read straight off the figure."""
    lead = f"{note} " if note else ""
    return f"{lead}All measurements are in {unit}.\n"


@register("geometry", "area_rectangle")
def area_rectangle(rng: random.Random, difficulty: str) -> Problem:
    lo, hi = SIZE[difficulty]
    l, w = rng.randint(lo, hi), rng.randint(lo, hi)
    unit = pick(rng, UNITS)
    question = _caption(unit) + tikz.rectangle_fig(l, w)
    return _mk(question, l * w, "area_rectangle", difficulty, "geo_rectangle_area", f"square {unit}")


@register("geometry", "area_square")
def area_square(rng: random.Random, difficulty: str) -> Problem:
    lo, hi = SQUARE_SIZE[difficulty]
    s = rng.randint(lo, hi)
    unit = pick(rng, UNITS)
    question = _caption(unit) + tikz.square_fig(s)
    return _mk(question, s * s, "area_square", difficulty, "geo_square_area", f"square {unit}")


@register("geometry", "area_circle")
def area_circle(rng: random.Random, difficulty: str) -> Problem:
    r, value, is_d = _circle_dims(rng, difficulty)
    unit = pick(rng, UNITS)
    question = _caption(unit) + tikz.circle_fig(value, is_d)
    return _mk(question, sp.pi * r**2, "area_circle", difficulty,
               "geo_circle_area", f"square {unit}")


@register("geometry", "circumference_circle")
def circumference_circle(rng: random.Random, difficulty: str) -> Problem:
    r, value, is_d = _circle_dims(rng, difficulty)
    unit = pick(rng, UNITS)
    question = _caption(unit) + tikz.circle_fig(value, is_d)
    return _mk(question, 2 * sp.pi * r, "circumference_circle", difficulty,
               "geo_circle_circumference", unit)


@register("geometry", "area_triangle")
def area_triangle(rng: random.Random, difficulty: str) -> Problem:
    lo, hi = SIZE[difficulty]
    b = rng.randint(lo, hi)
    h = _proportioned_even(rng, b, 0.5, 1.6)
    unit = pick(rng, UNITS)
    question = _caption(unit) + tikz.triangle_fig(b, h)
    return _mk(question, sp.Rational(b * h, 2), "area_triangle", difficulty, "geo_triangle_area", f"square {unit}")


@register("geometry", "area_trapezoid")
def area_trapezoid(rng: random.Random, difficulty: str) -> Problem:
    lo, hi = SIZE[difficulty]
    b1 = rng.randint(lo, hi)
    b2 = _proportioned(rng, b1, 0.5, 1.8)
    h = _proportioned_even(rng, (b1 + b2) // 2, 0.5, 1.6)
    unit = pick(rng, UNITS)
    question = _caption(unit) + tikz.trapezoid_fig(b1, b2, h)
    return _mk(question, sp.Rational((b1 + b2) * h, 2), "area_trapezoid", difficulty,
               "geo_trapezoid_area", f"square {unit}")


@register("geometry", "volume_rect_prism")
def volume_rect_prism(rng: random.Random, difficulty: str) -> Problem:
    lo, hi = SIZE[difficulty]
    l, w, h = rng.randint(lo, hi), rng.randint(lo, hi), rng.randint(lo, hi)
    unit = pick(rng, UNITS)
    question = _caption(unit, "A rectangular prism.") + tikz.rect_prism_fig(l, w, h)
    return _mk(question, l * w * h, "volume_rect_prism", difficulty, "geo_rect_prism_volume", f"cubic {unit}")


@register("geometry", "surface_area_rect_prism")
def surface_area_rect_prism(rng: random.Random, difficulty: str) -> Problem:
    lo, hi = SIZE[difficulty]
    l, w, h = rng.randint(lo, hi), rng.randint(lo, hi), rng.randint(lo, hi)
    unit = pick(rng, UNITS)
    question = _caption(unit, "A rectangular prism.") + tikz.rect_prism_fig(l, w, h)
    value = 2 * (l * w + l * h + w * h)
    return _mk(question, value, "surface_area_rect_prism", difficulty, "geo_rect_prism_sa", f"square {unit}")


@register("geometry", "volume_tri_prism")
def volume_tri_prism(rng: random.Random, difficulty: str) -> Problem:
    a, b, c = _triple(rng, difficulty)
    lo, hi = LENGTH[difficulty]
    length = rng.randint(lo, hi)
    unit = pick(rng, UNITS)
    question = (
        _caption(unit, "A triangular prism with a right-triangle base.")
        + tikz.tri_prism_fig(a, b, c, length)
    )
    value = sp.Rational(a * b, 2) * length
    return _mk(question, value, "volume_tri_prism", difficulty, "geo_tri_prism_volume", f"cubic {unit}")


@register("geometry", "surface_area_tri_prism")
def surface_area_tri_prism(rng: random.Random, difficulty: str) -> Problem:
    a, b, c = _triple(rng, difficulty)
    lo, hi = LENGTH[difficulty]
    length = rng.randint(lo, hi)
    unit = pick(rng, UNITS)
    question = (
        _caption(unit, "A triangular prism with a right-triangle base.")
        + tikz.tri_prism_fig(a, b, c, length)
    )
    value = a * b + (a + b + c) * length
    return _mk(question, value, "surface_area_tri_prism", difficulty, "geo_tri_prism_sa", f"square {unit}")
