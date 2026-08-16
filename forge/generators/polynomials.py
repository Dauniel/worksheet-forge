"""Polynomial multiplication and factoring.

Verified by re-expanding the printed question and the printed answer with
sympy and requiring they're algebraically identical -- the existing
``simplify`` strategy already does exactly that, so no new verify code is
needed here.
"""

from __future__ import annotations

import random

import sympy as sp

from ..core.latexfmt import coeff, linear, num, poly, terms
from ..core.problem import Problem
from ..core.registry import register
from ..core.sampling import nonzero_int, pick

RANGES = {"easy": (1, 6), "medium": (2, 9), "hard": (2, 12)}
X = sp.Symbol("x")


def _term_str(c: int, power: int) -> str:
    """A single ``c*x^power`` term, ``power`` possibly 0 (constant) or 1 (bare x)."""
    if power == 0:
        return num(c)
    if power == 1:
        return coeff(c, "x")
    return coeff(c, f"x^{{{power}}}")


def _sparse(pairs) -> str:
    """Render (coeff, power) pairs *in the given order* -- not necessarily
    descending, so this also drives ``standard_form``'s scrambled question."""
    return terms(*[_term_str(c, p) for c, p in pairs])


def _mk(question: str, answer: str, answer_expr, subskill: str, difficulty: str) -> Problem:
    return Problem(
        question_latex=f"${question}$",
        answer_latex=f"${answer}$",
        answer_expr=answer_expr,
        topic="polynomials",
        subskill=subskill,
        difficulty=difficulty,
        verify={"kind": "simplify"},
    )


@register("polynomials", "multiply_binomials")
def multiply_binomials(rng: random.Random, difficulty: str) -> Problem:
    """``(a1 x + b1)(a2 x + b2)``, expanded via FOIL."""
    _, hi = RANGES[difficulty]
    a1 = nonzero_int(rng, 1, min(hi, 5))
    a2 = nonzero_int(rng, 1, min(hi, 5))
    b1 = nonzero_int(rng, -hi, hi)
    b2 = nonzero_int(rng, -hi, hi)

    question = f"({linear(a1, b1)})({linear(a2, b2)})"
    c2, c1, c0 = a1 * a2, a1 * b2 + a2 * b1, b1 * b2
    answer_expr = c2 * X**2 + c1 * X + c0
    return _mk(question, poly([c2, c1, c0]), answer_expr, "multiply_binomials", difficulty)


@register("polynomials", "factor_trinomial")
def factor_trinomial(rng: random.Random, difficulty: str) -> Problem:
    """``x^2 + bx + c``, factored from two chosen integer roots ``p, q``."""
    _, hi = RANGES[difficulty]
    p = nonzero_int(rng, -hi, hi)
    q = nonzero_int(rng, -hi, hi)
    while q == p:
        q = nonzero_int(rng, -hi, hi)
    p, q = sorted((p, q))

    b, c = p + q, p * q
    question = poly([1, b, c])
    answer = f"({linear(1, p)})({linear(1, q)})"
    answer_expr = (X + p) * (X + q)
    return _mk(question, answer, answer_expr, "factor_trinomial", difficulty)


DIFF_SQ_HI = {"easy": 90, "medium": 110, "hard": 130}


@register("polynomials", "difference_of_squares")
def difference_of_squares(rng: random.Random, difficulty: str) -> Problem:
    """``x^2 - r^2``, factored as ``(x - r)(x + r)``.

    ``s`` is always 1 here -- a non-unit leading coefficient belongs only to
    ``factor_difference_of_squares_lead``, which additionally guarantees
    ``r`` is coprime with the leading coefficient so the factorization is
    always complete. Letting ``s`` vary here produced incompletely-factored
    answers like ``9x^2-81 -> (3x-9)(3x+9)``, where each factor still shares
    a common factor of 3.

    ``r`` starts at 2 (``x^2 - 1`` is a degenerate, pedagogically trivial
    draw) and its range is widened well past the other subskills' to
    compensate for ``s`` no longer contributing any variance -- with ``s``
    locked to 1, ``r`` alone has to clear ``test_no_hardcoded_problem_lists``'s
    distinct-draws floor.
    """
    hi = DIFF_SQ_HI[difficulty]
    r = nonzero_int(rng, 2, hi)
    s = 1

    question = poly([s * s, 0, -r * r])
    lead = coeff(s, "x")
    answer = f"({terms(lead, num(-r))})({terms(lead, num(r))})"
    answer_expr = (s * X - r) * (s * X + r)
    return _mk(question, answer, answer_expr, "difference_of_squares", difficulty)


