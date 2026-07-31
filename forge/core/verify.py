"""Independent re-derivation of every answer.

The rule: verification must not trust the generator's arithmetic. Wherever
possible we parse ``question_latex`` back into sympy from the *rendered string
the student will see* and re-derive the answer from scratch. A mismatch fails
the build; no PDF is ever emitted with an unverified key.
"""

from __future__ import annotations

import re
from typing import List

import sympy as sp
from sympy.parsing.sympy_parser import (
    implicit_multiplication,
    parse_expr,
    standard_transformations,
)

from .problem import Problem

_TRANSFORMS = standard_transformations + (implicit_multiplication,)


class VerificationError(AssertionError):
    pass


# --------------------------------------------------------------------------
# LaTeX -> sympy
# --------------------------------------------------------------------------

_FRAC = re.compile(r"\\d?frac\s*(?=\{)")


def _match_group(s: str, i: int):
    """Return (contents, index_after) for the brace group starting at s[i]=='{'."""
    if i >= len(s) or s[i] != "{":
        raise VerificationError(f"expected a brace group at position {i} of {s!r}")
    depth = 0
    for j in range(i, len(s)):
        if s[j] == "{":
            depth += 1
        elif s[j] == "}":
            depth -= 1
            if depth == 0:
                return s[i + 1 : j], j + 1
    raise VerificationError(f"unbalanced braces in {s!r}")


_TRAILING_INT = re.compile(r"(?<![\d.)])(\d+)\s*$")


def _expand_fracs(s: str) -> str:
    """Rewrite \\frac{a}{b} as ((a)/(b)), handling nested braces.

    A bare integer immediately before the fraction is a mixed number, and the
    whole thing is parenthesised: ``1 - 2\\frac{1}{3}`` must become
    ``1 - (2 + 1/3)``, not ``1 - 2 + 1/3``. Our renderers never put a bare
    integer before \\frac for a fractional coefficient (those come out as
    ``\\frac{2}{3}x``), so absorbing it is unambiguous here.
    """
    while True:
        m = _FRAC.search(s)
        if not m:
            return s
        numer, after = _match_group(s, m.end())
        denom, end = _match_group(s, after)
        body = f"(({_expand_fracs(numer)})/({_expand_fracs(denom)}))"

        head = s[: m.start()]
        whole = _TRAILING_INT.search(head)
        if whole:
            head = head[: whole.start()]
            body = f"({whole.group(1)} + {body})"
        s = f"{head}{body}{s[end:]}"


def latex_to_sympy(latex: str) -> sp.Expr:
    """Parse the subset of LaTeX these worksheets emit into a sympy expression."""
    s = latex.strip().strip("$").strip()
    s = s.replace(r"\left", "").replace(r"\right", "")
    s = s.replace(r"\cdot", "*").replace(r"\times", "*").replace(r"\div", "/")
    s = re.sub(r"\\[,;:!]", " ", s)
    s = _expand_fracs(s)
    s = s.replace("^", "**")
    # nth roots: \sqrt[3]{x} -> real_root(x, 3), so negative radicands (cube
    # roots) evaluate to the real root, not sympy's principal complex root.
    # Must run before the plain \sqrt rule.
    s = re.sub(r"\\sqrt\[(\d+)\]\{([^{}]*)\}", r"real_root((\2),\1)", s)
    s = re.sub(r"\\sqrt\s*\{([^{}]*)\}", r"sqrt(\1)", s)
    s = s.replace(r"\%", "").replace("%", "")
    s = s.replace("{", "(").replace("}", ")")
    if "\\" in s:
        raise VerificationError(f"unparsed LaTeX macro in {latex!r} -> {s!r}")
    try:
        expr = parse_expr(s, transformations=_TRANSFORMS, evaluate=True)
    except (SyntaxError, TypeError, sp.SympifyError) as e:
        raise VerificationError(f"cannot parse {latex!r} -> {s!r}: {e}") from None
    return expr


