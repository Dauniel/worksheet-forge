"""Guards against problems that are arithmetically correct and untrue.

A generator can satisfy every existing test -- verified key, no hardcoded
list, plenty of variance -- and still print a $23 eraser, a 75% sales
commission, or a 24-hour bike ride. Those cost the worksheet its credibility:
a student who notices the numbers are fake stops sanity-checking their own
answer against the situation, which is half of what a word problem teaches.

The other class here is the *fake* difficulty knob: a subskill that accepts a
difficulty argument and ignores it, so a tutor asking for "hard" gets easy
problems with no indication anything went wrong.
"""

from __future__ import annotations

import random
import re

import pytest
import sympy as sp

from forge.core.registry import all_generators, get
from forge.core.verify import verify_problem

DIFFICULTIES = ("easy", "medium", "hard")
SEEDS = range(300)


def _sample(topic, subskill, difficulty, seeds=SEEDS):
    fn = get(topic, subskill)
    return [fn(random.Random(s), difficulty) for s in seeds]


# --------------------------------------------------------------------------
# Difficulty has to mean something
# --------------------------------------------------------------------------

# unit_circle is genuinely a fixed, finite set of angles -- there is no honest
# harder tier without inventing distinctions the catalog does not claim. It is
# listed here rather than silently skipped so the exemption stays visible.
FLAT_BY_DESIGN = {
    ("unit_circle", "degree_radian_conversion"),
    ("unit_circle", "exact_trig_value"),
}


@pytest.mark.parametrize("key", sorted(all_generators()))
def test_every_difficulty_tier_produces_different_problems(key):
    """A generator that takes ``difficulty`` and ignores it is worse than one
    that has a single tier: the caller is told they got what they asked for."""
    if key in FLAT_BY_DESIGN:
        pytest.skip("fixed finite problem space; see FLAT_BY_DESIGN")
    topic, subskill = key
    seen = {
        d: tuple(p.question_latex for p in _sample(topic, subskill, d))
        for d in DIFFICULTIES
    }
    assert seen["easy"] != seen["medium"], f"{topic}/{subskill}: easy == medium"
    assert seen["medium"] != seen["hard"], f"{topic}/{subskill}: medium == hard"


def test_flat_by_design_list_has_no_stale_entries():
    registered = set(all_generators())
    stale = FLAT_BY_DESIGN - registered
    assert not stale, f"not registered generators: {sorted(stale)}"


# --------------------------------------------------------------------------
# Quadratics: a non-monic problem has to be genuinely non-monic
# --------------------------------------------------------------------------

@pytest.mark.parametrize("difficulty", DIFFICULTIES)
def test_factoring_leading_coefficient_is_not_a_common_factor(difficulty):
    """``3x^2 - 15x - 72`` is ``3(x^2 - 5x - 24)``: the student divides the 3
    away and never uses the AC method the tier is meant to drill. Scaling a
    monic trinomial by ``a`` always does this, which is why the generator
    builds from two rational roots instead."""
    for p in _sample("quadratics", "solve_by_factoring", difficulty):
        a, b, c = sp.Poly(
            sp.expand(_lhs(p.question_latex)), sp.Symbol("x")
        ).all_coeffs()
        assert sp.gcd(sp.gcd(a, b), c) == 1, (
            f"{p.question_latex} has a common factor; it collapses to a monic "
            f"trinomial and never exercises factoring with a != 1"
        )


def _lhs(question_latex: str):
    from forge.core.verify import latex_to_sympy

    return latex_to_sympy(question_latex.strip().strip("$").split("=")[0])


def test_factoring_tiers_have_the_intended_leading_coefficients():
    def leads(d):
        return {
            sp.Poly(sp.expand(_lhs(p.question_latex)), sp.Symbol("x")).all_coeffs()[0]
            for p in _sample("quadratics", "solve_by_factoring", d)
        }

    assert leads("easy") == {1}, "easy should stay monic"
    assert leads("medium") == {2, 3}
    assert max(leads("hard")) <= 6, (
        "past a = 6 the AC method's factor-pair scan stops testing "
        "understanding and starts testing patience"
    )
    assert min(leads("hard")) > 1, "hard should never fall back to monic"


# --------------------------------------------------------------------------
# Money has to look like money
# --------------------------------------------------------------------------

MONEY_SUBSKILLS = [
    ("word_problems", "percent_model"),
    ("percent_apps", "commission"),
    ("percent_apps", "markup_discount"),
    ("percent_apps", "tax_tip"),
    ("unit_rates", "unit_rate"),
]


@pytest.mark.parametrize("topic,subskill", MONEY_SUBSKILLS)
@pytest.mark.parametrize("difficulty", DIFFICULTIES)
def test_money_answers_are_never_improper_fractions(topic, subskill, difficulty):
    """"$\\frac{15}{2}$ dollars" is a correct answer to a question nobody
    asked. Dollars are decimal or whole, never fifteen-halves."""
    for p in _sample(topic, subskill, difficulty, seeds=range(200)):
        assert r"\frac" not in p.answer_latex and r"\dfrac" not in p.answer_latex, (
            f"{topic}/{subskill}: money answer {p.answer_latex} is a fraction "
            f"for {p.question_latex}"
        )