@register("polynomials", "synthetic_division")
def synthetic_division(rng: random.Random, difficulty: str) -> Problem:
    """Divide a cubic (or quartic at hard) by ``x - r``, exactly.

    Built backwards: pick the quotient and the root, multiply to get the
    dividend. That forces a zero remainder, which keeps the answer a clean
    polynomial -- and lets the existing ``simplify`` strategy verify it, since
    the printed question is then a rational expression algebraically equal to
    the printed quotient.
    """
    _, hi = RANGES[difficulty]
    degree = 3 if difficulty == "hard" else 2
    quotient = [nonzero_int(rng, 1, min(hi, 4))]
    quotient += [nonzero_int(rng, -hi, hi) for _ in range(degree)]
    r = nonzero_int(rng, -min(hi, 6), min(hi, 6))

    q_expr = sum(c * X ** (degree - i) for i, c in enumerate(quotient))
    dividend = sp.expand((X - r) * q_expr)
    dividend_coeffs = [int(dividend.coeff(X, k)) for k in range(degree + 1, -1, -1)]

    question = rf"\dfrac{{{poly(dividend_coeffs)}}}{{{linear(1, -r)}}}"
    return _mk(question, poly(quotient), q_expr, "synthetic_division", difficulty)


@register("polynomials", "factor_by_grouping")
def factor_by_grouping(rng: random.Random, difficulty: str) -> Problem:
    """``x^3 + ax^2 + bx + ab`` factors as ``(x + a)(x^2 + b)``.

    Built from the two factors outward, so the grouping always works -- a
    randomly drawn cubic almost never factors over the integers.
    """
    _, hi = RANGES[difficulty]
    a = nonzero_int(rng, -hi, hi)
    lead = nonzero_int(rng, 2, 3) if difficulty == "hard" else 1
    # b may be negative: x^3 + ax^2 - bx - ab groups just as cleanly, and
    # allowing the sign doubles a space that was small enough to make the
    # same first problem recur across seeds. Resampled until coprime with
    # ``lead`` so the quadratic factor ``lead*x^2 + b`` is always primitive
    # -- otherwise e.g. ``lead=2, b=4`` leaves a common factor of 2 inside
    # that factor, an incomplete factorization.
    while True:
        b = nonzero_int(rng, -hi, hi)
        if sp.gcd(lead, b) == 1:
            break

    expanded = sp.expand((X + a) * (lead * X**2 + b))
    coeffs = [int(expanded.coeff(X, k)) for k in range(3, -1, -1)]
    answer = f"({linear(1, a)})({poly([lead, 0, b])})"
    return _mk(poly(coeffs), answer, expanded, "factor_by_grouping", difficulty)


# --------------------------------------------------------------------------
# Part 1-7 additions: classifying, standard form, +/-, products, division,
# and factoring with a non-monic or perfect-square-lead coefficient.
# --------------------------------------------------------------------------

CLASSES = ("monomial", "binomial", "trinomial", "polynomial", "constant")