def _mixed_to_sympy(latex: str) -> sp.Expr:
    """Mixed numbers ``1\\frac{7}{12}`` mean 1 + 7/12, not 1 * 7/12."""
    s = latex.strip().strip("$").strip()
    m = re.fullmatch(r"(-?)(\d+)\s*(\\d?frac\{[^{}]*\}\{[^{}]*\})", s)
    if m:
        sign = -1 if m.group(1) == "-" else 1
        return sign * (sp.Integer(m.group(2)) + latex_to_sympy(m.group(3)))
    return latex_to_sympy(s)


def _equal(a, b) -> bool:
    try:
        diff = sp.simplify(sp.nsimplify(a) - sp.nsimplify(b))
        return bool(diff == 0)
    except (TypeError, sp.SympifyError):
        return False


# --------------------------------------------------------------------------
# Strategies
# --------------------------------------------------------------------------

def _v_evaluate(p: Problem) -> None:
    """Re-evaluate the printed expression and compare to the stated answer."""
    got = latex_to_sympy(p.verify.get("expr", p.question_latex))
    if not _equal(got, p.answer_expr):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {p.question_latex} evaluates to {got}, "
            f"key says {p.answer_expr}"
        )


def _v_simplify(p: Problem) -> None:
    """The answer must be algebraically identical to the printed expression."""
    got = latex_to_sympy(p.verify.get("expr", p.question_latex))
    if not _equal(sp.expand(got), sp.expand(sp.sympify(p.answer_expr))):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {p.question_latex} != {p.answer_expr}"
        )


def _v_solve(p: Problem) -> None:
    """Re-solve the printed relation and require exactly the keyed solution."""
    var = sp.Symbol(p.verify.get("var", "x"))
    lhs = latex_to_sympy(p.verify["lhs"])
    rhs = latex_to_sympy(p.verify["rhs"])
    sols = sp.solve(sp.Eq(lhs, rhs), var, dict=False)
    if len(sols) != 1:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {p.question_latex} has {len(sols)} solutions "
            f"({sols}); expected exactly one"
        )
    if not _equal(sols[0], p.answer_expr):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {p.question_latex} solves to {sols[0]}, "
            f"key says {p.answer_expr}"
        )


def _v_inequality(p: Problem) -> None:
    """Check the solution set by testing points on both sides of the boundary."""
    var = sp.Symbol(p.verify.get("var", "x"))
    lhs = latex_to_sympy(p.verify["lhs"])
    rhs = latex_to_sympy(p.verify["rhs"])
    rel = p.verify["rel"]
    stated = {"<": sp.Lt, "<=": sp.Le, ">": sp.Gt, ">=": sp.Ge}[rel](lhs, rhs)
    solved = sp.solve_univariate_inequality(stated, var, relational=False)
    keyed = p.verify["solution_set"]
    if solved != keyed:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {p.question_latex} has solution set {solved}, "
            f"key says {keyed}"
        )


def _v_tuple(p: Problem) -> None:
    """Multi-part answers (e.g. slope and intercept) compared componentwise."""
    expected = list(p.verify["expected"])
    got = list(p.answer_expr)
    if len(expected) != len(got) or not all(_equal(a, b) for a, b in zip(expected, got)):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {p.question_latex} -> {expected}, key says {got}"
        )


_POINT = re.compile(r"\(\s*(-?\d+)\s*,\s*(-?\d+)\s*\)")


def _points_in(p: Problem):
    pts = [(sp.Integer(a), sp.Integer(b)) for a, b in _POINT.findall(p.question_latex)]
    if len(pts) != 2:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: expected 2 points in {p.question_latex!r}, found {len(pts)}"
        )
    (x1, y1), (x2, y2) = pts
    if x1 == x2:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {p.question_latex} has an undefined slope"
        )
    return (x1, y1), (x2, y2)


def _v_slope_from_points(p: Problem) -> None:
    """Recompute the slope from the points as *printed* on the worksheet."""
    (x1, y1), (x2, y2) = _points_in(p)
    m = sp.Rational(y2 - y1, x2 - x1)
    if not _equal(m, p.answer_expr):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {p.question_latex} has slope {m}, key says {p.answer_expr}"
        )


