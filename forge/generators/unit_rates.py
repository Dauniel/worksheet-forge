"""Unit rates, including unit-price comparison ("which is the better buy?")."""

from __future__ import annotations

import random

import sympy as sp

from ..core.problem import Problem
from ..core.registry import register
from ..core.sampling import pick

NAMES = (
    "Ava", "Noah", "Mia", "Liam", "Zoe", "Ethan", "Ruby", "Omar", "Ines", "Kai",
)
ITEMS = (
    ("granola bars", "granola bar"), ("notebooks", "notebook"), ("erasers", "eraser"),
    ("juice boxes", "juice box"), ("bagels", "bagel"), ("pencils", "pencil"),
)
RATE_RANGE = {"easy": (2, 12), "medium": (2, 20), "hard": (3, 30)}
QTY_RANGE = {"easy": (2, 8), "medium": (3, 12), "hard": (4, 16)}


@register("unit_rates", "unit_rate")
def unit_rate(rng: random.Random, difficulty: str) -> Problem:
    lo, hi = RATE_RANGE[difficulty]
    rate = rng.randint(lo, hi)
    qlo, qhi = QTY_RANGE[difficulty]
    qty = rng.randint(qlo, qhi)
    total = rate * qty
    name = pick(rng, NAMES)
    plural, singular = pick(rng, ITEMS)
    text = (
        f"{name} pays $\\${total}$ for ${qty}$ {plural}. "
        f"Find the price per {singular}."
    )
    return Problem(
        question_latex=text,
        answer_latex=rf"$\${rate}$ per {singular}",
        answer_expr=sp.Integer(rate),
        topic="unit_rates",
        subskill="unit_rate",
        difficulty=difficulty,
        verify={"kind": "unit_rate"},
    )


@register("unit_rates", "unit_price_comparison")
def unit_price_comparison(rng: random.Random, difficulty: str) -> Problem:
    """Two package sizes at two prices; pick the better per-unit deal.

    Built backwards from two *different* unit rates so there is never a tie.
    """
    lo, hi = RATE_RANGE[difficulty]
    qlo, qhi = QTY_RANGE[difficulty]
    while True:
        rate_a = rng.randint(lo, hi)
        rate_b = rng.randint(lo, hi)
        if rate_a != rate_b:
            break
    qty_a, qty_b = rng.randint(qlo, qhi), rng.randint(qlo, qhi)
    price_a, price_b = rate_a * qty_a, rate_b * qty_b
    plural, _ = pick(rng, ITEMS)
    text = (
        f"Option A: $\\${price_a}$ for ${qty_a}$ {plural}. "
        f"Option B: $\\${price_b}$ for ${qty_b}$ {plural}. "
        f"Which option is the better price per {plural[:-1]}?"
    )
    winner = "Option A" if sp.Rational(price_a, qty_a) < sp.Rational(price_b, qty_b) else "Option B"
    return Problem(
        question_latex=text,
        answer_latex=winner,
        answer_expr=winner,
        topic="unit_rates",
        subskill="unit_price_comparison",
        difficulty=difficulty,
        verify={"kind": "unit_price_comparison", "answer_check": None},
    )
