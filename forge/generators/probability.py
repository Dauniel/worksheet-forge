"""Simple and compound probability, always as an exact reduced fraction.

Every count is sampled and the answer is a ``Rational``, so nothing is ever
rounded and the verifier recomputes from the printed counts rather than
trusting the generator.

Sentence frames are authored (the one thing CLAUDE.md permits); every colour,
count, and event in them is sampled.
"""

from __future__ import annotations

import random

import sympy as sp

from ..core.problem import Problem
from ..core.registry import register
from ..core.sampling import pick

COUNT = {"easy": (2, 6), "medium": (3, 9), "hard": (4, 14)}
COLORS = ("red", "blue", "green", "yellow", "purple", "orange", "black", "white")
ITEMS = ("marbles", "counters", "tiles", "cubes", "beads")


def _mk(question: str, value, subskill: str, difficulty: str, kind: str) -> Problem:
    value = sp.Rational(value)
    return Problem(
        question_latex=question,
        answer_latex=f"${sp.latex(value)}$",
        answer_expr=value,
        topic="probability",
        subskill=subskill,
        difficulty=difficulty,
        verify={"kind": kind},
    )


@register("probability", "simple_probability")
def simple_probability(rng: random.Random, difficulty: str) -> Problem:
    """One draw from a bag: P(target colour).

    The counts print in a fixed order (target first, then the rest) so the
    verifier can identify the favourable count by position.
    """
    lo, hi = COUNT[difficulty]
    target_color, other_color = rng.sample(COLORS, 2)
    item = pick(rng, ITEMS)
    favourable = rng.randint(lo, hi)
    other = rng.randint(lo, hi)

    question = (
        f"A bag holds ${favourable}$ {target_color} {item} and "
        f"${other}$ {other_color} {item}. One is drawn at random. "
        f"Find the probability that it is {target_color}."
    )
    return _mk(question, sp.Rational(favourable, favourable + other),
               "simple_probability", difficulty, "prob_simple")


@register("probability", "independent_events")
def independent_events(rng: random.Random, difficulty: str) -> Problem:
    """Two draws *with* replacement, so the two draws stay independent.

    With replacement is stated explicitly in the frame -- without it the
    second draw's denominator changes and the problem becomes the dependent
    case, which is a different skill.
    """
    lo, hi = COUNT[difficulty]
    target_color, other_color = rng.sample(COLORS, 2)
    item = pick(rng, ITEMS)
    favourable = rng.randint(lo, hi)
    other = rng.randint(lo, hi)
    total = favourable + other

    question = (
        f"A bag holds ${favourable}$ {target_color} {item} and "
        f"${other}$ {other_color} {item}. One is drawn, replaced, and a "
        f"second is drawn. Find the probability that both are {target_color}."
    )
    return _mk(question, sp.Rational(favourable, total) ** 2,
               "independent_events", difficulty, "prob_independent")


@register("probability", "dependent_events")
def dependent_events(rng: random.Random, difficulty: str) -> Problem:
    """Two draws *without* replacement: the denominator shrinks by one.

    Needs at least two favourable items, or the second draw is impossible and
    the answer is a trivial zero.
    """
    lo, hi = COUNT[difficulty]
    target_color, other_color = rng.sample(COLORS, 2)
    item = pick(rng, ITEMS)
    favourable = rng.randint(max(lo, 2), hi)
    other = rng.randint(lo, hi)
    total = favourable + other

    question = (
        f"A bag holds ${favourable}$ {target_color} {item} and "
        f"${other}$ {other_color} {item}. Two are drawn at random without "
        f"replacement. Find the probability that both are {target_color}."
    )
    value = sp.Rational(favourable, total) * sp.Rational(favourable - 1, total - 1)
    return _mk(question, value, "dependent_events", difficulty, "prob_dependent")
