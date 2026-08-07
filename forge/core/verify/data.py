"""Verification strategies for numeric and prose work: percents, word
problems, scientific notation, statistics, probability, and classification.
"""

from __future__ import annotations

import re
from typing import List

import sympy as sp

from ..problem import Problem

from .parsing import (
    VerificationError,
    _equal,
    _nums,
    _nums_any,
    latex_to_sympy,
)


_PERCENT_OF = re.compile(r"(-?[\d.]+)\s*\\?%\s*\$?\s*of\s*\$?\s*(-?[\d.]+)")

_CHANGE = re.compile(r"from\s*\$?\\?\$?(-?[\d.]+)\$?\s*to\s*\$?\\?\$?(-?[\d.]+)")

def _v_percent_of(p: Problem) -> None:
    m = _PERCENT_OF.search(p.question_latex)
    if not m:
        raise VerificationError(f"{p.topic}/{p.subskill}: cannot read {p.question_latex!r}")
    pct, whole = sp.Rational(m.group(1)), sp.Rational(m.group(2))
    if not _equal(pct / 100 * whole, p.answer_expr):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {p.question_latex} -> {pct / 100 * whole}, "
            f"key says {p.answer_expr}"
        )

def _v_percent_change(p: Problem) -> None:
    m = _CHANGE.search(p.question_latex)
    if not m:
        raise VerificationError(f"{p.topic}/{p.subskill}: cannot read {p.question_latex!r}")
    old, new = sp.Rational(m.group(1)), sp.Rational(m.group(2))
    if old == 0:
        raise VerificationError(f"{p.topic}/{p.subskill}: percent change from zero")
    change = (new - old) / old * 100
    if not _equal(change, p.answer_expr):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {p.question_latex} -> {change}%, key says {p.answer_expr}"
        )

def _v_word(p: Problem) -> None:
    """Word problems: re-solve the model, and confirm it matches the prose.

    A templated sentence cannot be parsed back the way an expression can, so
    this does two things instead: it re-solves the stated equation from
    scratch, and it asserts every sampled quantity actually appears in the
    question text -- catching the case where the model and the prose drift.
    """
    var = sp.Symbol(p.verify.get("var", "x"))
    lhs = latex_to_sympy(p.verify["lhs"])
    rhs = latex_to_sympy(p.verify["rhs"])
    sols = sp.solve(sp.Eq(lhs, rhs), var)
    if len(sols) != 1 or not _equal(sols[0], p.answer_expr):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: model {p.verify['lhs']} = {p.verify['rhs']} "
            f"solves to {sols}, key says {p.answer_expr}"
        )
    for q in p.verify.get("quantities", []):
        if str(q) not in p.question_latex:
            raise VerificationError(
                f"{p.topic}/{p.subskill}: quantity {q} is in the model but not in the "
                f"prose: {p.question_latex!r}"
            )

_SCI = re.compile(r"(-?\d+(?:\.\d+)?)\s*\\times\s*10\^\{(-?\d+)\}")

def _sci_values(text: str) -> List[sp.Rational]:
    """Every ``c x 10^e`` in a string, as exact rationals."""
    return [
        sp.Rational(c) * sp.Integer(10) ** int(e) for c, e in _SCI.findall(text)
    ]

def _one_sci(p: Problem, text: str, where: str) -> sp.Rational:
    vals = _sci_values(text)
    if len(vals) != 1:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: expected one scientific-notation value "
            f"in the {where}, found {len(vals)}"
        )
    return vals[0]

def _check_normalized(p: Problem, text: str) -> None:
    """A scientific-notation answer must have its coefficient in [1, 10)."""
    m = _SCI.search(text)
    if m is None:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: answer is not in scientific notation"
        )
    coeff = abs(sp.Rational(m.group(1)))
    if not (1 <= coeff < 10):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: coefficient {coeff} is not in [1, 10)"
        )

