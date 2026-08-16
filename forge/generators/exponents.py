"""Exponent rules."""

from __future__ import annotations

import random

import sympy as sp

from ..core.latexfmt import var_pow


def _mono(*parts: str) -> str:
    """Join ``var_pow`` factors of a multiplied monomial with a separating
    space so two adjacent bare variables (e.g. exponent 1 next to exponent
    1) never merge into one token -- ``latex_to_sympy``'s tokenizer reads
    ``xy`` as a single two-letter symbol, not ``x * y``, when nothing
    (a digit, a brace, an operator) separates them. Empty factors (exponent
    0) are dropped entirely.
    """
    return " ".join(p for p in parts if p)
from ..core.problem import Problem
from ..core.registry import register
from ..core.sampling import nonzero_int, pick

X = sp.Symbol("x")
EXP_RANGE = {"easy": (2, 7), "medium": (2, 9), "hard": (2, 12)}
# Easy work keeps coefficients small but not fixed at 1 -- a constant
# coefficient collapses the sample space into a handful of archetypes.
COEF_RANGE = {"easy": (1, 4), "medium": (2, 9), "hard": (2, 12)}
# negative_exponents and zero_and_negative_powers each used a bare
# ``if difficulty == "easy"`` test, so they advertised three tiers and
# implemented two -- medium and hard were byte-identical. Three bands each.
NEG_BASES = {
    "easy": (2, 3, 4, 5),
    "medium": (2, 3, 4, 5, 6, 7, 10),
    "hard": (2, 3, 5, 6, 7, 10, 11, 12),
}
NEG_MAX_N = {"easy": 3, "medium": 4, "hard": 4}
NEG_COEF = {"easy": (1, 9), "medium": (1, 9), "hard": (2, 12)}
ZNP_BASES = {"easy": (2, 3, 5), "medium": (2, 3, 5, 6, 7), "hard": (2, 3, 5, 6, 7, 10)}
ZNP_A = {"easy": (2, 5), "medium": (2, 5), "hard": (2, 6)}
ZNP_B = {"easy": (-4, 0), "medium": (-4, 0), "hard": (-5, 0)}
# Powers stay readable: no key running to seven figures.
ZNP_MAX = 100_000


def _mk(question: str, expr, subskill: str, difficulty: str, kind: str = "simplify") -> Problem:
    return Problem(
        question_latex=f"${question}$",
        answer_latex=f"${sp.latex(expr)}$",
        answer_expr=expr,
        topic="exponents",
        subskill=subskill,
        difficulty=difficulty,
        verify={"kind": kind, "expr": question},
    )


@register("exponents", "product_rule")
def product_rule(rng: random.Random, difficulty: str) -> Problem:
    lo, hi = EXP_RANGE[difficulty]
    a, b = rng.randint(lo, hi), rng.randint(lo, hi)
    ca = rng.randint(*COEF_RANGE[difficulty])
    cb = rng.randint(*COEF_RANGE[difficulty])
    lead_a = "" if ca == 1 else str(ca)
    lead_b = "" if cb == 1 else str(cb)
    question = rf"{lead_a}x^{{{a}}} \cdot {lead_b}x^{{{b}}}"
    return _mk(question, ca * cb * X ** (a + b), "product_rule", difficulty)


@register("exponents", "quotient_rule")
def quotient_rule(rng: random.Random, difficulty: str) -> Problem:
    lo, hi = EXP_RANGE[difficulty]
    b = rng.randint(lo, hi)
    a = b + rng.randint(1, hi)  # keep the result a positive power
    k = rng.randint(*COEF_RANGE[difficulty])
    lead = "" if k == 1 else str(k)  # never "1x"
    question = rf"\dfrac{{{lead}x^{{{a}}}}}{{x^{{{b}}}}}"
    return _mk(question, k * X ** (a - b), "quotient_rule", difficulty)


@register("exponents", "power_rule")
def power_rule(rng: random.Random, difficulty: str) -> Problem:
    lo, hi = EXP_RANGE[difficulty]
    a, n = rng.randint(lo, hi), rng.randint(2, 4 if difficulty != "hard" else 5)
    k = rng.randint(*COEF_RANGE[difficulty])
    lead = "" if k == 1 else str(k)
    question = rf"({lead}x^{{{a}}})^{{{n}}}"
    return _mk(question, k**n * X ** (a * n), "power_rule", difficulty)


@register("exponents", "negative_exponents")
def negative_exponents(rng: random.Random, difficulty: str) -> Problem:
    """Numeric so the answer is a concrete fraction, not just a rewrite."""
    base = pick(rng, NEG_BASES[difficulty])
    n = rng.randint(1, NEG_MAX_N[difficulty])
    k = rng.randint(*NEG_COEF[difficulty])
    lead = "" if k == 1 else f"{k} \\cdot "

    style = rng.randrange(3)
    if style == 0:
        question = rf"{lead}{base}^{{-{n}}}"
        value = sp.Rational(k, base**n)
    elif style == 1:
        question = rf"\dfrac{{{k}}}{{{base}^{{-{n}}}}}"
        value = sp.Integer(k * base**n)
    else:
        m = rng.randint(1, n)
        question = rf"{lead}({base}^{{{m}}})^{{-{n}}}"
        value = sp.Rational(k, base ** (m * n))
    return _mk(question, value, "negative_exponents", difficulty, "evaluate")


