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
# (plural, singular, cheapest, dearest) -- the price bounds are what keep the
# sentence honest. Sampling a unit rate independently of the item is how you
# end up asking for the price of a $23 eraser: arithmetically fine, and the
# kind of detail that tells a student the numbers are fake and not worth
# sanity-checking. The item is chosen to fit the rate, not the other way
# round, so the difficulty ramp still gets the range it asks for.
ITEMS = (
    ("pencils", "pencil", 1, 3),
    ("erasers", "eraser", 1, 3),
    ("juice boxes", "juice box", 1, 4),
    ("bagels", "bagel", 2, 5),
    ("granola bars", "granola bar", 1, 4),
    ("notebooks", "notebook", 2, 8),
    ("water bottles", "water bottle", 6, 18),
    ("phone cases", "phone case", 8, 25),
    ("T-shirts", "T-shirt", 9, 30),
    ("backpacks", "backpack", 15, 45),
)
RATE_RANGE = {"easy": (2, 12), "medium": (2, 20), "hard": (3, 30)}
QTY_RANGE = {"easy": (2, 8), "medium": (3, 12), "hard": (4, 16)}


def _pick_item(rng: random.Random, difficulty: str, distinct_rates: int = 1):
    """An item, plus ``distinct_rates`` unit prices it could plausibly carry.

    Both prices come from the *same* item's band, since both options in a
    comparison are that same item.
    """
    lo, hi = RATE_RANGE[difficulty]
    candidates = [it for it in ITEMS if it[3] >= lo and it[2] <= hi]
    plural, singular, ilo, ihi = pick(rng, candidates)
    plo, phi = max(lo, ilo), min(hi, ihi)
    if phi - plo + 1 < distinct_rates:
        plo, phi = ilo, ihi  # a narrow band still has to yield distinct prices
    rates: list = []
    while len(rates) < distinct_rates:
        r = rng.randint(plo, phi)
        if r not in rates:
            rates.append(r)
    return plural, singular, rates


@register("unit_rates", "unit_rate")
def unit_rate(rng: random.Random, difficulty: str) -> Problem:
    qlo, qhi = QTY_RANGE[difficulty]
    qty = rng.randint(qlo, qhi)
    name = pick(rng, NAMES)
    plural, singular, (rate,) = _pick_item(rng, difficulty)
    total = rate * qty
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
    The two package sizes must differ as well: equal quantities turn the
    question into "which number is smaller", answerable without ever forming
    a unit rate, which is the one thing this subskill exists to practice.
    """
    qlo, qhi = QTY_RANGE[difficulty]
    plural, singular, (rate_a, rate_b) = _pick_item(rng, difficulty, distinct_rates=2)
    qty_a = rng.randint(qlo, qhi)
    while True:
        qty_b = rng.randint(qlo, qhi)
        if qty_b != qty_a:
            break
    price_a, price_b = rate_a * qty_a, rate_b * qty_b
    text = (
        f"Option A: $\\${price_a}$ for ${qty_a}$ {plural}. "
        f"Option B: $\\${price_b}$ for ${qty_b}$ {plural}. "
        f"Which option is the better price per {singular}?"
    )
    winner = "Option A" if sp.Rational(price_a, qty_a) < sp.Rational(price_b, qty_b) else "Option B"
    return Problem(
        question_latex=text,
        answer_latex=winner,
        answer_expr=winner,
        topic="unit_rates",
        subskill="unit_price_comparison",
        difficulty=difficulty,
        verify={"kind": "unit_price_comparison"},
    )