def _v_sci_to_scientific(p: Problem) -> None:
    """Question is the plain number; the answer restates it in sci notation."""
    plain = _nums_any(p.question_latex)
    _check_normalized(p, p.answer_latex)
    stated = _one_sci(p, p.answer_latex, "answer")
    if not _equal(plain, stated):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {stated} is not equal to {plain}"
        )

def _v_sci_from_scientific(p: Problem) -> None:
    """Question is scientific notation; the answer is the plain number."""
    stated = _one_sci(p, p.question_latex, "question")
    plain = _nums_any(p.answer_latex)
    if not _equal(plain, stated):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {plain} is not equal to {stated}"
        )

def _v_sci_multiply_divide(p: Problem) -> None:
    operands = _sci_values(p.question_latex)
    if len(operands) != 2:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: expected two operands, found {len(operands)}"
        )
    a, b = operands
    # Read the operator that sits between the two parenthesised operands.
    between = p.question_latex.split(")", 1)[1]
    if between.lstrip().startswith("\\div"):
        expected = a / b
    else:
        expected = a * b
    _check_normalized(p, p.answer_latex)
    if not _equal(expected, p.answer_expr):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: result should be {expected}"
        )

def _bag_counts(p: Problem):
    """The two printed counts, favourable first, as the frames always order."""
    counts = _nums(p.question_latex)
    if len(counts) != 2:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: expected 2 counts, found {len(counts)}"
        )
    favourable, other = counts
    return favourable, favourable + other

def _v_prob_simple(p: Problem) -> None:
    fav, total = _bag_counts(p)
    expected = sp.Rational(fav, total)
    if not _equal(expected, p.answer_expr):
        raise VerificationError(f"{p.topic}/{p.subskill}: should be {expected}")

def _v_prob_independent(p: Problem) -> None:
    fav, total = _bag_counts(p)
    expected = sp.Rational(fav, total) ** 2
    if not _equal(expected, p.answer_expr):
        raise VerificationError(f"{p.topic}/{p.subskill}: should be {expected}")

def _v_prob_dependent(p: Problem) -> None:
    fav, total = _bag_counts(p)
    expected = sp.Rational(fav, total) * sp.Rational(fav - 1, total - 1)
    if not _equal(expected, p.answer_expr):
        raise VerificationError(f"{p.topic}/{p.subskill}: should be {expected}")

def _data_set(p: Problem) -> List[sp.Integer]:
    """Re-read a statistics data set off the printed list."""
    values = _nums(p.question_latex)
    if not values:
        raise VerificationError(f"{p.topic}/{p.subskill}: no data set in question")
    return values

def _v_stat_mean(p: Problem) -> None:
    v = _data_set(p)
    expected = sp.Rational(sum(v), len(v))
    if not _equal(expected, p.answer_expr):
        raise VerificationError(f"{p.topic}/{p.subskill}: mean should be {expected}")

def _v_stat_median(p: Problem) -> None:
    v = sorted(_data_set(p))
    mid = len(v) // 2
    expected = (
        sp.Rational(v[mid - 1] + v[mid], 2) if len(v) % 2 == 0 else sp.Integer(v[mid])
    )
    if not _equal(expected, p.answer_expr):
        raise VerificationError(f"{p.topic}/{p.subskill}: median should be {expected}")

def _v_stat_mode(p: Problem) -> None:
    v = _data_set(p)
    counts = {x: v.count(x) for x in v}
    best = max(counts.values())
    winners = [x for x, c in counts.items() if c == best]
    if len(winners) != 1:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: data set has no single mode ({winners})"
        )
    if not _equal(winners[0], p.answer_expr):
        raise VerificationError(f"{p.topic}/{p.subskill}: mode should be {winners[0]}")

def _v_stat_range(p: Problem) -> None:
    v = _data_set(p)
    expected = max(v) - min(v)
    if not _equal(expected, p.answer_expr):
        raise VerificationError(f"{p.topic}/{p.subskill}: range should be {expected}")

def _classify_value(value) -> set:
    labels: set = set()
    if bool(value.is_rational):
        labels.add("rational")
        if bool(value.is_integer):
            labels.add("integer")
            if value >= 0:
                labels.add("whole")
    else:
        labels.add("irrational")
    return labels