@register("exponents", "combined_rules")
def combined_rules(rng: random.Random, difficulty: str) -> Problem:
    """Multi-variable expressions that stack several exponent rules at once:

    a nested power times a monomial, a quotient of two-variable monomials, a
    negative-exponent factor that must clean up positive, or a nested power
    of a quotient. Always resolves to a positive-exponent monomial.
    """
    lo, hi = EXP_RANGE[difficulty]
    Y = sp.Symbol("y")
    style = rng.randrange(4)

    if style == 0:
        ca = rng.randint(*COEF_RANGE[difficulty])
        a, b = rng.randint(lo, hi), rng.randint(1, hi)
        n = rng.randint(2, 3)
        cb = rng.randint(*COEF_RANGE[difficulty])
        c, d = rng.randint(lo, hi), rng.randint(1, hi)
        lead_a = "" if ca == 1 else str(ca)
        lead_b = "" if cb == 1 else str(cb)
        question = (
            rf"({lead_a}x^{{{a}}}y^{{{b}}})^{{{n}}} \cdot {lead_b}x^{{{c}}}y^{{{d}}}"
        )
        value = (ca**n) * cb * X ** (a * n + c) * Y ** (b * n + d)
    elif style == 1:
        ca = rng.randint(2, max(2, COEF_RANGE[difficulty][1]))
        divisors = [i for i in range(1, ca + 1) if ca % i == 0]
        cb = pick(rng, divisors)
        a = rng.randint(lo + 2, hi + 2)
        c = rng.randint(lo, a - 1)
        b = rng.randint(lo + 2, hi + 2)
        d = rng.randint(lo, b - 1)
        lead_a = "" if ca == 1 else str(ca)
        lead_b = "" if cb == 1 else str(cb)
        question = (
            rf"\dfrac{{{lead_a}x^{{{a}}}y^{{{b}}}}}{{{lead_b}x^{{{c}}}y^{{{d}}}}}"
        )
        value = sp.Rational(ca, cb) * X ** (a - c) * Y ** (b - d)
    elif style == 2:
        ca = rng.randint(2, 6)
        a = rng.randint(1, 3)
        n = rng.randint(2, 3)
        m = a * n + rng.randint(0, hi)
        question = rf"({ca}x^{{-{a}}})^{{{n}}} \cdot x^{{{m}}}"
        value = sp.Integer(ca**n) * X ** (m - a * n)
    else:
        ca = rng.randint(2, 6)
        divisors = [i for i in range(1, ca + 1) if ca % i == 0]
        cb = pick(rng, divisors)
        a = rng.randint(lo + 1, hi + 1)
        c = rng.randint(lo, a - 1)
        n = rng.randint(2, 3)
        lead_a = "" if ca == 1 else str(ca)
        lead_b = "" if cb == 1 else str(cb)
        question = rf"\left(\dfrac{{{lead_a}x^{{{a}}}}}{{{lead_b}x^{{{c}}}}}\right)^{{{n}}}"
        value = sp.Rational(ca, cb) ** n * X ** ((a - c) * n)

    return _mk(question, value, "combined_rules", difficulty)


def _ve(var: str, e: int) -> str:
    """A single ``var^e`` factor, omitted entirely when ``e == 0``."""
    if e == 0:
        return ""
    if e == 1:
        return var
    return f"{var}^{{{e}}}"


def _mvcoef(c: int) -> str:
    """A monomial's numeric coefficient, dropped entirely when it is 1.

    A quotient's denominator coefficient is drawn from the divisors of the
    numerator's so the two divide evenly, and 1 is always among them -- which
    printed a literal ``1x^{2}`` before this existed. Same class of bug as
    ``latexfmt.coeff``'s ``1y`` case, but for juxtaposed monomial factors
    rather than +/- joined terms.
    """
    return "" if c == 1 else str(c)


def _zero_pow(var: str) -> str:
    """A literal ``var^{0}`` factor, kept visible in the question.

    ``latexfmt.var_pow`` drops an exponent of 0 entirely, which is right when
    building an answer but wrong here: recognizing that anything to the zero
    power is 1 is the whole point of the exercise, so the factor has to be on
    the page for the student to cancel. The value passed to sympy still
    multiplies by ``var**0``, so the key shows it already simplified away.
    """
    return f"{var}^{{0}}"


MV_COEF = {"easy": (2, 6), "medium": (2, 9), "hard": (2, 12)}
MV_EXP = {"easy": (1, 5), "medium": (2, 7), "hard": (2, 9)}


