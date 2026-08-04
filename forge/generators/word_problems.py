"""Word problems.

The one place authored text is allowed -- and only as *frames*. Every name,
quantity and rate is sampled from the rng, and the answer is solved by sympy
from a model the verifier re-solves independently. A frame is scaffolding; it
is never a problem. Adding a frame widens variety, but the numbers must always
come from the rng.
"""

from __future__ import annotations

import random

import sympy as sp

from ..core.problem import Problem
from ..core.registry import register
from ..core.sampling import pick

X = sp.Symbol("x")

NAMES = (
    "Ava", "Noah", "Mia", "Liam", "Zoe", "Ethan", "Ruby", "Omar", "Ines", "Kai",
    "Priya", "Diego", "Nina", "Sam", "Leo", "Maya", "Jonas", "Tara", "Wes", "Iris",
)
ITEMS = (
    ("stickers", "sticker"), ("marbles", "marble"), ("books", "book"),
    ("tickets", "ticket"), ("cards", "card"), ("plants", "plant"),
    ("candles", "candle"), ("posters", "poster"), ("mugs", "mug"),
)
SCALE = {"easy": (2, 9), "medium": (3, 15), "hard": (4, 25)}


def _mk(text: str, lhs: str, rhs: str, value, subskill: str, difficulty: str,
        quantities, unit: str = "") -> Problem:
    value = sp.nsimplify(value)
    answer = f"{sp.latex(value)}" + (f"\\text{{ {unit}}}" if unit else "")
    return Problem(
        question_latex=text,
        answer_latex=f"${answer}$",
        answer_expr=value,
        topic="word_problems",
        subskill=subskill,
        difficulty=difficulty,
        verify={
            "kind": "word",
            "var": "x",
            "lhs": lhs,
            "rhs": rhs,
            "quantities": quantities,
            # Prose is templated scaffolding, not a literal rendering of the
            # model -- lhs/rhs are never expected to appear verbatim in the
            # sentence (verify.py's generic fragment check would otherwise
            # demand that). _v_word already cross-checks quantities instead.
            "prose": True,
        },
    )


@register("word_problems", "linear_model")
def linear_model(rng: random.Random, difficulty: str) -> Problem:
    """Backwards construction: choose the answer, then derive the total."""
    lo, hi = SCALE[difficulty]
    name = pick(rng, NAMES)
    plural, singular = pick(rng, ITEMS)
    per = rng.randint(2, hi)
    # Never 1: "already owns 1 plants" reads as a bug to a student.
    extra = rng.randint(2, hi * 2)
    x_sol = rng.randint(2, hi)
    total = per * x_sol + extra

    text = (
        f"{name} buys ${per}$ {plural} each week and already owns ${extra}$ {plural}. "
        f"After how many weeks will {name} have ${total}$ {plural}?"
    )
    return _mk(text, f"{per}x + {extra}", str(total), x_sol, "linear_model",
               difficulty, [per, extra, total], "weeks")


@register("word_problems", "rate_model")
def rate_model(rng: random.Random, difficulty: str) -> Problem:
    lo, hi = SCALE[difficulty]
    name = pick(rng, NAMES)
    rate = rng.randint(2, hi + 5)
    hours = rng.randint(2, hi)
    distance = rate * hours
    text = (
        f"{name} rides at a steady ${rate}$ miles per hour and travels "
        f"${distance}$ miles. How many hours does the ride take?"
    )
    return _mk(text, f"{rate}x", str(distance), hours, "rate_model",
               difficulty, [rate, distance], "hours")


@register("word_problems", "percent_model")
def percent_model(rng: random.Random, difficulty: str) -> Problem:
    pct = pick(rng, (10, 15, 20, 25, 30, 40, 50))
    name = pick(rng, NAMES)
    plural, singular = pick(rng, ITEMS)
    original = rng.randint(2, 20) * 10
    saved = sp.Rational(pct, 100) * original
    text = (
        f"A {singular} originally costs $\\${original}$. {name} uses a "
        f"${pct}\\%$ off coupon. How many dollars does {name} save?"
    )
    return _mk(text, "x", str(saved), saved, "percent_model",
               difficulty, [original, pct], "dollars")


@register("word_problems", "comparison_model")
def comparison_model(rng: random.Random, difficulty: str) -> Problem:
    """Two plans that cost the same at the answer -- built backwards from it."""
    lo, hi = SCALE[difficulty]
    a_name, b_name = "Plan A", "Plan B"
    x_sol = rng.randint(2, hi)
    m1 = rng.randint(2, hi + 3)
    m2 = m1 + rng.randint(1, 6)
    b1 = rng.randint(5, hi * 4)
    # b2 chosen so the two plans agree exactly at x_sol.
    b2 = (m1 - m2) * x_sol + b1
    if b2 < 0:
        b1 += -b2
        b2 = 0
    plural, _ = pick(rng, ITEMS)
    text = (
        f"{a_name} charges $\\${b1}$ plus $\\${m1}$ per month. "
        f"{b_name} charges $\\${b2}$ plus $\\${m2}$ per month. "
        f"After how many months do the two plans cost the same?"
    )
    return _mk(text, f"{m1}x + {b1}", f"{m2}x + {b2}", x_sol, "comparison_model",
               difficulty, [m1, m2, b1, b2], "months")