@register("polynomials", "classify_polynomial")
def classify_polynomial(rng: random.Random, difficulty: str) -> Problem:
    """Classify by term count: monomial/binomial/trinomial/polynomial(4-6
    terms)/constant. Answer is the bare word -- verified structurally by
    re-counting the printed expression's terms, not by re-solving anything.
    """
    _, hi = RANGES[difficulty]
    cat = pick(rng, CLASSES)
    if cat == "constant":
        c = nonzero_int(rng, -5 * hi, 5 * hi)
        question = num(c)
    else:
        nterms = {"monomial": 1, "binomial": 2, "trinomial": 3}.get(
            cat, rng.randint(4, 6)
        )
        degree = nterms - 1 + rng.randint(0, 2)
        if cat == "monomial":
            degree = max(degree, 1)  # a bare number is a constant, not a monomial
        powers = sorted(rng.sample(range(0, degree + 1), nterms), reverse=True)
        if degree not in powers:
            powers[0] = degree
        coeffs = [nonzero_int(rng, -hi, hi) for _ in powers]
        question = _sparse(list(zip(coeffs, powers)))
    answer = cat.capitalize()
    return Problem(
        question_latex=f"${question}$",
        answer_latex=rf"$\text{{{answer}}}$",
        answer_expr=answer,
        topic="polynomials",
        subskill="classify_polynomial",
        difficulty=difficulty,
        verify={"kind": "classify_polynomial"},
    )


@register("polynomials", "standard_form")
def standard_form(rng: random.Random, difficulty: str) -> Problem:
    """A scrambled-order polynomial; the answer is the same polynomial with
    powers strictly descending. Verified structurally (descending exponents
    in the printed key) plus an algebraic-identity check against the question.
    """
    _, hi = RANGES[difficulty]
    nterms = rng.randint(3, 5)
    degree = nterms - 1 + rng.randint(0, 2)
    powers = sorted(rng.sample(range(0, degree + 1), min(nterms, degree + 1)), reverse=True)
    if degree not in powers:
        powers[0] = degree
    coeffs = [nonzero_int(rng, -hi, hi) for _ in powers]
    pairs = list(zip(coeffs, powers))
    scrambled = pairs[:]
    while True:
        rng.shuffle(scrambled)
        if scrambled != pairs:
            break
    question = _sparse(scrambled)
    answer = _sparse(pairs)
    dense = [0] * (degree + 1)
    for c, p in pairs:
        dense[degree - p] = c
    answer_expr = sum(c * X**p for c, p in pairs)
    return Problem(
        question_latex=f"${question}$",
        answer_latex=f"${answer}$",
        answer_expr=answer_expr,
        topic="polynomials",
        subskill="standard_form",
        difficulty=difficulty,
        verify={"kind": "standard_form"},
    )


ADD_RANGES = {"easy": (1, 6), "medium": (2, 12), "hard": (2, 20)}


def _random_degree(rng: random.Random, difficulty: str) -> int:
    """Degree for add/subtract polynomials -- mostly quadratic/cubic, with an
    occasional sparse high-degree draw at "medium" to match the source
    assignment (mostly small polynomials, the occasional sparse high-degree
    pair). "Hard" keeps the original wide 2-6 range unscoped by this change.
    """
    if difficulty == "medium" and rng.random() >= 0.175:
        return rng.randint(2, 3)
    return rng.randint(2, 6)


def _random_poly_coeffs(rng: random.Random, difficulty: str, sparse: bool = False):
    """A dense highest-degree-first coefficient list, degree 2-6 (2-3 typical
    at "medium" -- see :func:`_random_degree`)."""
    lo, hi = ADD_RANGES[difficulty]
    degree = _random_degree(rng, difficulty)
    coeffs = [nonzero_int(rng, -hi, hi) for _ in range(degree + 1)]
    if sparse:
        for i in range(1, degree):
            if rng.random() < 0.5:
                coeffs[i] = 0
    return coeffs, degree


@register("polynomials", "add_polynomials")
def add_polynomials(rng: random.Random, difficulty: str) -> Problem:
    """``(p1) + (p2)``, degree 2-6, sometimes sparse or high-degree."""
    sparse = rng.random() < 0.35
    c1, d1 = _random_poly_coeffs(rng, difficulty, sparse)
    c2, d2 = _random_poly_coeffs(rng, difficulty, sparse)
    question = f"({poly(c1)}) + ({poly(c2)})"
    e1 = sum(c * X ** (d1 - i) for i, c in enumerate(c1))
    e2 = sum(c * X ** (d2 - i) for i, c in enumerate(c2))
    answer_expr = sp.expand(e1 + e2)
    return _mk(question, poly_from_expr(answer_expr), answer_expr, "add_polynomials", difficulty)