@pytest.mark.parametrize("difficulty", DIFFICULTIES)
def test_unit_prices_are_plausible_for_the_item(difficulty):
    """A $23 eraser is the detail that tells a student the numbers are fake."""
    from forge.generators.unit_rates import ITEMS

    bounds = {singular: (lo, hi) for _, singular, lo, hi in ITEMS}
    for p in _sample("unit_rates", "unit_rate", difficulty):
        price = int(re.search(r"\\\$(\d+)\$ per", p.answer_latex).group(1))
        singular = p.answer_latex.split(" per ", 1)[1]
        lo, hi = bounds[singular]
        assert lo <= price <= hi, (
            f"${price} per {singular} is outside the plausible band {lo}-{hi}"
        )


@pytest.mark.parametrize("difficulty", DIFFICULTIES)
def test_commission_and_tax_rates_stay_in_the_real_world(difficulty):
    for p in _sample("percent_apps", "commission", difficulty):
        pct = int(re.search(r"\$(\d+)\\%\$", p.question_latex).group(1))
        assert pct <= 20, f"a {pct}% sales commission is not a thing"
    for p in _sample("percent_apps", "tax_tip", difficulty):
        pct = int(re.search(r"\$(\d+)\\%\$", p.question_latex).group(1))
        kind = "tip" if "tip" in p.question_latex else "tax"
        limit = 25 if kind == "tip" else 12
        assert pct <= limit, f"a {pct}% {kind} is not a thing"


# --------------------------------------------------------------------------
# Situations have to be physically sensible
# --------------------------------------------------------------------------

@pytest.mark.parametrize("difficulty", DIFFICULTIES)
def test_bike_rides_are_a_believable_length(difficulty):
    for p in _sample("word_problems", "rate_model", difficulty):
        hours = sp.Integer(int(re.search(r"\$(\d+)\\text", p.answer_latex).group(1)))
        assert hours <= 9, f"nobody rides {hours} hours: {p.question_latex}"


@pytest.mark.parametrize("difficulty", DIFFICULTIES)
def test_plans_always_quote_a_real_base_fee(difficulty):
    """"Plan B charges $0 plus $9 per month" is not how a plan is quoted."""
    for p in _sample("word_problems", "comparison_model", difficulty):
        fees = [int(v) for v in re.findall(r"\\\$(\d+)\$ plus", p.question_latex)]
        assert all(f > 0 for f in fees), p.question_latex


@pytest.mark.parametrize("difficulty", DIFFICULTIES)
def test_unit_price_comparison_needs_two_different_package_sizes(difficulty):
    """Equal quantities reduce the question to "which number is smaller",
    which can be answered without ever forming a unit rate."""
    for p in _sample("unit_rates", "unit_price_comparison", difficulty):
        qtys = [int(v) for v in re.findall(r"for \$(\d+)\$", p.question_latex)]
        assert len(qtys) == 2 and qtys[0] != qtys[1], p.question_latex


# --------------------------------------------------------------------------
# Printed maths has to be printed as maths
# --------------------------------------------------------------------------

@pytest.mark.parametrize("key", sorted(all_generators()))
def test_no_raw_slash_fractions_in_printed_problems(key):
    """``\\dfrac{24/5}{32}`` is a fraction stacked inside a proportion, printed
    by str()-ing a sympy Rational instead of latex()-ing it."""
    topic, subskill = key
    for p in _sample(topic, subskill, "hard", seeds=range(120)):
        for field in (p.question_latex, p.answer_latex):
            assert not re.search(r"\d/\d", field), (
                f"{topic}/{subskill}: raw slash fraction in {field!r} "
                f"-- use sp.latex(), not str()"
            )


@pytest.mark.parametrize("key", sorted(all_generators()))
def test_units_are_set_inside_the_math(key):
    r"""``$37$\text{ dollars}`` compiles, but sets the unit in a different font
    from every other key on the sheet."""
    topic, subskill = key
    for p in _sample(topic, subskill, "medium", seeds=range(60)):
        # Only a \text{...} that *closes* the answer is outside math mode --
        # "$\text{No solution}$" is text set inside math, which is correct.
        assert not re.search(r"\$\\text\{[^}]*\}\s*$", p.answer_latex), (
            f"{topic}/{subskill}: unit set outside math mode in {p.answer_latex!r}"
        )


# --------------------------------------------------------------------------
# Everything above still has to be a verified problem
# --------------------------------------------------------------------------

@pytest.mark.parametrize("key", sorted(all_generators()))
def test_realism_constraints_did_not_break_verification(key):
    topic, subskill = key
    for difficulty in DIFFICULTIES:
        for p in _sample(topic, subskill, difficulty, seeds=range(40)):
            verify_problem(p)