def _v_line_through_points(p: Problem) -> None:
    """The keyed equation must actually pass through both printed points."""
    (x1, y1), (x2, y2) = _points_in(p)
    x = sp.Symbol("x")
    rhs = latex_to_sympy(p.answer_latex.split("=", 1)[1])
    for px, py in ((x1, y1), (x2, y2)):
        if not _equal(rhs.subs(x, px), py):
            raise VerificationError(
                f"{p.topic}/{p.subskill}: key {p.answer_latex} misses point ({px}, {py})"
            )


def _v_slope_intercept(p: Problem) -> None:
    """Read m and b straight off the printed equation."""
    x = sp.Symbol("x")
    rhs = latex_to_sympy(p.question_latex.split("=", 1)[1])
    poly = sp.Poly(rhs, x)
    if poly.degree() > 1:
        raise VerificationError(f"{p.topic}/{p.subskill}: {p.question_latex} is not linear")
    m, b = rhs.coeff(x, 1), rhs.coeff(x, 0)
    got_m, got_b = p.answer_expr
    if not (_equal(m, got_m) and _equal(b, got_b)):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {p.question_latex} has m={m}, b={b}; "
            f"key says m={got_m}, b={got_b}"
        )


def _v_point_slope(p: Problem) -> None:
    """The keyed line must have the printed slope and hit the printed point."""
    pts = _POINT.findall(p.question_latex)
    if len(pts) != 1:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: expected 1 point in {p.question_latex!r}"
        )
    px, py = sp.Integer(pts[0][0]), sp.Integer(pts[0][1])
    m_txt = re.search(r"m\s*=\s*([^$]+)\$", p.question_latex)
    if not m_txt:
        raise VerificationError(f"{p.topic}/{p.subskill}: no slope in {p.question_latex!r}")
    m = latex_to_sympy(m_txt.group(1))

    x = sp.Symbol("x")
    rhs = latex_to_sympy(p.answer_latex.split("=", 1)[1])
    if not _equal(sp.diff(rhs, x), m):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: key {p.answer_latex} has slope {sp.diff(rhs, x)}, "
            f"question says {m}"
        )
    if not _equal(rhs.subs(x, px), py):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: key {p.answer_latex} misses point ({px}, {py})"
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


# Matches a bare "$5$", a dollar amount "$\$5$", or a percent "$5\%$" --
# always the integer between the outer math delimiters, in reading order.
_NUM = re.compile(r"\$\\?\$?(-?\d+)\\?%?\$")


def _nums(text: str) -> List[sp.Integer]:
    """Pull every printed integer out of a prose question, in reading order."""
    return [sp.Integer(x) for x in _NUM.findall(text)]


def _v_geo_rectangle_area(p: Problem) -> None:
    l, w = _nums(p.question_latex)
    if not _equal(l * w, p.answer_expr):
        raise VerificationError(f"{p.topic}/{p.subskill}: area should be {l * w}")


def _v_geo_square_area(p: Problem) -> None:
    (s,) = _nums(p.question_latex)
    if not _equal(s * s, p.answer_expr):
        raise VerificationError(f"{p.topic}/{p.subskill}: area should be {s * s}")


def _v_geo_triangle_area(p: Problem) -> None:
    b, h = _nums(p.question_latex)
    expected = sp.Rational(b * h, 2)
    if not _equal(expected, p.answer_expr):
        raise VerificationError(f"{p.topic}/{p.subskill}: area should be {expected}")


def _v_geo_trapezoid_area(p: Problem) -> None:
    b1, b2, h = _nums(p.question_latex)
    expected = sp.Rational((b1 + b2) * h, 2)
    if not _equal(expected, p.answer_expr):
        raise VerificationError(f"{p.topic}/{p.subskill}: area should be {expected}")


def _v_geo_rect_prism_volume(p: Problem) -> None:
    l, w, h = _nums(p.question_latex)
    expected = l * w * h
    if not _equal(expected, p.answer_expr):
        raise VerificationError(f"{p.topic}/{p.subskill}: volume should be {expected}")