@register("polynomials", "subtract_polynomials")
def subtract_polynomials(rng: random.Random, difficulty: str) -> Problem:
    """``(p1) - (p2)``, degree 2-6, sometimes sparse or high-degree."""
    sparse = rng.random() < 0.35
    c1, d1 = _random_poly_coeffs(rng, difficulty, sparse)
    c2, d2 = _random_poly_coeffs(rng, difficulty, sparse)
    question = f"({poly(c1)}) - ({poly(c2)})"
    e1 = sum(c * X ** (d1 - i) for i, c in enumerate(c1))
    e2 = sum(c * X ** (d2 - i) for i, c in enumerate(c2))
    answer_expr = sp.expand(e1 - e2)
    return _mk(question, poly_from_expr(answer_expr), answer_expr, "subtract_polynomials", difficulty)


def poly_from_expr(expr) -> str:
    """Render an already-expanded sympy polynomial in ``x`` with :func:`poly`."""
    expr = sp.expand(expr)
    if expr == 0:
        return "0"
    degree = sp.degree(expr, X)
    coeffs = [int(expr.coeff(X, k)) for k in range(degree, -1, -1)]
    return poly(coeffs)


MONO_HI = {"easy": (1, 5), "medium": (2, 8), "hard": (2, 12)}


@register("polynomials", "multiply_monomial")
def multiply_monomial(rng: random.Random, difficulty: str) -> Problem:
    """``c*x^n * (poly)``, e.g. ``2x(4x^2)``, ``4x(1 - x)``, ``3x(-x^2+2x-12)``."""
    lo, hi = MONO_HI[difficulty]
    mono_c = nonzero_int(rng, lo, hi)
    mono_p = rng.randint(1, 3)
    mono_str = _term_str(mono_c, mono_p)
    mono_expr = mono_c * X**mono_p

    inner_deg = rng.randint(1, 2)
    inner_coeffs = [nonzero_int(rng, -hi, hi) for _ in range(inner_deg + 1)]
    inner_expr = sum(c * X ** (inner_deg - i) for i, c in enumerate(inner_coeffs))

    question = f"{mono_str}({poly(inner_coeffs)})"
    answer_expr = sp.expand(mono_expr * inner_expr)
    return _mk(question, poly_from_expr(answer_expr), answer_expr, "multiply_monomial", difficulty)


@register("polynomials", "multiply_poly")
def multiply_poly(rng: random.Random, difficulty: str) -> Problem:
    """Binomial times trinomial (or larger), e.g. ``(4x+1)(x^2-4x+5)``."""
    _, hi = RANGES[difficulty]
    hi = min(hi, 9)
    d1 = 1
    d2 = 2 if difficulty != "hard" else pick(rng, (2, 2, 3))
    c1 = [nonzero_int(rng, -hi, hi) for _ in range(d1 + 1)]
    c2 = [nonzero_int(rng, -hi, hi) for _ in range(d2 + 1)]
    e1 = sum(c * X ** (d1 - i) for i, c in enumerate(c1))
    e2 = sum(c * X ** (d2 - i) for i, c in enumerate(c2))
    question = f"({poly(c1)})({poly(c2)})"
    answer_expr = sp.expand(e1 * e2)
    return _mk(question, poly_from_expr(answer_expr), answer_expr, "multiply_poly", difficulty)


DIV_HI = {"easy": (1, 5), "medium": (2, 8), "hard": (2, 10)}


