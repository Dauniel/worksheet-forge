"""Percent applications as distinct real-world subtypes.

Percent proportion, estimating with friendly percents, markup/discount,
percent error, commission, and tax/tip. Every quantity is sampled from
``rng``; sentences are templated scaffolding only. Verification re-reads the
printed numbers straight out of the sentence (see ``forge/core/verify.py``)
and re-applies each formula independently.
"""

from __future__ import annotations

import random

import sympy as sp

from ..core.problem import Problem
from ..core.registry import register
from ..core.sampling import nonzero_int, pick

NAMES = (
    "Ava", "Noah", "Mia", "Liam", "Zoe", "Ethan", "Ruby", "Omar", "Ines", "Kai",
    "Priya", "Diego", "Nina", "Sam", "Leo", "Maya", "Jonas", "Tara", "Wes", "Iris",
)
ITEMS = (
    ("jacket", "jackets"), ("bicycle", "bicycles"), ("backpack", "backpacks"),
    ("skateboard", "skateboards"), ("tablet", "tablets"), ("lamp", "lamps"),
    ("guitar", "guitars"), ("watch", "watches"),
)
PERCENTS = {
    "easy": (5, 10, 15, 20, 25, 50),
    "medium": (5, 8, 12, 15, 18, 20, 25, 30, 40, 60),
    "hard": (6, 9, 13, 17, 22, 28, 35, 45, 55, 65, 75),
}
FRIENDLY = (10, 20, 25, 50, 75)
# Percent bands that belong to the specific situation. Reusing the generic
# PERCENTS ladder here produced a 75% sales commission and a 65% sales tax --
# arithmetically sound, and nonsense as a sentence about the world.
COMMISSION_PCTS = {"easy": (5, 10, 20), "medium": (4, 8, 12, 15), "hard": (3, 6, 9, 18)}
TAX_PCTS = {"easy": (5, 10), "medium": (6, 8, 9), "hard": (4, 7, 12)}
TIP_PCTS = {"easy": (10, 20), "medium": (15, 18, 25), "hard": (12, 16, 22)}
# estimate_percent ramps by how far the real numbers sit from the friendly
# benchmark, and by how large the base is -- it took no difficulty argument
# at all before, so all three tiers were identical.
ESTIMATE = {
    "easy": {"friendly": (10, 25, 50), "base": (2, 12), "pct_off": 2, "base_off": 2},
    "medium": {"friendly": (10, 20, 25, 50), "base": (5, 30), "pct_off": 4, "base_off": 5},
    "hard": {"friendly": (20, 25, 50, 75), "base": (10, 60), "pct_off": 6, "base_off": 8},
}


def _mk(text: str, value, subskill: str, difficulty: str, kind: str, unit: str = "dollars") -> Problem:
    value = sp.nsimplify(value)
    return Problem(
        question_latex=text,
        # Unit inside the math, as word_problems does it -- \text outside $..$
        # compiled, but set the unit in a different font from every other key.
        answer_latex=f"${sp.latex(value)}" + (rf"\text{{ {unit}}}$" if unit else "$"),
        answer_expr=value,
        topic="percent_apps",
        subskill=subskill,
        difficulty=difficulty,
        verify={"kind": kind},
    )


@register("percent_apps", "percent_proportion")
def percent_proportion(rng: random.Random, difficulty: str) -> Problem:
    """Solve the percent proportion part/whole = percent/100 for the hidden piece."""
    pct = pick(rng, PERCENTS[difficulty])
    # The part has to come out whole. Left free, a 15%-of-350 draw printed
    # \dfrac{\frac{105}{2}}{x} -- a fraction stacked inside a proportion,
    # which is neither what a percent proportion looks like nor something a
    # student can read at a glance.
    while True:
        whole = rng.randint(2, 40) * pick(rng, (2, 4, 5, 10))
        if (pct * whole) % 100 == 0:
            break
    part = sp.Rational(pct, 100) * whole
    slot = pick(rng, ("part", "whole", "percent"))
    if slot == "part":
        lhs, rhs, answer = r"\dfrac{x}{" + str(whole) + "}", rf"\dfrac{{{pct}}}{{100}}", part
    elif slot == "whole":
        lhs, rhs, answer = rf"\dfrac{{{sp.latex(sp.nsimplify(part))}}}{{x}}", rf"\dfrac{{{pct}}}{{100}}", sp.Integer(whole)
    else:
        lhs, rhs, answer = rf"\dfrac{{{sp.latex(sp.nsimplify(part))}}}{{{whole}}}", r"\dfrac{x}{100}", sp.Integer(pct)
    return Problem(
        question_latex=f"${lhs} = {rhs}$",
        answer_latex=f"$x = {sp.latex(answer)}$",
        answer_expr=answer,
        topic="percent_apps",
        subskill="percent_proportion",
        difficulty=difficulty,
        verify={"kind": "solve", "var": "x", "lhs": lhs, "rhs": rhs},
    )