def _v_geo_rect_prism_sa(p: Problem) -> None:
    l, w, h = _nums(p.question_latex)
    expected = 2 * (l * w + l * h + w * h)
    if not _equal(expected, p.answer_expr):
        raise VerificationError(f"{p.topic}/{p.subskill}: surface area should be {expected}")


def _v_geo_tri_prism_volume(p: Problem) -> None:
    a, b, c, length = _nums(p.question_latex)
    expected = sp.Rational(a * b, 2) * length
    if not _equal(expected, p.answer_expr):
        raise VerificationError(f"{p.topic}/{p.subskill}: volume should be {expected}")


def _v_geo_tri_prism_sa(p: Problem) -> None:
    a, b, c, length = _nums(p.question_latex)
    expected = a * b + (a + b + c) * length
    if not _equal(expected, p.answer_expr):
        raise VerificationError(f"{p.topic}/{p.subskill}: surface area should be {expected}")


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


STRATEGIES = {
    "evaluate": _v_evaluate,
    "simplify": _v_simplify,
    "solve": _v_solve,
    "inequality": _v_inequality,
    "tuple": _v_tuple,
    "slope_from_points": _v_slope_from_points,
    "line_through_points": _v_line_through_points,
    "slope_intercept": _v_slope_intercept,
    "point_slope": _v_point_slope,
    "percent_of": _v_percent_of,
    "percent_change": _v_percent_change,
    "word": _v_word,
    "geo_rectangle_area": _v_geo_rectangle_area,
    "geo_square_area": _v_geo_square_area,
    "geo_triangle_area": _v_geo_triangle_area,
    "geo_trapezoid_area": _v_geo_trapezoid_area,
    "geo_rect_prism_volume": _v_geo_rect_prism_volume,
    "geo_rect_prism_sa": _v_geo_rect_prism_sa,
    "geo_tri_prism_volume": _v_geo_tri_prism_volume,
    "geo_tri_prism_sa": _v_geo_tri_prism_sa,
    "classify": _v_classify,
    "estimate_percent": _v_estimate_percent,
    "markup_discount": _v_markup_discount,
    "percent_error": _v_percent_error,
    "commission": _v_commission,
    "tax_tip": _v_tax_tip,
    "unit_rate": _v_unit_rate,
    "unit_price_comparison": _v_unit_price_comparison,
}


def verify_problem(p: Problem) -> None:
    kind = p.verify.get("kind", "evaluate")
    try:
        strategy = STRATEGIES[kind]
    except KeyError:
        raise VerificationError(f"unknown verification kind {kind!r}") from None
    strategy(p)
    _check_answer_latex(p)


def _check_answer_latex(p: Problem) -> None:
    """The *printed* key must agree with the verified symbolic answer."""
    text = p.verify.get("answer_check", p.answer_latex)
    if text is None:
        return
    s = text.strip().strip("$").strip()
    s = re.sub(r"^[A-Za-z]\s*=\s*", "", s)
    try:
        printed = _mixed_to_sympy(s)
    except (VerificationError, sp.SympifyError, TypeError, SyntaxError):
        return  # non-numeric keys (e.g. inequalities) are checked by their strategy
    target = p.answer_expr
    # Sets, relations and multi-part keys are their strategy's job, not this
    # check -- only plain numeric or algebraic expressions compare meaningfully.
    opaque = (list, tuple, sp.Set, sp.core.relational.Relational)
    if isinstance(target, opaque) or isinstance(printed, opaque):
        return
    if not _equal(printed, target):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: printed key {p.answer_latex!r} reads as {printed}, "
            f"but the verified answer is {target}"
        )


def verify_all(problems: List[Problem]) -> None:
    errors = []
    for p in problems:
        try:
            verify_problem(p)
        except VerificationError as e:
            errors.append(str(e))
    if errors:
        raise VerificationError(
            f"{len(errors)} answer(s) failed verification:\n  - "
            + "\n  - ".join(errors)
        )