@register("polynomials", "divide_by_monomial")
def divide_by_monomial(rng: random.Random, difficulty: str) -> Problem:
    """Built backwards from the quotient so the division is always exact:
    choose the quotient and the monomial divisor, multiply to get the
    dividend, e.g. ``(20x^4+15x^2)/(5x^2)``, ``(-18x^2+21x)/(-3)``.
    """
    lo, hi = DIV_HI[difficulty]
    div_c = nonzero_int(rng, lo, hi) * rng.choice((-1, 1))
    div_p = rng.randint(0, 2)
    divisor_expr = div_c * X**div_p

    nterms = rng.randint(2, 3)
    max_power = rng.randint(div_p + 1, div_p + 4)
    powers = sorted(rng.sample(range(div_p, max_power + 1), min(nterms, max_power - div_p + 1)), reverse=True)
    if max_power not in powers:
        powers[0] = max_power
    q_coeffs = [nonzero_int(rng, -hi, hi) for _ in powers]
    quotient_expr = sum(c * X ** p for c, p in zip(q_coeffs, powers))
    dividend_expr = sp.expand(quotient_expr * divisor_expr)

    divisor_str = num(div_c) if div_p == 0 else _term_str(div_c, div_p)
    dividend_str = poly_from_expr(dividend_expr)
    question = rf"\dfrac{{{dividend_str}}}{{{divisor_str}}}"
    answer_str = _sparse(list(zip(q_coeffs, powers)))
    return _mk(question, answer_str, quotient_expr, "divide_by_monomial", difficulty)


LEAD_HI = {"easy": (1, 6), "medium": (1, 8), "hard": (1, 9)}


@register("polynomials", "factor_trinomial_lead")
def factor_trinomial_lead(rng: random.Random, difficulty: str) -> Problem:
    """``a*x^2+bx+c`` with ``a > 1``, built backwards from ``(mx+n)(px+q)``.

    Mirrors ``quadratics.solve_by_factoring``'s denominator trick: choosing
    ``m, p`` as the two leading factors (rather than scaling a monic
    trinomial by a constant) is what keeps the leading coefficient genuinely
    non-monic instead of a common factor a student could divide away first.
    """
    hi = LEAD_HI[difficulty][1]
    while True:
        m = pick(rng, (2, 3, 4) if difficulty != "easy" else (2, 3))
        p = pick(rng, (1, 2, 3))
        n = nonzero_int(rng, -hi, hi)
        q = nonzero_int(rng, -hi, hi)
        # Each linear factor must itself be primitive, or that factor still
        # has a common factor a student could pull out (e.g. m=2, n=4 leaves
        # (2x+4) = 2(x+2), an incomplete factorization) even though the
        # overall trinomial's gcd check below passes.
        if sp.gcd(m, n) != 1 or sp.gcd(p, q) != 1:
            continue
        a, b, c = m * p, m * q + n * p, n * q
        if a <= 1:
            continue
        if sp.gcd(sp.gcd(a, b), c) != 1:
            continue
        if sp.Rational(-n, m) == sp.Rational(-q, p):
            continue
        break
    question = poly([a, b, c])
    answer = f"({linear(m, n)})({linear(p, q)})"
    answer_expr = (m * X + n) * (p * X + q)
    return _mk(question, answer, answer_expr, "factor_trinomial_lead", difficulty)


DIFF_SQ_LEAD_HI = {"easy": 60, "medium": 90, "hard": 120}


@register("polynomials", "factor_difference_of_squares_lead")
def factor_difference_of_squares_lead(rng: random.Random, difficulty: str) -> Problem:
    """``(sx)^2 - r^2`` with ``s >= 2``, so the leading coefficient is itself
    a perfect square greater than 1 (``4x^2-25``, ``9x^2-49``) -- the
    ``s = 1`` case is already covered by ``difference_of_squares``.

    ``r`` is resampled until it's coprime with ``s``: otherwise
    ``gcd(s, r) > 1`` divides both ``(sx - r)`` and ``(sx + r)`` and the
    answer isn't fully factored (e.g. ``4x^2-36 -> (2x-6)(2x+6)``, each
    factor still divisible by 2).
    """
    hi = DIFF_SQ_LEAD_HI[difficulty]
    s = pick(rng, (2, 3))
    while True:
        r = nonzero_int(rng, 1, hi)
        if sp.gcd(s, r) == 1:
            break
    question = poly([s * s, 0, -r * r])
    lead = coeff(s, "x")
    answer = f"({terms(lead, num(-r))})({terms(lead, num(r))})"
    answer_expr = (s * X - r) * (s * X + r)
    return _mk(question, answer, answer_expr, "factor_difference_of_squares_lead", difficulty)
