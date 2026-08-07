"""Decimal arithmetic and conversion between decimals, fractions and percents.

Every value is an exact terminating decimal held as a ``Fraction``, never a
binary float, so answers are exact and the verifier compares them exactly.
That is only possible because ``verify.parsing._exactify`` reads a printed
``3.4`` as 17/5 rather than the nearest double.

Division is built backwards -- pick the divisor and the quotient, multiply to
get the dividend -- because dividing two freely sampled decimals is usually
non-terminating (0.7 / 0.3), which no answer key can state exactly.
"""

from __future__ import annotations

import random
from fractions import Fraction

import sympy as sp

from ..core.problem import Problem
from ..core.registry import register
from ..core.sampling import pick

# Digits after the point, and the size of the whole part.
PLACES = {"easy": (1, 1), "medium": (1, 2), "hard": (1, 3)}
WHOLE = {"easy": (0, 20), "medium": (0, 60), "hard": (1, 200)}
# Denominators that terminate: only 2s and 5s divide a power of ten.
TERMINATING = {"easy": (2, 4, 5, 8, 10, 20), "medium": (2, 4, 5, 8, 10, 16, 20, 25),
               "hard": (2, 4, 5, 8, 16, 20, 25, 40, 50, 80, 125)}
# Numerator ceiling for the conversion subskills. Wide enough that no single
# value (2.5 was appearing in 9 of 50 runs) dominates the draw.
CONV_NUMER = {"easy": 12, "medium": 20, "hard": 30}
# Explicit per-tier bands: an ad-hoc "1 if easy else 2" makes medium and hard
# identical, which the tier-collapse guard rejects.
MUL_PLACES = {"easy": 1, "medium": 2, "hard": 3}
MUL_TOP = {"easy": 49, "medium": 99, "hard": 199}
DIV_DIVISOR = {"easy": 9, "medium": 25, "hard": 60}


def _decimal(rng: random.Random, difficulty: str) -> Fraction:
    """An exact terminating decimal with a tier-appropriate number of places."""
    places = rng.randint(*PLACES[difficulty])
    lo, hi = WHOLE[difficulty]
    whole = rng.randint(lo, hi)
    scale = 10**places
    frac = rng.randint(1, scale - 1)
    return Fraction(whole * scale + frac, scale)


def _fmt(value: Fraction) -> str:
    """Print an exact decimal without a trailing zero or an exponent."""
    s = f"{float(value):.10f}".rstrip("0").rstrip(".")
    return s if s else "0"


def _mk(question: str, value, subskill: str, difficulty: str,
        answer_text: str = "", kind: str = "evaluate") -> Problem:
    exact = sp.Rational(value.numerator, value.denominator) if isinstance(
        value, Fraction) else value
    return Problem(
        question_latex=f"${question}$",
        answer_latex=f"${answer_text or _fmt(value)}$",
        answer_expr=exact,
        topic="decimals",
        subskill=subskill,
        difficulty=difficulty,
        verify={"kind": kind},
    )


@register("decimals", "add_sub_decimals")
def add_sub_decimals(rng: random.Random, difficulty: str) -> Problem:
    a, b = _decimal(rng, difficulty), _decimal(rng, difficulty)
    if rng.random() < 0.5:
        return _mk(f"{_fmt(a)} + {_fmt(b)}", a + b, "add_sub_decimals", difficulty)
    # Keep subtraction positive at easy: negative decimals are a separate skill.
    if difficulty == "easy" and b > a:
        a, b = b, a
    return _mk(f"{_fmt(a)} - {_fmt(b)}", a - b, "add_sub_decimals", difficulty)


@register("decimals", "multiply_decimals")
def multiply_decimals(rng: random.Random, difficulty: str) -> Problem:
    """Place-value counting is the skill, so both factors carry decimals."""
    places = MUL_PLACES[difficulty]
    a = Fraction(rng.randint(11, 10 ** (places + 1) - 1), 10**places)
    b = Fraction(rng.randint(11, MUL_TOP[difficulty]), 10)
    return _mk(rf"{_fmt(a)} \times {_fmt(b)}", a * b, "multiply_decimals", difficulty)


@register("decimals", "divide_decimals")
def divide_decimals(rng: random.Random, difficulty: str) -> Problem:
    """Backwards from the quotient, so the division terminates exactly."""
    quotient = _decimal(rng, difficulty)
    divisor = Fraction(rng.randint(2, DIV_DIVISOR[difficulty]), 10)
    dividend = quotient * divisor
    return _mk(rf"{_fmt(dividend)} \div {_fmt(divisor)}", quotient,
               "divide_decimals", difficulty)


@register("decimals", "decimal_to_fraction")
def decimal_to_fraction(rng: random.Random, difficulty: str) -> Problem:
    """Write a terminating decimal as a fraction in lowest terms."""
    denom = pick(rng, TERMINATING[difficulty])
    top = denom * CONV_NUMER[difficulty]
    numer = rng.randint(1, top)
    while Fraction(numer, denom).denominator == 1:  # would print as a whole number
        numer = rng.randint(1, top)
    value = Fraction(numer, denom)
    exact = sp.Rational(value.numerator, value.denominator)
    return _mk(_fmt(value), value, "decimal_to_fraction", difficulty,
               answer_text=sp.latex(exact))


@register("decimals", "fraction_to_decimal")
def fraction_to_decimal(rng: random.Random, difficulty: str) -> Problem:
    """Only terminating fractions: 1/3 has no exact decimal to key."""
    denom = pick(rng, TERMINATING[difficulty])
    numer = rng.randint(1, denom * CONV_NUMER[difficulty])
    value = Fraction(numer, denom)
    exact = sp.Rational(value.numerator, value.denominator)
    # \dfrac in a question body: \frac renders shrunken, and a repo-wide
    # sweep enforces it.
    body = sp.latex(exact).replace(r"\frac", r"\dfrac")
    return Problem(
        question_latex=f"${body}$",
        answer_latex=f"${_fmt(value)}$",
        answer_expr=exact,
        topic="decimals",
        subskill="fraction_to_decimal",
        difficulty=difficulty,
        verify={"kind": "evaluate"},
    )


@register("decimals", "decimal_to_percent")
def decimal_to_percent(rng: random.Random, difficulty: str) -> Problem:
    """The question is a bare decimal; the directions say what to do with it.

    Splitting the two directions into two subskills keeps the item bare --
    "0.35 as a percent" printed on every line would be directions repeated
    per item, which the LaTeX conventions forbid.
    """
    places = rng.randint(*PLACES[difficulty])
    value = Fraction(rng.randint(1, 10 ** (places + 2)), 10 ** (places + 2))
    percent = value * 100
    return _mk(_fmt(value), percent, "decimal_to_percent", difficulty,
               answer_text=rf"{_fmt(percent)}\%", kind="decimal_to_percent")


@register("decimals", "percent_to_decimal")
def percent_to_decimal(rng: random.Random, difficulty: str) -> Problem:
    places = rng.randint(*PLACES[difficulty])
    value = Fraction(rng.randint(1, 10 ** (places + 2)), 10 ** (places + 2))
    percent = value * 100
    return _mk(rf"{_fmt(percent)}\%", value, "percent_to_decimal", difficulty,
               kind="percent_to_decimal")