def _v_classify(p: Problem) -> None:
    value = latex_to_sympy(p.question_latex)
    got = _classify_value(value)
    expected = set(p.answer_expr)
    if got != expected:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {p.question_latex} classifies as {got}, "
            f"key says {expected}"
        )
    # The PRINTED key ("Rational, Integer, Whole") must name the same labels.
    printed = {s.strip().lower() for s in p.answer_latex.strip("$").split(",") if s.strip()}
    if printed != got:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: printed key {p.answer_latex!r} says {printed}, "
            f"but {p.question_latex} classifies as {got}"
        )

def _v_estimate_percent(p: Problem) -> None:
    # order in the prose: actual_pct, actual_whole, friendly_pct, friendly_whole
    _, _, fpct, fwhole = _nums(p.question_latex)
    expected = sp.Rational(fpct, 100) * fwhole
    if not _equal(expected, p.answer_expr):
        raise VerificationError(f"{p.topic}/{p.subskill}: estimate should be {expected}")

def _v_markup_discount(p: Problem) -> None:
    original, pct = _nums(p.question_latex)
    sign = -1 if "discount" in p.question_latex.lower() or "off" in p.question_latex.lower() \
        or "sale" in p.question_latex.lower() or "clearance" in p.question_latex.lower() else 1
    expected = original + sign * sp.Rational(pct, 100) * original
    if not _equal(expected, p.answer_expr):
        raise VerificationError(f"{p.topic}/{p.subskill}: new price should be {expected}")

def _v_percent_error(p: Problem) -> None:
    actual, measured = _nums(p.question_latex)
    if actual == 0:
        raise VerificationError(f"{p.topic}/{p.subskill}: percent error from zero actual value")
    expected = sp.Abs(measured - actual) / actual * 100
    if not _equal(expected, p.answer_expr):
        raise VerificationError(f"{p.topic}/{p.subskill}: percent error should be {expected}")

def _v_commission(p: Problem) -> None:
    pct, sales = _nums(p.question_latex)
    expected = sp.Rational(pct, 100) * sales
    if not _equal(expected, p.answer_expr):
        raise VerificationError(f"{p.topic}/{p.subskill}: commission should be {expected}")

def _v_tax_tip(p: Problem) -> None:
    amount, pct = _nums(p.question_latex)
    expected = amount + sp.Rational(pct, 100) * amount
    if not _equal(expected, p.answer_expr):
        raise VerificationError(f"{p.topic}/{p.subskill}: total should be {expected}")

def _v_unit_rate(p: Problem) -> None:
    total, quantity = _nums(p.question_latex)
    if quantity == 0:
        raise VerificationError(f"{p.topic}/{p.subskill}: divide by zero quantity")
    expected = sp.Rational(total, quantity)
    if not _equal(expected, p.answer_expr):
        raise VerificationError(f"{p.topic}/{p.subskill}: unit rate should be {expected}")

def _v_unit_price_comparison(p: Problem) -> None:
    price_a, qty_a, price_b, qty_b = _nums(p.question_latex)
    if qty_a == 0 or qty_b == 0:
        raise VerificationError(f"{p.topic}/{p.subskill}: divide by zero quantity")
    rate_a, rate_b = sp.Rational(price_a, qty_a), sp.Rational(price_b, qty_b)
    if rate_a == rate_b:
        raise VerificationError(f"{p.topic}/{p.subskill}: tied unit prices, no unique better buy")
    expected = "A" if rate_a < rate_b else "B"
    if str(p.answer_expr).strip().upper().replace("OPTION ", "") != expected:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: better buy is Option {expected}, key says {p.answer_expr}"
        )
    # Check the PRINTED text specifically, not just answer_expr -- catches a
    # rendering bug even though today the two strings are identical.
    printed = str(p.answer_latex).strip().upper().replace("OPTION ", "")
    if printed != expected:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: better buy is Option {expected}, "
            f"printed key says {p.answer_latex!r}"
        )
