"""Cross-generator sweeps for the coefficient bugs that keep coming back.

test_latexfmt.py checks the formatting primitives in isolation; this file
checks that every generator actually *uses* them, by sweeping real output.
"""

from __future__ import annotations

import random
import re

import pytest

from forge.core.problem import DIFFICULTIES
from forge.core.registry import all_generators

SEEDS = 300

# "1x", "1y", "1x^2" -- an implicit coefficient of 1 must never be printed.
ONE_COEFF = re.compile(r"(?<![\d.])1\s*[a-zA-Z](?![a-zA-Z])")
# "0x" -- a zero term must be dropped, not printed.
ZERO_COEFF = re.compile(r"(?<![\d.])0\s*[a-zA-Z](?![a-zA-Z])")
NEG_ONE_COEFF = re.compile(r"-\s*1\s*[a-zA-Z](?![a-zA-Z])")
PLUS_NEGATIVE = re.compile(r"\+\s*-")


def _texts():
    for key, gen in sorted(all_generators().items()):
        for seed in range(SEEDS):
            p = gen(random.Random(seed), DIFFICULTIES[seed % len(DIFFICULTIES)])
            yield key, seed, p


@pytest.mark.parametrize("pattern,label", [
    (ONE_COEFF, "an explicit coefficient of 1 (write 'y', not '1y')"),
    (NEG_ONE_COEFF, "an explicit coefficient of -1 (write '-x', not '-1x')"),
    (ZERO_COEFF, "a zero coefficient (drop the term)"),
    (PLUS_NEGATIVE, "'+ -' (write '- n')"),
])
def test_no_coefficient_smells(pattern, label):
    offenders = []
    for key, seed, p in _texts():
        for field in (p.question_latex, p.answer_latex):
            # Exponents and fraction internals legitimately contain a bare 1.
            stripped = re.sub(r"\^\{[^{}]*\}", "", field)
            stripped = re.sub(r"\\d?frac\{[^{}]*\}\{[^{}]*\}", "", stripped)
            if pattern.search(stripped):
                offenders.append(f"{key[0]}/{key[1]} seed {seed}: {field}")
    assert not offenders, (
        f"{len(offenders)} problem(s) printed {label}:\n  "
        + "\n  ".join(offenders[:10])
    )


def test_zero_slope_renders_without_x():
    """A zero slope must give 'y = 5', never 'y = 0x + 5'.

    ``identify_slope_intercept`` no longer samples a zero slope: Part 10's
    directions now ask for the x-intercept too, which is undefined for a
    horizontal line, so that generator is built backwards from a nonzero
    slope and a clean x-intercept (see ``_line_with_x_intercept`` in
    ``forge/generators/slope.py``). ``equation_from_two_points`` still draws
    ``m`` unrestricted via ``_line``'s default ``allow_zero_slope=True``, so
    the "0x" rendering bug is swept there instead.
    """
    gen = all_generators()[("slope", "equation_from_two_points")]
    found_zero_slope = False
    for seed in range(2000):
        p = gen(random.Random(seed), "medium")
        if p.answer_expr[0] == 0:
            found_zero_slope = True
            assert "x" not in p.answer_latex, p.answer_latex
    assert found_zero_slope, "never sampled a zero slope; widen the sweep"


def test_answers_are_never_floats():
    """No decimal answers -- they are almost always a float artifact.

    ``scientific_notation`` and ``decimals`` are the honest exceptions: for
    both, a decimal point *is* the subject matter -- converting between
    ``3.4 x 10^-3`` and ``0.0034``, or between ``0.35`` and ``7/20``. Their
    exactness is held instead by ``test_decimal_answers_stay_exact`` below;
    the point of this rule is to catch 0.30000000000000004, not the digit.
    """
    for key, seed, p in _texts():
        if key[0] in ("scientific_notation", "decimals"):
            continue
        assert "." not in p.answer_latex, f"{key} seed {seed}: {p.answer_latex}"


def test_decimal_answers_stay_exact():
    """Their decimals must be exact rationals, never binary floats."""
    import sympy as sp

    for key, seed, p in _texts():
        if key[0] not in ("scientific_notation", "decimals"):
            continue
        assert not p.answer_expr.atoms(sp.Float), (
            f"{key} seed {seed}: answer carries a Float, not an exact value: "
            f"{p.answer_expr!r}"
        )


def test_math_mode_is_balanced():
    for key, seed, p in _texts():
        for field in (p.question_latex, p.answer_latex):
            # An escaped \$ consumes one literal "$" and is not a delimiter.
            dollars = field.count("$") - field.count(r"\$")
            assert dollars % 2 == 0, f"{key} seed {seed}: unbalanced math mode in {field}"


def test_word_problems_agree_in_number():
    """No "1 plants": a quantity of 1 must never precede a plural noun."""
    from forge.generators.word_problems import ITEMS

    plurals = [plural for plural, _ in ITEMS]
    bad = re.compile(r"\b1\$?\s+(" + "|".join(plurals) + r")\b")
    for key, seed, p in _texts():
        if key[0] != "word_problems":
            continue
        assert not bad.search(p.question_latex), f"{key} seed {seed}: {p.question_latex}"