@register("exponents", "multivariable_simplify")
def multivariable_simplify(rng: random.Random, difficulty: str) -> Problem:
    """Multi-variable simplification with zero/negative exponents; answers
    always have positive exponents only, printed as a fraction when needed.

    Five shapes rotate across draws: a plain product, a product where some
    exponents are negative, a power-of-product times an outer monomial, a
    whole parenthesized expression raised to a negative power, and a quotient
    that includes a zero-exponent factor.
    """
    clo, chi = MV_COEF[difficulty]
    elo, ehi = MV_EXP[difficulty]
    A, B, C = sp.symbols("a b c")
    style = rng.randrange(5)

    if style == 0:
        X, Y = sp.symbols("x y")
        ca, cb = rng.randint(clo, chi), rng.randint(clo, chi)
        a1, b1 = rng.randint(elo, ehi), rng.randint(elo, ehi)
        a2, b2 = rng.randint(elo, ehi), rng.randint(elo, ehi)
        question = (
            rf"{ca}{_mono(var_pow('x', a1), var_pow('y', b1))} \cdot "
            rf"{cb}{_mono(var_pow('x', a2), var_pow('y', b2))}"
        )
        value = ca * cb * X ** (a1 + a2) * Y ** (b1 + b2)
    elif style == 1:
        ca, cb = rng.randint(clo, chi), rng.randint(clo, chi)
        e1 = rng.randint(1, ehi)
        e2 = -rng.randint(1, ehi)
        e3 = -rng.randint(1, ehi)
        e4 = rng.randint(1, ehi)
        question = (
            rf"{ca}{_mono(var_pow('a', e1), var_pow('b', e2))} \cdot "
            rf"{cb}{_mono(var_pow('a', e3), var_pow('b', e4))}"
        )
        value = ca * cb * A ** (e1 + e3) * B ** (e2 + e4)
    elif style == 2:
        X, Y, Z = sp.symbols("x y z")
        ca = rng.randint(clo, chi)
        a = rng.randint(1, min(ehi, 5))
        cb = rng.randint(clo, chi)
        a2, b2, c2 = (rng.randint(1, min(ehi, 5)) for _ in range(3))
        n = rng.randint(2, 3)
        question = (
            rf"{ca}{var_pow('x', a)}"
            rf"({cb}{_mono(var_pow('x', a2), var_pow('y', b2), var_pow('z', c2))})^{{{n}}}"
        )
        value = ca * (cb**n) * X ** (a + a2 * n) * Y ** (b2 * n) * Z ** (c2 * n)
    elif style == 3:
        X, Y, Z = sp.symbols("x y z")
        c = pick(rng, (2, 3))
        ex = -rng.randint(1, min(ehi, 4))
        ey = rng.randint(1, min(ehi, 4))
        ez = -rng.randint(1, min(ehi, 4))
        n = pick(rng, (-1, -2))
        question = (
            rf"({c}{_mono(var_pow('x', ex), var_pow('y', ey), var_pow('z', ez))})^{{{n}}}"
        )
        value = sp.Integer(c) ** n * X ** (ex * n) * Y ** (ey * n) * Z ** (ez * n)
    else:
        X, Y, Z = sp.symbols("x y z")
        ca = rng.randint(clo, chi)
        divisors = [i for i in range(1, ca + 1) if ca % i == 0]
        cb = pick(rng, divisors)
        a1, b1 = rng.randint(elo, ehi), -rng.randint(1, ehi)
        a2 = rng.randint(1, a1 - 1) if a1 > 1 else 0
        b2 = -rng.randint(1, ehi)
        c1 = rng.randint(1, ehi)
        question = (
            rf"\dfrac{{{_mvcoef(ca)}"
            rf"{_mono(var_pow('x', a1), var_pow('y', b1), var_pow('z', c1))}}}"
            rf"{{{_mvcoef(cb)}"
            rf"{_mono(var_pow('x', a2), var_pow('y', b2), _zero_pow('z'))}}}"
        )
        value = sp.Rational(ca, cb) * X ** (a1 - a2) * Y ** (b1 - b2) * Z**c1

    return _mk(question, value, "multivariable_simplify", difficulty)


@register("exponents", "zero_and_negative_powers")
def zero_and_negative_powers(rng: random.Random, difficulty: str) -> Problem:
    """Mixed product of powers of the same base, including zero exponents."""
    while True:
        base = pick(rng, ZNP_BASES[difficulty])
        a = rng.randint(*ZNP_A[difficulty])
        b = rng.randint(*ZNP_B[difficulty])
        value = sp.Rational(base) ** (a + b)
        if max(abs(sp.numer(value)), abs(sp.denom(value))) <= ZNP_MAX:
            break
    question = rf"{base}^{{{a}}} \cdot {base}^{{{b}}}"
    return _mk(question, value, "zero_and_negative_powers", difficulty, "evaluate")
