"""Scientific notation: converting both ways, and multiplying/dividing.

Everything is exact -- the coefficient is a terminating decimal with one digit
before the point, so a value is never approximated and the verifier can
compare exactly rather than within a tolerance.

Backwards construction: the coefficient and exponent are picked first and the
plain-form number derived from them, so no problem can land on a value that
does not convert cleanly.
"""

from __future__ import annotations

import random
from decimal import Decimal

import sympy as sp

from ..core.problem import Problem
from ..core.registry import register

# Exponent magnitude. Negative exponents (small numbers) are the harder half,
# so easy stays positive-only.
EXP = {"easy": (1, 4), "medium": (2, 6), "hard": (3, 9)}
ALLOW_NEGATIVE_EXP = {"easy": False, "medium": True, "hard": True}
# Digits after the point in the coefficient: 3.5 x 10^4 is easier to place
# than 3.507 x 10^4.
DECIMALS = {"easy": (0, 1), "medium": (1, 2), "hard": (1, 3)}


def _coefficient(rng: random.Random, difficulty: str, max_places: int = 99) -> Decimal:
    """A value in [1, 10) with a tier-appropriate number of decimal places.

    ``max_places`` caps the draw for cases that multiply two coefficients
    together: 3 places times 3 places yields 6, and ``3.588732`` is not a
    number anyone puts on a worksheet.
    """
    lead = rng.randint(1, 9)
    lo, hi = DECIMALS[difficulty]
    places = rng.randint(lo, min(hi, max_places))
    if places == 0:
        return Decimal(lead)
    tail = "".join(str(rng.randint(0, 9)) for _ in range(places))
    # A trailing zero would print as 3.50, which is not how a coefficient is
    # written and would make the "same number of significant digits" reading
    # ambiguous.
    tail = tail[:-1] + str(rng.randint(1, 9))
    return Decimal(f"{lead}.{tail}")


def _exponent(rng: random.Random, difficulty: str) -> int:
    lo, hi = EXP[difficulty]
    n = rng.randint(lo, hi)
    if ALLOW_NEGATIVE_EXP[difficulty] and rng.random() < 0.4:
        return -n
    return n


def _plain(coeff: Decimal, exp: int) -> Decimal:
    """The same value written out, exactly -- Decimal keeps it terminating."""
    return coeff.scaleb(exp)


def _fmt_plain(value: Decimal) -> str:
    """Print a plain decimal without exponent notation or trailing zeros."""
    s = format(value, "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s


def _sci_latex(coeff: Decimal, exp: int) -> str:
    return f"{coeff} \\times 10^{{{exp}}}"


def _mk(question: str, value, subskill: str, difficulty: str, kind: str) -> Problem:
    return Problem(
        question_latex=question,
        answer_latex=f"${value}$",
        answer_expr=sp.Rational(str(value)),
        topic="scientific_notation",
        subskill=subskill,
        difficulty=difficulty,
        verify={"kind": kind},
    )


@register("scientific_notation", "to_scientific")
def to_scientific(rng: random.Random, difficulty: str) -> Problem:
    """Given the plain number, write it in scientific notation."""
    coeff = _coefficient(rng, difficulty)
    exp = _exponent(rng, difficulty)
    plain = _plain(coeff, exp)
    question = f"${_fmt_plain(plain)}$"
    answer = _sci_latex(coeff, exp)
    return Problem(
        question_latex=question,
        answer_latex=f"${answer}$",
        answer_expr=sp.Rational(str(plain)),
        topic="scientific_notation",
        subskill="to_scientific",
        difficulty=difficulty,
        verify={"kind": "sci_to_scientific"},
    )


@register("scientific_notation", "from_scientific")
def from_scientific(rng: random.Random, difficulty: str) -> Problem:
    """Given scientific notation, write the plain number."""
    coeff = _coefficient(rng, difficulty)
    exp = _exponent(rng, difficulty)
    plain = _plain(coeff, exp)
    return _mk(f"${_sci_latex(coeff, exp)}$", _fmt_plain(plain),
               "from_scientific", difficulty, "sci_from_scientific")


def _normalize(value: Decimal):
    """Rewrite a value as ``(coefficient in [1, 10), exponent)``, exactly."""
    exp = 0
    sign = -1 if value < 0 else 1
    value = abs(value)
    while value >= 10:
        value /= 10
        exp += 1
    while value < 1:
        value *= 10
        exp -= 1
    return sign * value.normalize(), exp


@register("scientific_notation", "multiply_divide")
def multiply_divide(rng: random.Random, difficulty: str) -> Problem:
    """Multiply or divide two numbers in scientific notation.

    Renormalizing is the point of the subskill: two coefficients multiply to
    as much as 81, so the result has to be pushed back into [1, 10) and the
    exponent adjusted.

    Division is built backwards -- pick the divisor and the quotient, then
    derive the dividend. Dividing two freely sampled coefficients would give
    repeating decimals (3.5 / 1.7), which cannot be written exactly and would
    force the answer key into an approximation.
    """
    e1, e2 = _exponent(rng, difficulty), _exponent(rng, difficulty)
    times = rng.random() < 0.5

    if times:
        # Capped so the product does not run to six decimal places.
        c1 = _coefficient(rng, difficulty, max_places=2)
        c2 = _coefficient(rng, difficulty, max_places=2)
        op = "\\times"
        result = _plain(c1, e1) * _plain(c2, e2)
    else:
        # Both capped at one decimal place so their product -- the dividend
        # the student actually reads -- has at most two.
        c2 = _coefficient(rng, difficulty, max_places=1)
        quotient = _coefficient(rng, difficulty, max_places=1)
        c1 = c2 * quotient  # exact by construction; may exceed 10, so renormalize
        c1, shift = _normalize(c1)
        e1 += shift
        op = "\\div"
        result = _plain(c1, e1) / _plain(c2, e2)

    coeff, exp = _normalize(result)
    question = f"$({_sci_latex(c1, e1)}) {op} ({_sci_latex(c2, e2)})$"
    return Problem(
        question_latex=question,
        answer_latex=f"${_sci_latex(coeff, exp)}$",
        answer_expr=sp.Rational(str(coeff)) * sp.Integer(10) ** exp,
        topic="scientific_notation",
        subskill="multiply_divide",
        difficulty=difficulty,
        verify={"kind": "sci_multiply_divide"},
    )