@register("percent_apps", "estimate_percent")
def estimate_percent(rng: random.Random, difficulty: str) -> Problem:
    """Round both the percent and the base to friendly benchmarks, given in the
    prompt itself so the estimate has one exact, verifiable value."""
    tier = ESTIMATE[difficulty]
    fpct = pick(rng, tier["friendly"])
    # The whole point is a benchmark you can do in your head, so the
    # benchmark answer must itself be whole -- 75% of 290 is not an estimate
    # a student would ever report as 435/2.
    while True:
        fwhole = rng.randint(*tier["base"]) * 10
        if (fpct * fwhole) % 100 == 0:
            break
    pct_offset = nonzero_int(rng, -tier["pct_off"], tier["pct_off"])
    whole_offset = nonzero_int(rng, -tier["base_off"], tier["base_off"])
    actual_pct = max(1, fpct + pct_offset)
    actual_whole = max(1, fwhole + whole_offset)
    text = (
        f"Estimate ${actual_pct}\\%$ of ${actual_whole}$ by rounding to "
        f"${fpct}\\%$ of ${fwhole}$."
    )
    value = sp.Rational(fpct, 100) * fwhole
    return _mk(text, value, "estimate_percent", difficulty, "estimate_percent", unit="")


@register("percent_apps", "markup_discount")
def markup_discount(rng: random.Random, difficulty: str) -> Problem:
    is_discount = pick(rng, (True, False))
    pct = pick(rng, PERCENTS[difficulty])
    original = rng.randint(4, 60) * pick(rng, (1, 5))
    # Keep the result a clean number.
    while (pct * original) % 100 != 0:
        original += 1
    name = pick(rng, NAMES)
    singular, _ = pick(rng, ITEMS)
    if is_discount:
        text = (
            f"A {singular} that normally costs $\\${original}$ is on sale for "
            f"${pct}\\%$ off. Find the sale price."
        )
        value = original - sp.Rational(pct, 100) * original
    else:
        text = (
            f"A store marks up a {singular} that costs $\\${original}$ by "
            f"${pct}\\%$. Find the new price."
        )
        value = original + sp.Rational(pct, 100) * original
    return _mk(text, value, "markup_discount", difficulty, "markup_discount")


@register("percent_apps", "percent_error")
def percent_error(rng: random.Random, difficulty: str) -> Problem:
    pe = pick(rng, PERCENTS[difficulty])
    step = 100 // sp.igcd(pe, 100)
    actual = step * rng.randint(1, max(3, 60 // step))
    sign = pick(rng, (1, -1))
    measured = actual + sign * sp.Rational(pe, 100) * actual
    text = (
        f"A recipe calls for ${actual}$ grams of flour. A student measures "
        f"${int(measured)}$ grams. Find the percent error."
    )
    return _mk(text, sp.Integer(pe), "percent_error", difficulty, "percent_error", unit="")


@register("percent_apps", "commission")
def commission(rng: random.Random, difficulty: str) -> Problem:
    pct = pick(rng, COMMISSION_PCTS[difficulty])
    sales = rng.randint(2, 80) * pick(rng, (5, 10, 20))
    while (pct * sales) % 100 != 0:
        sales += 1
    name = pick(rng, NAMES)
    text = (
        f"{name} earns a ${pct}\\%$ commission on sales of $\\${sales}$. "
        f"Find {name}'s commission."
    )
    value = sp.Rational(pct, 100) * sales
    return _mk(text, value, "commission", difficulty, "commission")


@register("percent_apps", "tax_tip")
def tax_tip(rng: random.Random, difficulty: str) -> Problem:
    kind = pick(rng, ("tip", "sales tax"))
    pct = pick(rng, (TIP_PCTS if kind == "tip" else TAX_PCTS)[difficulty])
    amount = rng.randint(4, 90) * pick(rng, (1, 5))
    while (pct * amount) % 100 != 0:
        amount += 1
    name = pick(rng, NAMES)
    text = (
        f"{name}'s bill comes to $\\${amount}$. Including a ${pct}\\%$ {kind}, "
        f"find the total amount {name} pays."
    )
    value = amount + sp.Rational(pct, 100) * amount
    return _mk(text, value, "tax_tip", difficulty, "tax_tip")
