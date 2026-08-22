"""Verification strategies for symbolic work: equations, inequalities,
expressions, lines, systems, quadratics, radicals, logs and sequences.
"""

from __future__ import annotations

import re

import sympy as sp

from ..problem import Problem

from .parsing import (
    _expand_fracs,
    VerificationError,
    _FRAC,
    _POINT,
    _REL_CLASS,
    _REL_OP,
    _REL_TOKEN,
    _equal,
    _match_group,
    _nums,
    _split_relation,
    latex_relation_to_sympy,
    latex_to_sympy,
)


def _v_evaluate(p: Problem) -> None:
    """Re-evaluate the printed expression and compare to the stated answer."""
    got = latex_to_sympy(p.verify.get("expr", p.question_latex))
    if not _equal(got, p.answer_expr):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {p.question_latex} evaluates to {got}, "
            f"key says {p.answer_expr}"
        )

_FACTORING_SUBSKILLS = {
    "factor_trinomial",
    "factor_by_grouping",
    "difference_of_squares",
    "factor_trinomial_lead",
    "factor_difference_of_squares_lead",
}


def _v_simplify(p: Problem) -> None:
    """The answer must be algebraically identical to the printed expression."""
    got = latex_to_sympy(p.verify.get("expr", p.question_latex))
    if not _equal(sp.expand(got), sp.expand(sp.sympify(p.answer_expr))):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {p.question_latex} != {p.answer_expr}"
        )
    if p.subskill in _FACTORING_SUBSKILLS:
        _check_fully_factored(p)


def _check_fully_factored(p: Problem) -> None:
    """The printed key must be sympy's fully-factored form, not just a
    product that multiplies back to the question -- each individual factor
    must be primitive (content 1), so a common factor like ``2`` can't be
    left sitting inside two linear factors, e.g. ``4x^2-36 -> (2x-6)(2x+6)``
    (each factor has content 2) or ``9x^2-81 -> (3x-9)(3x+9)`` (content 3).
    """
    x = sp.Symbol("x")
    printed = latex_to_sympy(p.answer_latex)
    for factor in sp.Mul.make_args(sp.sympify(printed)):
        if factor.free_symbols:
            poly_ = sp.Poly(factor, x)
            content = poly_.content()
            if content != 1:
                raise VerificationError(
                    f"{p.topic}/{p.subskill}: printed key {p.answer_latex!r} is not "
                    f"fully factored -- factor {factor} has content {content}"
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

def _v_abs_solve(p: Problem) -> None:
    """Re-solve the printed |...| = c equation; require exactly the keyed roots."""
    # sympy's Abs-equation solver refuses a symbol with no real/imaginary
    # assumption ("argument is not real or imaginary") -- these are always
    # real-valued algebra problems, so declare it.
    name = p.verify.get("var", "x")
    var = sp.Symbol(name, real=True)
    # latex_to_sympy parses with a plain (no-assumptions) symbol of the same
    # name; swap it for the real one so sp.solve sees `var` as the unknown.
    lhs = latex_to_sympy(p.verify["lhs"]).subs(sp.Symbol(name), var)
    rhs = latex_to_sympy(p.verify["rhs"])
    sols = sorted(sp.solve(sp.Eq(lhs, rhs), var), key=lambda s: sp.N(s))
    expected = list(p.answer_expr)
    if len(sols) != len(expected) or not all(_equal(a, b) for a, b in zip(sols, expected)):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {p.question_latex} solves to {sols}, "
            f"key says {expected}"
        )
    # The PRINTED key (``x = s1 \text{ or } x = s2``) must state the same
    # roots -- answer_expr alone doesn't catch a rendering bug in the text.
    printed = [sp.Integer(v) for v in re.findall(r"x\s*=\s*(-?\d+)", p.answer_latex)]
    printed.sort(key=lambda s: sp.N(s))
    if len(printed) != len(sols) or not all(_equal(a, b) for a, b in zip(sols, printed)):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: printed key {p.answer_latex!r} states roots "
            f"{printed}, but {p.question_latex} solves to {sols}"
        )

def _v_inequality(p: Problem) -> None:
    """Re-derive the solution set from the PRINTED question and the PRINTED
    key independently -- neither comes from ``p.verify``, which is only used
    as a secondary cross-check. This is what catches a wrong direction or
    boundary in the printed answer, not just a self-consistent tautology.
    """
    var = sp.Symbol(p.verify.get("var", "x"))

    # 1. Re-derive lhs/rhs/rel from the printed question itself.
    q_lhs_text, q_op, q_rhs_text = _split_relation(p.question_latex.strip().strip("$"))
    q_lhs = latex_to_sympy(q_lhs_text)
    q_rhs = latex_to_sympy(q_rhs_text)

    # 2. The generator's stored lhs/rhs/rel must agree with what's printed.
    stored_lhs = latex_to_sympy(p.verify["lhs"])
    stored_rhs = latex_to_sympy(p.verify["rhs"])
    if not (_equal(stored_lhs, q_lhs) and _equal(stored_rhs, q_rhs) and q_op == p.verify["rel"]):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: printed question {p.question_latex!r} reads as "
            f"{q_lhs} {q_op} {q_rhs}, but verify[lhs/rhs/rel] says "
            f"{p.verify['lhs']} {p.verify['rel']} {p.verify['rhs']}"
        )

    stated = _REL_CLASS[q_op](q_lhs, q_rhs)
    solved = sp.solve_univariate_inequality(stated, var, relational=False)

    # 3. Parse the PRINTED answer key on its own and require the same set.
    printed_rel = latex_relation_to_sympy(p.answer_latex)
    printed_solved = sp.solve_univariate_inequality(printed_rel, var, relational=False)
    if printed_solved != solved:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {p.question_latex} has solution set {solved}, "
            f"but printed key {p.answer_latex!r} reads as {printed_solved}"
        )

    # 4. Secondary cross-check against what the generator stored -- not the
    # sole authority, just a sanity check that it agrees.
    keyed = p.verify.get("solution_set")
    if keyed is not None and solved != keyed:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {p.question_latex} has solution set {solved}, "
            f"but verify['solution_set'] says {keyed}"
        )

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
    if "=" not in p.answer_latex:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: key {p.answer_latex!r} has no '=' to parse"
        )
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
    got_m, got_b, got_x0 = p.answer_expr
    if not (_equal(m, got_m) and _equal(b, got_b)):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {p.question_latex} has m={m}, b={b}; "
            f"key says m={got_m}, b={got_b}"
        )
    x0 = -b / m
    if not _equal(x0, got_x0):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {p.question_latex} has x-intercept {x0}; "
            f"key says {got_x0}"
        )
    _v_check_printed_m_b(p, m, b)
    _v_check_printed_x_intercept(p, x0)

def _v_check_printed_x_intercept(p: Problem, x0) -> None:
    """The PRINTED ``x\\text{-intercept} = (val, 0)`` key must match the
    re-derived x-intercept -- ``answer_expr`` alone doesn't catch a rendering
    bug in the printed text."""
    m = re.search(r"x\\text\{-intercept\}\s*=\s*\((-?[\d./]+),\s*0\)", p.answer_latex)
    if not m:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: cannot read x-intercept from {p.answer_latex!r}"
        )
    printed_x0 = latex_to_sympy(m.group(1))
    if not _equal(printed_x0, x0):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: printed key {p.answer_latex!r} states x-intercept "
            f"{printed_x0}; re-derived is {x0}"
        )

def _v_check_printed_m_b(p: Problem, m, b) -> None:
    """The PRINTED ``m = ..., \\quad b = ...`` key must match the re-derived
    ``m``/``b`` -- ``answer_expr`` alone doesn't catch a rendering bug."""
    m_txt = re.search(r"m\s*=\s*([^$,]+)", p.answer_latex)
    b_txt = re.search(r"b\s*=\s*([^$]+)", p.answer_latex)
    if not m_txt or not b_txt:
        raise VerificationError(f"{p.topic}/{p.subskill}: cannot read m/b from {p.answer_latex!r}")
    printed_m = latex_to_sympy(m_txt.group(1))
    printed_b = latex_to_sympy(b_txt.group(1))
    if not (_equal(printed_m, m) and _equal(printed_b, b)):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: printed key {p.answer_latex!r} reads m={printed_m}, "
            f"b={printed_b}; re-derived m={m}, b={b}"
        )

def _v_slope_and_line(p: Problem) -> None:
    """Recompute slope from the printed points; check both stated m and line."""
    (x1, y1), (x2, y2) = _points_in(p)
    m = sp.Rational(y2 - y1, x2 - x1)

    m_txt = re.search(r"m\s*=\s*([^$,]+)", p.answer_latex)
    if not m_txt:
        raise VerificationError(f"{p.topic}/{p.subskill}: no slope in {p.answer_latex!r}")
    stated_m = latex_to_sympy(m_txt.group(1))
    if not _equal(stated_m, m):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {p.question_latex} has slope {m}, key states {stated_m}"
        )

    line_txt = re.search(r"y\s*=\s*([^$]+)\$", p.answer_latex)
    if not line_txt:
        raise VerificationError(f"{p.topic}/{p.subskill}: no line in {p.answer_latex!r}")
    x = sp.Symbol("x")
    rhs = latex_to_sympy(line_txt.group(1))
    for px, py in ((x1, y1), (x2, y2)):
        if not _equal(rhs.subs(x, px), py):
            raise VerificationError(
                f"{p.topic}/{p.subskill}: key {p.answer_latex} misses point ({px}, {py})"
            )

def _v_slope_intercept_standard(p: Problem) -> None:
    """Solve the printed standard-form equation for y independently."""
    text = p.question_latex.strip().strip("$")
    lhs_text, rhs_text = text.split("=", 1)
    lhs = latex_to_sympy(lhs_text)
    rhs = latex_to_sympy(rhs_text)
    x, y = sp.Symbol("x"), sp.Symbol("y")
    sols = sp.solve(sp.Eq(lhs, rhs), y)
    if len(sols) != 1:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {p.question_latex} has {len(sols)} solutions for y"
        )
    sol = sols[0]
    poly = sp.Poly(sol, x)
    if poly.degree() > 1:
        raise VerificationError(f"{p.topic}/{p.subskill}: {p.question_latex} is not linear in x")
    m, b = sol.coeff(x, 1), sol.coeff(x, 0)
    got_m, got_b, got_x0 = p.answer_expr
    if not (_equal(m, got_m) and _equal(b, got_b)):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {p.question_latex} has m={m}, b={b}; "
            f"key says m={got_m}, b={got_b}"
        )
    x0 = -b / m
    if not _equal(x0, got_x0):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {p.question_latex} has x-intercept {x0}; "
            f"key says {got_x0}"
        )
    _v_check_printed_m_b(p, m, b)
    _v_check_printed_x_intercept(p, x0)

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
    if "=" not in p.answer_latex:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: key {p.answer_latex!r} has no '=' to parse"
        )
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

def _three_part_solution(text: str, var: sp.Symbol):
    """Solve ``a REL expr REL c`` by intersecting its two halves.

    ``solve_univariate_inequality`` takes one relation at a time, so a
    conjunction is solved as two sets and intersected -- which is also
    literally what the compound inequality means.
    """
    s = text.strip().strip("$").strip()
    ops = list(_REL_TOKEN.finditer(s))
    if len(ops) != 2:
        raise VerificationError(
            f"expected a three-part inequality, found {len(ops)} relations in {text!r}"
        )
    left = s[: ops[0].start()]
    middle = s[ops[0].end(): ops[1].start()]
    right = s[ops[1].end():]
    l_expr, m_expr, r_expr = (latex_to_sympy(t) for t in (left, middle, right))
    op1, op2 = (_REL_OP[o.group(0)] for o in ops)
    first = sp.solve_univariate_inequality(
        _REL_CLASS[op1](l_expr, m_expr), var, relational=False
    )
    second = sp.solve_univariate_inequality(
        _REL_CLASS[op2](m_expr, r_expr), var, relational=False
    )
    return first.intersect(second)

def _v_compound_inequality(p: Problem) -> None:
    var = sp.Symbol("x")
    solved = _three_part_solution(p.question_latex, var)
    if solved != p.answer_expr:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {p.question_latex} solves to {solved}, "
            f"key says {p.answer_expr}"
        )
    # The printed key is its own three-part inequality; solving it must give
    # the same set, or the rendering flipped a bound the answer_expr did not.
    printed = _three_part_solution(p.answer_latex, var)
    if printed != solved:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: printed key {p.answer_latex!r} reads as "
            f"{printed}, but the solution set is {solved}"
        )

_COMPOUND = re.compile(r"(-?\d+)\s*(<=|\\le|<)\s*x\s*(<=|\\le|<)\s*(-?\d+)")

def _v_abs_inequality(p: Problem) -> None:
    """Re-derive the printed |...| inequality's solution set with sympy;
    require the printed compound/union key to describe the same set."""
    name = p.verify.get("var", "x")
    var = sp.Symbol(name, real=True)
    plain = sp.Symbol(name)

    text = p.question_latex.strip().strip("$")
    lhs_text, op, rhs_text = _split_relation(text)
    lhs = latex_to_sympy(lhs_text).subs(plain, var)
    rhs = latex_to_sympy(rhs_text)
    solved = sp.solve_univariate_inequality(_REL_CLASS[op](lhs, rhs), var, relational=False)

    answer_text = p.answer_latex.strip().strip("$")
    if r"\text{ or }" in answer_text:
        rels = []
        for part in answer_text.split(r"\text{ or }"):
            plhs, pop, prhs = _split_relation(part.strip())
            rels.append(_REL_CLASS[pop](latex_to_sympy(plhs).subs(plain, var), latex_to_sympy(prhs)))
        if len(rels) != 2:
            raise VerificationError(f"{p.topic}/{p.subskill}: cannot read key {p.answer_latex!r}")
        # solve_univariate_inequality only accepts a single relation, not an
        # Or() of two -- solve each piece separately and union the results.
        printed_solved = sp.Union(
            *(sp.solve_univariate_inequality(r, var, relational=False) for r in rels)
        )
    else:
        m = _COMPOUND.match(answer_text)
        if not m:
            raise VerificationError(f"{p.topic}/{p.subskill}: cannot read key {p.answer_latex!r}")
        lo, op1, op2, hi_v = m.group(1), m.group(2), m.group(3), m.group(4)
        printed_solved = sp.Interval(
            sp.Integer(lo), sp.Integer(hi_v), left_open=(op1 == "<"), right_open=(op2 == "<")
        )

    if printed_solved != solved:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {p.question_latex} has solution set {solved}, "
            f"but printed key {p.answer_latex!r} reads as {printed_solved}"
        )

def _v_point_in_inequality(p: Problem) -> None:
    """Independently evaluate whether the printed point satisfies the
    printed inequality; require the printed Yes/No key to agree."""
    text = p.question_latex
    ineq_part = text.split(";", 1)[0].strip().strip("$")
    _lhs_text, op, rhs_text = _split_relation(ineq_part)
    x = sp.Symbol("x")
    rhs = latex_to_sympy(rhs_text)
    pts = _POINT.findall(text)
    if len(pts) != 1:
        raise VerificationError(f"{p.topic}/{p.subskill}: expected 1 point in {text!r}")
    px, py = sp.Integer(pts[0][0]), sp.Integer(pts[0][1])
    is_sol = bool(_REL_CLASS[op](py, rhs.subs(x, px)))

    answer_text = p.answer_latex.strip().strip("$")
    expected = "Yes" if is_sol else "No"
    if answer_text != expected:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: point ({px}, {py}) {'is' if is_sol else 'is not'} "
            f"a solution of {ineq_part}, but key says {answer_text!r}"
        )

def _v_system_point_in_inequality(p: Problem) -> None:
    """Same as :func:`_v_point_in_inequality`, but the point must satisfy
    both printed inequalities in a ``\\begin{cases}`` block."""
    text = p.question_latex
    ineq_part = text.split(";", 1)[0]
    m = _CASES.search(ineq_part)
    if not m:
        raise VerificationError(f"{p.topic}/{p.subskill}: no cases block in {ineq_part!r}")
    parts = [e.strip() for e in m.group(1).split(r"\\") if e.strip()]
    if len(parts) != 2:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: expected 2 inequalities in {ineq_part!r}"
        )
    x = sp.Symbol("x")
    pts = _POINT.findall(text)
    if len(pts) != 1:
        raise VerificationError(f"{p.topic}/{p.subskill}: expected 1 point in {text!r}")
    px, py = sp.Integer(pts[0][0]), sp.Integer(pts[0][1])

    results = []
    for part in parts:
        _lhs_text, op, rhs_text = _split_relation(part)
        boundary = latex_to_sympy(rhs_text).subs(x, px)
        results.append(bool(_REL_CLASS[op](py, boundary)))
    is_sol = all(results)

    answer_text = p.answer_latex.strip().strip("$")
    expected = "Yes" if is_sol else "No"
    if answer_text != expected:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: point ({px}, {py}) {'is' if is_sol else 'is not'} "
            f"a solution of the system, but key says {answer_text!r}"
        )

_CASES = re.compile(r"\\begin\{cases\}(.*?)\\end\{cases\}", re.S)

def _parse_system(question_latex: str):
    """Pull the two equations out of a printed ``\\begin{cases}...\\end{cases}``
    block and return them as sympy ``Eq`` objects -- re-derived from the
    printed text, never from anything the generator stored."""
    m = _CASES.search(question_latex)
    if not m:
        raise VerificationError(f"no cases block found in {question_latex!r}")
    parts = [e.strip() for e in m.group(1).split(r"\\") if e.strip()]
    if len(parts) != 2:
        raise VerificationError(
            f"expected 2 equations in {question_latex!r}, found {len(parts)}"
        )
    eqs = []
    for part in parts:
        if "=" not in part:
            raise VerificationError(f"no '=' in system equation {part!r}")
        lhs_t, rhs_t = part.split("=", 1)
        eqs.append(sp.Eq(latex_to_sympy(lhs_t), latex_to_sympy(rhs_t)))
    return eqs

def _v_solve_system(p: Problem) -> None:
    """Re-solve the printed system with ``linsolve`` and require the keyed point."""
    x, y = sp.symbols("x y")
    eqs = _parse_system(p.question_latex)
    sol = sp.linsolve(eqs, x, y)
    if len(sol) != 1:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {p.question_latex} has {len(sol)} solution(s), expected 1"
        )
    (xv, yv), = sol
    if xv.free_symbols or yv.free_symbols:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {p.question_latex} is a dependent system, "
            "not a unique solution"
        )
    exp_x, exp_y = p.answer_expr
    if not (_equal(xv, exp_x) and _equal(yv, exp_y)):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {p.question_latex} solves to ({xv}, {yv}), "
            f"key says ({exp_x}, {exp_y})"
        )
    xm = re.search(r"x\s*=\s*([^,\$]+)", p.answer_latex)
    ym = re.search(r"y\s*=\s*([^\$]+)", p.answer_latex)
    if not xm or not ym:
        raise VerificationError(f"{p.topic}/{p.subskill}: cannot read x/y from {p.answer_latex!r}")
    printed_x = latex_to_sympy(xm.group(1))
    printed_y = latex_to_sympy(ym.group(1))
    if not (_equal(printed_x, xv) and _equal(printed_y, yv)):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: printed key {p.answer_latex!r} states "
            f"({printed_x}, {printed_y}), re-derived is ({xv}, {yv})"
        )

def _v_classify_system(p: Problem) -> None:
    """Re-classify the printed system with ``linsolve``; require the printed
    key to name the same case (and, for a unique solution, the same point)."""
    x, y = sp.symbols("x y")
    eqs = _parse_system(p.question_latex)
    sol = sp.linsolve(eqs, x, y)
    text = p.answer_latex

    if len(sol) == 0:
        if "No solution" not in text:
            raise VerificationError(
                f"{p.topic}/{p.subskill}: {p.question_latex} has no solution, "
                f"but key says {text!r}"
            )
        return
    (xv, yv), = sol
    if xv.free_symbols or yv.free_symbols:
        if "Infinitely" not in text:
            raise VerificationError(
                f"{p.topic}/{p.subskill}: {p.question_latex} has infinitely many "
                f"solutions, but key says {text!r}"
            )
        return
    if "One solution" not in text:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {p.question_latex} has exactly one solution "
            f"({xv}, {yv}), but key says {text!r}"
        )
    pts = _POINT.findall(text)
    if len(pts) != 1:
        raise VerificationError(f"{p.topic}/{p.subskill}: cannot read point from {text!r}")
    px, py = sp.Integer(pts[0][0]), sp.Integer(pts[0][1])
    if not (_equal(px, xv) and _equal(py, yv)):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: key states point ({px}, {py}), re-derived is ({xv}, {yv})"
        )

def _v_solve_quadratic(p: Problem) -> None:
    """Re-solve the printed ``... = 0`` and require exactly the keyed roots."""
    text = p.question_latex.strip().strip("$")
    if "=" not in text:
        raise VerificationError(f"{p.topic}/{p.subskill}: no '=' in {p.question_latex!r}")
    lhs_t, rhs_t = text.split("=", 1)
    var = sp.Symbol(p.verify.get("var", "x"))
    sols = sorted(
        sp.solve(sp.Eq(latex_to_sympy(lhs_t), latex_to_sympy(rhs_t)), var),
        key=lambda s: sp.N(s),
    )
    if len(sols) != 2:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {p.question_latex} has {len(sols)} solution(s), expected 2"
        )
    expected = sorted(p.answer_expr, key=lambda s: sp.N(s))
    if not all(_equal(a, b) for a, b in zip(sols, expected)):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {p.question_latex} solves to {sols}, key says {expected}"
        )
    parts = p.answer_latex.strip().strip("$").split(r"\text{ or }")
    if len(parts) != 2:
        raise VerificationError(f"{p.topic}/{p.subskill}: cannot split key {p.answer_latex!r}")
    printed = []
    for part in parts:
        mm = re.search(r"x\s*=\s*(.+)", part.strip())
        if not mm:
            raise VerificationError(f"{p.topic}/{p.subskill}: cannot read root from {part!r}")
        printed.append(latex_to_sympy(mm.group(1)))
    printed.sort(key=lambda s: sp.N(s))
    if not all(_equal(a, b) for a, b in zip(sols, printed)):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: printed key {p.answer_latex!r} states {printed}, "
            f"re-derived {sols}"
        )

def _v_quadratic_vertex(p: Problem) -> None:
    """Recompute the vertex from the printed standard-form equation."""
    text = p.question_latex.strip().strip("$")
    if "=" not in text:
        raise VerificationError(f"{p.topic}/{p.subskill}: no '=' in {p.question_latex!r}")
    x = sp.Symbol("x")
    rhs = latex_to_sympy(text.split("=", 1)[1])
    poly_ = sp.Poly(rhs, x)
    if poly_.degree() != 2:
        raise VerificationError(f"{p.topic}/{p.subskill}: {p.question_latex} is not quadratic")
    a, b, _c = poly_.all_coeffs()
    h = -b / (2 * a)
    k = rhs.subs(x, h)
    pts = _POINT.findall(p.answer_latex)
    if len(pts) != 1:
        raise VerificationError(f"{p.topic}/{p.subskill}: cannot read vertex from {p.answer_latex!r}")
    ph, pk = sp.Integer(pts[0][0]), sp.Integer(pts[0][1])
    if not (_equal(ph, h) and _equal(pk, k)):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: vertex should be ({h}, {k}), key says ({ph}, {pk})"
        )

def _rational_equal(a, b) -> bool:
    """Equality for expressions that may be rational functions of x -- plain
    ``_equal`` runs ``nsimplify``, which targets numeric values, not
    expressions with a free variable."""
    try:
        return sp.simplify(sp.cancel(a - b)) == 0
    except (TypeError, sp.SympifyError):
        return False

def _extract_fracs(text: str) -> list:
    """Find every ``\\frac{...}{...}``/``\\dfrac{...}{...}`` in text, using the
    balanced-brace matcher (not a flat regex) so a squared term's ``x^{2}``
    inside the numerator doesn't truncate the match."""
    out = []
    for m in _FRAC.finditer(text):
        numer, after = _match_group(text, m.end())
        denom, _end = _match_group(text, after)
        out.append((numer, denom))
    return out

def _v_simplify_rational(p: Problem) -> None:
    """Cancel the printed fraction independently; require the same reduced
    polynomial and the same excluded value(s) in the printed domain note."""
    text = p.question_latex.strip().strip("$")
    fracs = _extract_fracs(text)
    if not fracs:
        raise VerificationError(f"{p.topic}/{p.subskill}: no fraction in {p.question_latex!r}")
    x = sp.Symbol("x")
    numer = latex_to_sympy(fracs[0][0])
    denom = latex_to_sympy(fracs[0][1])
    simplified = sp.cancel(numer / denom)
    if sp.denom(simplified) != 1:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {p.question_latex} does not reduce to a "
            f"polynomial ({simplified})"
        )
    ans_text = p.answer_latex.strip().strip("$")
    ans_expr_text, _, domain_text = ans_text.partition(",")
    printed = latex_to_sympy(ans_expr_text)
    if not _rational_equal(printed, simplified):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {p.question_latex} simplifies to {simplified}, "
            f"key says {printed}"
        )
    roots = sp.solve(sp.Eq(denom, 0), x)
    printed_excl = {sp.Integer(v) for v in re.findall(r"x\s*\\neq\s*(-?\d+)", domain_text)}
    if set(roots) != printed_excl:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: denominator is zero at {roots}, key excludes {printed_excl}"
        )

def _v_multiply_rational(p: Problem) -> None:
    """Multiply and cancel the two printed fractions independently."""
    text = p.question_latex.strip().strip("$")
    fracs = _extract_fracs(text)
    if len(fracs) != 2:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: expected 2 fractions in {p.question_latex!r}"
        )
    (n1, d1), (n2, d2) = fracs
    numer = latex_to_sympy(n1) * latex_to_sympy(n2)
    denom = latex_to_sympy(d1) * latex_to_sympy(d2)
    simplified = sp.cancel(numer / denom)

    ans_text = p.answer_latex.strip().strip("$")
    printed = latex_to_sympy(ans_text)
    if not _rational_equal(printed, simplified):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {p.question_latex} simplifies to {simplified}, "
            f"key says {printed}"
        )

def _complex_from_text(s: str) -> sp.Expr:
    """Parse an "a + bi" / "a - bi" / "bi" / "a" fragment into a sympy
    expression over ``I`` -- these generators only ever emit that shape, so a
    literal ``i -> I`` swap (with a ``*`` inserted after a digit) is safe."""
    s = s.strip().strip("$").replace("i", "I")
    s = re.sub(r"(\d)I", r"\1*I", s)
    return latex_to_sympy(s)

def _v_complex_arith(p: Problem) -> None:
    """Re-parse the two printed complex numbers and the operator; recompute
    independently and require the same printed result."""
    text = p.question_latex.strip().strip("$")
    m = re.match(r"\((.+?)\)\s*([+\-])\s*\((.+?)\)$", text)
    if m:
        a = _complex_from_text(m.group(1))
        c = _complex_from_text(m.group(3))
        got = a + c if m.group(2) == "+" else a - c
    else:
        m = re.match(r"\((.+?)\)\((.+?)\)$", text)
        if not m:
            raise VerificationError(f"{p.topic}/{p.subskill}: cannot parse {p.question_latex!r}")
        a = _complex_from_text(m.group(1))
        c = _complex_from_text(m.group(2))
        got = sp.expand(a * c)

    printed = _complex_from_text(p.answer_latex)
    if sp.simplify(got - printed) != 0:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {p.question_latex} = {got}, key says {printed}"
        )

def _v_power_of_i(p: Problem) -> None:
    m = re.search(r"i\^\{(\d+)\}", p.question_latex)
    if not m:
        raise VerificationError(f"{p.topic}/{p.subskill}: cannot read exponent from {p.question_latex!r}")
    n = int(m.group(1))
    expected = (sp.Integer(1), sp.I, sp.Integer(-1), -sp.I)[n % 4]
    printed = _complex_from_text(p.answer_latex)
    if sp.simplify(printed - expected) != 0:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: i^{n} = {expected}, key says {printed}"
        )

def _v_solve_exponential(p: Problem) -> None:
    """Re-solve the printed a^x = c independently."""
    text = p.question_latex.strip().strip("$")
    m = re.match(r"(\d+)\^x\s*=\s*(.+)", text)
    if not m:
        raise VerificationError(f"{p.topic}/{p.subskill}: cannot parse {p.question_latex!r}")
    a = sp.Integer(m.group(1))
    c = latex_to_sympy(m.group(2))
    var = sp.Symbol("x", real=True)
    # Without real=True, solve() also returns complex branch solutions
    # whenever `a` is a perfect power of another integer (e.g. 8 = 2^3),
    # since a^x = c is then satisfied by x plus multiples of a complex period.
    sols = sp.solve(sp.Eq(a ** var, c), var)
    if len(sols) != 1:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {p.question_latex} has {len(sols)} solution(s)"
        )
    xm = re.search(r"x\s*=\s*(.+)", p.answer_latex.strip().strip("$"))
    if not xm:
        raise VerificationError(f"{p.topic}/{p.subskill}: cannot read key {p.answer_latex!r}")
    printed = latex_to_sympy(xm.group(1))
    if not _equal(sols[0], printed):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {p.question_latex} solves to {sols[0]}, key says {printed}"
        )

def _v_solve_logarithmic(p: Problem) -> None:
    """Re-derive x = b**c from the printed log_b(x) = c and require the same key."""
    text = p.question_latex.strip().strip("$")
    m = re.match(r"\\log_\{(\d+)\}\(x\)\s*=\s*(-?\d+)", text)
    if not m:
        raise VerificationError(f"{p.topic}/{p.subskill}: cannot parse {p.question_latex!r}")
    b, c = sp.Integer(m.group(1)), sp.Integer(m.group(2))
    expected = b ** c
    xm = re.search(r"x\s*=\s*(.+)", p.answer_latex.strip().strip("$"))
    if not xm:
        raise VerificationError(f"{p.topic}/{p.subskill}: cannot read key {p.answer_latex!r}")
    printed = latex_to_sympy(xm.group(1))
    if not _equal(expected, printed):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: log_{{{b}}}(x)={c} solves to x={expected}, key says {printed}"
        )

_LOG = re.compile(r"\\log_\{(\d+)\}\(([^()]*)\)")

def _v_condense_log(p: Problem) -> None:
    """Independently recompute the log-product identity numerically/symbolically."""
    text = p.question_latex.strip().strip("$")
    found = _LOG.findall(text)
    if len(found) != 2:
        raise VerificationError(f"{p.topic}/{p.subskill}: expected 2 logs in {p.question_latex!r}")
    (b1, x1), (b2, x2) = found
    if b1 != b2:
        raise VerificationError(f"{p.topic}/{p.subskill}: mismatched bases {b1} vs {b2}")
    lhs_val = sp.log(sp.Integer(x1), sp.Integer(b1)) + sp.log(sp.Integer(x2), sp.Integer(b1))

    am = _LOG.match(p.answer_latex.strip().strip("$"))
    if not am:
        raise VerificationError(f"{p.topic}/{p.subskill}: cannot read key {p.answer_latex!r}")
    rhs_val = sp.log(sp.Integer(am.group(2)), sp.Integer(am.group(1)))

    if sp.simplify(lhs_val - rhs_val) != 0:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {p.question_latex} = {sp.N(lhs_val)}, "
            f"key {p.answer_latex!r} = {sp.N(rhs_val)}"
        )

def _v_arithmetic_nth_term(p: Problem) -> None:
    a1, d, n = _nums(p.question_latex)
    expected = a1 + (n - 1) * d
    if not _equal(expected, p.answer_expr):
        raise VerificationError(f"{p.topic}/{p.subskill}: term should be {expected}")

def _v_geometric_nth_term(p: Problem) -> None:
    a1, r, n = _nums(p.question_latex)
    expected = a1 * r ** (n - 1)
    if not _equal(expected, p.answer_expr):
        raise VerificationError(f"{p.topic}/{p.subskill}: term should be {expected}")

def _v_arithmetic_series_sum(p: Problem) -> None:
    a1, d, n = _nums(p.question_latex)
    expected = sp.Rational(n, 2) * (2 * a1 + (n - 1) * d)
    if not _equal(expected, p.answer_expr):
        raise VerificationError(f"{p.topic}/{p.subskill}: sum should be {expected}")


def _v_inverse_function(p: Problem) -> None:
    """Compose the printed inverse with the printed function; require x.

    This is the definition, re-derived: whatever the generator computed, the
    printed key is only correct if f(f^-1(x)) simplifies to x.
    """
    x = sp.Symbol("x")
    m = re.search(r"f\(x\)\s*=\s*([^$]+)", p.question_latex.strip().strip("$"))
    if m is None:
        raise VerificationError(f"{p.topic}/{p.subskill}: no f(x) = ... in question")
    f_expr = latex_to_sympy(m.group(1))

    key = p.answer_latex.strip().strip("$")
    inv = re.search(r"f\^\{-1\}\(x\)\s*=\s*(.+)$", key)
    if inv is None:
        raise VerificationError(f"{p.topic}/{p.subskill}: no f^-1(x) = ... in key")
    inv_expr = latex_to_sympy(inv.group(1))

    if not _equal(inv_expr, p.answer_expr):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: printed inverse {inv_expr} does not match "
            f"the verified answer {p.answer_expr}"
        )
    composed = sp.simplify(f_expr.subs(x, inv_expr))
    if sp.simplify(composed - x) != 0:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: f(f^-1(x)) = {composed}, not x"
        )


def _v_composition(p: Problem) -> None:
    """Re-read f and g off the question and compose them independently."""
    x = sp.Symbol("x")
    text = p.question_latex.strip().strip("$")
    f_m = re.search(r"f\(x\)\s*=\s*([^,]+),", text)
    g_m = re.search(r"g\(x\)\s*=\s*([^,]+),", text)
    if not (f_m and g_m):
        raise VerificationError(f"{p.topic}/{p.subskill}: cannot read f and g")
    f_expr = latex_to_sympy(f_m.group(1))
    g_expr = latex_to_sympy(g_m.group(1))
    expected = sp.expand(f_expr.subs(x, g_expr))
    if not _equal(expected, p.answer_expr):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: f(g(x)) = {expected}, key says {p.answer_expr}"
        )
    printed = latex_to_sympy(re.sub(r"^g\(x\)\s*=\s*", "", p.answer_latex.strip().strip("$")))
    if not _equal(printed, expected):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: printed key {printed} != {expected}"
        )


def _v_transformation(p: Problem) -> None:
    """The printed equation must expand to the verified transformed function."""
    key = re.sub(r"^g\(x\)\s*=\s*", "", p.answer_latex.strip().strip("$"))
    printed = latex_to_sympy(key)
    if not _equal(sp.expand(printed), sp.expand(p.answer_expr)):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: printed key {printed} does not expand to "
            f"{p.answer_expr}"
        )


_SINUSOID = re.compile(
    r"y\s*=\s*(-?\d*)\\(?:sin|cos)\\left\("
    r"(?:(\d+)\()?x\s*([+-])\s*(\d+)\)?"
)


def _sinusoid_params(p: Problem):
    """Re-read (a, b, c) off the printed ``y = a f(b(x - c)) + d``."""
    m = _SINUSOID.search(p.question_latex.replace(" ", ""))
    if m is None:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: cannot read the sinusoid from "
            f"{p.question_latex!r}"
        )
    lead, b_txt, sign, shift = m.groups()
    a = -1 if lead == "-" else (1 if lead in ("", None) else int(lead))
    b = int(b_txt) if b_txt else 1
    # The equation prints (x - c); a printed "+" means c is negative.
    c = int(shift) if sign == "-" else -int(shift)
    return a, b, c


def _v_trig_amplitude(p: Problem) -> None:
    a, _, _ = _sinusoid_params(p)
    if not _equal(abs(a), p.answer_expr):
        raise VerificationError(f"{p.topic}/{p.subskill}: amplitude is {abs(a)}")


def _v_trig_period(p: Problem) -> None:
    _, b, _ = _sinusoid_params(p)
    expected = sp.nsimplify(2 * sp.pi / b)
    if not _equal(expected, p.answer_expr):
        raise VerificationError(f"{p.topic}/{p.subskill}: period is {expected}")


def _v_trig_phase_shift(p: Problem) -> None:
    _, _, c = _sinusoid_params(p)
    if not _equal(c, p.answer_expr):
        raise VerificationError(f"{p.topic}/{p.subskill}: phase shift is {c}")


def _v_compound_or(p: Problem) -> None:
    """Solve each half independently and union them; compare to the key.

    Also re-solves the *printed* key the same way, so a rendering that flips
    a bound is caught even when answer_expr is right.
    """
    x = sp.Symbol("x")
    halves = re.findall(r"\$([^$]+)\$", p.question_latex)
    if len(halves) != 2:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: expected two inequalities, found {len(halves)}"
        )
    solved = sp.Union(*[
        sp.solve_univariate_inequality(
            latex_relation_to_sympy(h), x, relational=False
        )
        for h in halves
    ])
    if solved != p.answer_expr:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: solves to {solved}, key says {p.answer_expr}"
        )
    printed_halves = re.findall(r"\$([^$]+)\$", p.answer_latex)
    printed = sp.Union(*[
        sp.solve_univariate_inequality(
            latex_relation_to_sympy(h), x, relational=False
        )
        for h in printed_halves
    ])
    if printed != solved:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: printed key reads as {printed}, not {solved}"
        )


def _v_evaluate_function(p: Problem) -> None:
    """Re-read f and the input off the question and substitute independently."""
    x = sp.Symbol("x")
    text = p.question_latex.strip().strip("$")
    m = re.search(r"f\(x\)\s*=\s*(.+?),\s*\\quad\s*f\((-?\d+)\)", text)
    if m is None:
        raise VerificationError(f"{p.topic}/{p.subskill}: cannot read f and input")
    expr = latex_to_sympy(m.group(1))
    expected = expr.subs(x, sp.Integer(m.group(2)))
    if not _equal(expected, p.answer_expr):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: f({m.group(2)}) = {expected}, "
            f"key says {p.answer_expr}"
        )


def _v_substitution(p: Problem) -> None:
    """Re-read the expression and variable values off the question and
    substitute independently, rather than trusting the generator's own sum.
    """
    text = p.question_latex.strip().strip("$")
    if r"\quad" not in text:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: expected an expression and values "
            f"separated by \\quad"
        )
    expr_part, assign_part = text.split(r"\quad", 1)
    expr_part = expr_part.strip().rstrip(",").strip()
    assignments = re.findall(r"([a-zA-Z])\s*=\s*(-?\d+)", assign_part)
    if len(assignments) != 2:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: expected two variable assignments, "
            f"found {len(assignments)}"
        )
    subs_map = {sp.Symbol(k): sp.Integer(v) for k, v in assignments}
    expr = latex_to_sympy(expr_part)
    expected = expr.subs(subs_map)
    if not _equal(expected, p.answer_expr):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: substitution gives {expected}, "
            f"key says {p.answer_expr}"
        )


_PAIR = re.compile(r"\((-?\d+),\s*(-?\d+)\)")


def _v_domain_range(p: Problem) -> None:
    """Recompute the domain and range from the printed ordered pairs."""
    pairs = [(int(a), int(b)) for a, b in _PAIR.findall(p.question_latex)]
    if not pairs:
        raise VerificationError(f"{p.topic}/{p.subskill}: no ordered pairs in question")
    domain = tuple(sorted({a for a, _ in pairs}))
    values = tuple(sorted({b for _, b in pairs}))
    if (domain, values) != tuple(p.answer_expr):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: domain/range should be {domain} / {values}"
        )
    # The printed key must state the same two sets, not just answer_expr.
    printed = re.findall(r"\\\{([^{}]*)\\\}", p.answer_latex)
    if len(printed) != 2:
        raise VerificationError(f"{p.topic}/{p.subskill}: key must state two sets")
    got_d = tuple(sorted(int(v) for v in printed[0].split(",")))
    got_r = tuple(sorted(int(v) for v in printed[1].split(",")))
    if (got_d, got_r) != (domain, values):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: printed key {got_d} / {got_r} != "
            f"{domain} / {values}"
        )


# Formula variables are single letters, but "rt" and "Prt" tokenize as one
# symbol -- sympy's implicit multiplication does not split adjacent letters.
# Splitting them here (rather than storing a sympy expression on the Problem)
# keeps verification a re-derivation from the printed string.
_PI_PLACEHOLDER = "Z"


def _formula_to_sympy(text: str) -> sp.Expr:
    s = text.replace(r"\ell", "L").replace(r"\pi", _PI_PLACEHOLDER)
    # Expand \dfrac first: the letter-splitter below would otherwise turn the
    # macro name itself into \d*f*r*a*c.
    s = _expand_fracs(s)
    s = re.sub(r"([A-Za-z])(?=[A-Za-z])", r"\1*", s)
    expr = latex_to_sympy(s)
    return expr.subs(sp.Symbol(_PI_PLACEHOLDER), sp.pi)


def _v_literal_equation(p: Problem) -> None:
    """Solve the printed formula for the printed variable, with sympy.

    The formula bank is authored text, so this is the check that matters: the
    key is only correct if sympy, solving the equation as printed, agrees.
    """
    text = p.question_latex.strip().strip("$")
    m = re.match(r"(.+?),\s*solve for \$?([A-Za-z])\$?$", text)
    if m is None:
        raise VerificationError(f"{p.topic}/{p.subskill}: cannot read the formula")
    body, target = m.group(1), m.group(2)
    if "=" not in body:
        raise VerificationError(f"{p.topic}/{p.subskill}: no equation in {body!r}")
    lhs_text, rhs_text = body.split("=", 1)
    lhs, rhs = _formula_to_sympy(lhs_text), _formula_to_sympy(rhs_text)
    var = sp.Symbol(target)
    solutions = sp.solve(sp.Eq(lhs, rhs), var)
    if not solutions:
        raise VerificationError(f"{p.topic}/{p.subskill}: cannot solve for {target}")

    key = p.answer_latex.strip().strip("$")
    km = re.match(rf"{target}\s*=\s*(.+)$", key)
    if km is None:
        raise VerificationError(f"{p.topic}/{p.subskill}: key must read '{target} = ...'")
    printed = _formula_to_sympy(km.group(1))
    if not any(sp.simplify(printed - s) == 0 for s in solutions):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {target} = {printed} is not a solution "
            f"(sympy gives {solutions})"
        )


def _v_classify_polynomial(p: Problem) -> None:
    """Re-count the printed expression's terms; the key must name that count."""
    text = p.question_latex.strip().strip("$")
    x = sp.Symbol("x")
    expr = latex_to_sympy(text)
    if not expr.free_symbols:
        expected = "Constant"
    else:
        nterms = len(sp.expand(expr).as_ordered_terms())
        expected = {1: "Monomial", 2: "Binomial", 3: "Trinomial"}.get(nterms, "Polynomial")
    got = p.answer_latex.strip().strip("$")
    m = re.match(r"\\text\{(.+)\}$", got)
    if m:
        got = m.group(1)
    if got != expected:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {p.question_latex} should classify as "
            f"{expected!r}, key says {got!r}"
        )


def _v_standard_form(p: Problem) -> None:
    """Algebraic identity against the question, plus a structural check that
    the printed key's powers of x are strictly descending."""
    got = latex_to_sympy(p.question_latex)
    answer = latex_to_sympy(p.answer_latex)
    if not _equal(sp.expand(got), sp.expand(answer)):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {p.question_latex} != {p.answer_latex}"
        )
    ans_text = p.answer_latex.strip().strip("$").replace(" ", "")
    powers = []
    for term in re.findall(r"[+-]?[^+-]+", ans_text):
        m = re.search(r"x\^\{(-?\d+)\}", term)
        if m:
            powers.append(int(m.group(1)))
        elif "x" in term:
            powers.append(1)
        else:
            powers.append(0)
    if powers != sorted(powers, reverse=True):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: key {p.answer_latex!r} is not in "
            f"standard (descending-power) form: read powers {powers}"
        )


def _v_simplify_radical_vars(p: Problem) -> None:
    """Independently recompute the printed radical (bare or a quotient
    radicand) with positive-valued variables and compare to the key."""
    text = p.question_latex.strip().strip("$")
    m = re.match(r"\\sqrt(?:\[(\d+)\])?\{", text)
    if not m:
        raise VerificationError(f"{p.topic}/{p.subskill}: cannot read radical from {p.question_latex!r}")
    n = int(m.group(1)) if m.group(1) else 2
    body, end = _match_group(text, m.end() - 1)
    if end != len(text):
        raise VerificationError(f"{p.topic}/{p.subskill}: trailing content in {p.question_latex!r}")
    if r"\dfrac" in body or r"\frac" in body:
        fracs = _extract_fracs(body)
        if len(fracs) != 1:
            raise VerificationError(f"{p.topic}/{p.subskill}: expected 1 fraction in {body!r}")
        numer_t, denom_t = fracs[0]
        radicand = latex_to_sympy(numer_t) / latex_to_sympy(denom_t)
    else:
        radicand = latex_to_sympy(body)
    subs = {s: sp.Symbol(s.name, positive=True) for s in radicand.free_symbols}
    radicand = radicand.subs(subs)
    got = sp.root(radicand, n)

    # Parse the PRINTED key too (not just answer_expr), with the same
    # positive-variable assumption -- comparing in plain-symbol space can't
    # prove e.g. sqrt(x*y) == sqrt(x)*sqrt(y) even though it holds for
    # positive reals, so both sides have to be compared positive-for-positive.
    ans_text = p.answer_latex.strip().strip("$")
    printed = latex_to_sympy(ans_text)
    printed = printed.subs({s: sp.Symbol(s.name, positive=True) for s in printed.free_symbols})
    if not _equal(got, printed):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {p.question_latex} simplifies to {got}, "
            f"printed key {p.answer_latex!r} reads as {printed}"
        )
    got_plain = got.subs({s: sp.Symbol(s.name) for s in got.free_symbols})
    if not _equal(got_plain, p.answer_expr):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {p.question_latex} simplifies to {got}, "
            f"but the generator's own answer_expr says {p.answer_expr}"
        )


def _v_vertex_and_direction(p: Problem) -> None:
    """Recompute the vertex and opening direction from the printed equation."""
    text = p.question_latex.strip().strip("$")
    x = sp.Symbol("x")
    rhs = latex_to_sympy(text.split("=", 1)[1])
    poly_ = sp.Poly(rhs, x)
    if poly_.degree() != 2:
        raise VerificationError(f"{p.topic}/{p.subskill}: {p.question_latex} is not quadratic")
    a, b, _c = poly_.all_coeffs()
    h = -b / (2 * a)
    k = rhs.subs(x, h)
    expected_dir = "maximum" if a < 0 else "minimum"
    pts = _POINT.findall(p.answer_latex)
    if len(pts) != 1:
        raise VerificationError(f"{p.topic}/{p.subskill}: cannot read vertex from {p.answer_latex!r}")
    ph, pk = sp.Integer(pts[0][0]), sp.Integer(pts[0][1])
    if not (_equal(ph, h) and _equal(pk, k)):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: vertex should be ({h}, {k}), key says ({ph}, {pk})"
        )
    if expected_dir not in p.answer_latex:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: parabola should state {expected_dir!r}, "
            f"key is {p.answer_latex!r}"
        )


def _v_vertex_form_complete_square(p: Problem) -> None:
    """The printed vertex form must expand to the same polynomial as the
    printed standard form, and evaluate to the re-derived vertex value k at
    the re-derived vertex x = h."""
    text = p.question_latex.strip().strip("$")
    if "=" not in text:
        raise VerificationError(f"{p.topic}/{p.subskill}: no '=' in {p.question_latex!r}")
    x = sp.Symbol("x")
    rhs = latex_to_sympy(text.split("=", 1)[1])
    poly_ = sp.Poly(rhs, x)
    if poly_.degree() != 2:
        raise VerificationError(f"{p.topic}/{p.subskill}: {p.question_latex} is not quadratic")
    a, b, c = poly_.all_coeffs()
    h = -sp.Rational(b, 2 * a)
    k = c - sp.Rational(b, 2) ** 2 / a

    ans_text = p.answer_latex.strip().strip("$")
    if "=" not in ans_text:
        raise VerificationError(f"{p.topic}/{p.subskill}: no '=' in key {p.answer_latex!r}")
    printed = latex_to_sympy(ans_text.split("=", 1)[1])
    if not _equal(sp.expand(printed), sp.expand(rhs)):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: printed vertex form does not expand to "
            f"{rhs}"
        )
    if not _equal(printed.subs(x, h), k):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: printed vertex form does not equal the "
            f"re-derived vertex value {k} at x = {h}"
        )


def _v_complete_square_blanks(p: Problem) -> None:
    """Re-derive both blanks from the printed ``ax^2+bx+c=0`` and require the
    printed pair to match."""
    text = p.question_latex.strip().strip("$")
    eq_part = text.split(r"\quad\Rightarrow\quad")[0].strip()
    if "=" not in eq_part:
        raise VerificationError(f"{p.topic}/{p.subskill}: no '=' in {eq_part!r}")
    lhs_t, rhs_t = eq_part.split("=", 1)
    x = sp.Symbol("x")
    lhs = latex_to_sympy(lhs_t) - latex_to_sympy(rhs_t)
    poly_ = sp.Poly(lhs, x)
    if poly_.degree() != 2:
        raise VerificationError(f"{p.topic}/{p.subskill}: {eq_part} is not quadratic")
    a, b, _c = poly_.all_coeffs()
    k = sp.Rational(b, 2 * a) ** 2
    right = a * k

    ans_text = p.answer_latex.strip().strip("$")
    nums = re.findall(r"-?\d+", ans_text)
    if len(nums) != 2:
        raise VerificationError(f"{p.topic}/{p.subskill}: cannot read two blanks from {ans_text!r}")
    pk, pr = sp.Integer(nums[0]), sp.Integer(nums[1])
    if not (_equal(pk, k) and _equal(pr, right)):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: blanks should be ({k}, {right}), key says ({pk}, {pr})"
        )


def _v_solve_quadratic_no_real(p: Problem) -> None:
    """Re-derive the discriminant from the printed equation; require it to be
    negative and the key to state "no real solutions"."""
    text = p.question_latex.strip().strip("$")
    if "=" not in text:
        raise VerificationError(f"{p.topic}/{p.subskill}: no '=' in {p.question_latex!r}")
    lhs_t, rhs_t = text.split("=", 1)
    x = sp.Symbol("x")
    poly_ = sp.Poly(latex_to_sympy(lhs_t) - latex_to_sympy(rhs_t), x)
    if poly_.degree() != 2:
        raise VerificationError(f"{p.topic}/{p.subskill}: {p.question_latex} is not quadratic")
    a, b, c = poly_.all_coeffs()
    disc = b * b - 4 * a * c
    if disc >= 0:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: discriminant {disc} >= 0, real solutions exist"
        )
    if "no real solution" not in p.answer_latex.lower():
        raise VerificationError(
            f"{p.topic}/{p.subskill}: key does not state 'no real solutions': {p.answer_latex!r}"
        )


# --------------------------------------------------------------------------
# properties: commutative / associative / identity / inverse
# --------------------------------------------------------------------------

_PROP_NAME = {"commutative": "Commutative", "associative": "Associative",
              "identity": "Identity", "inverse": "Inverse"}
_OP_NAME = {"+": "Addition", "*": "Multiplication"}
_OP_KEY = {"+": "add", "*": "mul"}


def _property_tokenize(s: str) -> list:
    s = s.replace(" ", "")
    s = re.sub(r"\\d?frac\{1\}\{([^{}]+)\}", r"INV(\1)", s)
    tokens = re.findall(r"INV|\\cdot|\d+|[A-Za-z]|[()+\-]", s)
    return ["*" if t == r"\cdot" else t for t in tokens]


def _property_parse_primary(tokens: list, i: int):
    if i >= len(tokens):
        raise VerificationError("properties: unexpected end of expression")
    t = tokens[i]
    if t == "-":
        node, i = _property_parse_primary(tokens, i + 1)
        return ("neg", node), i
    if t == "(":
        node, i = _property_parse_expr(tokens, i + 1)
        if i >= len(tokens) or tokens[i] != ")":
            raise VerificationError("properties: unbalanced parentheses")
        return node, i + 1
    if t == "INV":
        if i + 1 >= len(tokens) or tokens[i + 1] != "(":
            raise VerificationError("properties: malformed 1/x term")
        node, i = _property_parse_expr(tokens, i + 2)
        if i >= len(tokens) or tokens[i] != ")":
            raise VerificationError("properties: unbalanced parentheses in 1/x term")
        return ("inv", node), i + 1
    if t.isdigit():
        return ("num", int(t)), i + 1
    if len(t) == 1 and t.isalpha():
        return ("var", t), i + 1
    raise VerificationError(f"properties: unrecognized token {t!r}")


def _property_parse_expr(tokens: list, i: int):
    node, i = _property_parse_primary(tokens, i)
    while i < len(tokens) and tokens[i] in ("+", "*"):
        op = tokens[i]
        rhs, i = _property_parse_primary(tokens, i + 1)
        node = ("bin", op, node, rhs)
    return node, i


def _property_parse_side(text: str):
    tokens = _property_tokenize(text)
    if not tokens:
        raise VerificationError("properties: empty side of equation")
    node, i = _property_parse_expr(tokens, 0)
    if i != len(tokens):
        raise VerificationError(f"properties: trailing tokens in {text!r}")
    return node


def _property_is_atom(n) -> bool:
    return n[0] in ("num", "var", "neg", "inv")


def _property_check_identity(lhs, rhs, op) -> bool:
    identity_elem = ("num", 0) if op == "+" else ("num", 1)
    for atom_side, other in ((lhs, rhs), (rhs, lhs)):
        if _property_is_atom(atom_side) and other[0] == "bin" and other[1] == op:
            l, r = other[2], other[3]
            if (l == atom_side and r == identity_elem) or (r == atom_side and l == identity_elem):
                return True
    return False


def _property_check_inverse(lhs, rhs, op) -> bool:
    identity_elem = ("num", 0) if op == "+" else ("num", 1)
    inv_op = "neg" if op == "+" else "inv"
    for atom_side, other in ((lhs, rhs), (rhs, lhs)):
        if atom_side == identity_elem and other[0] == "bin" and other[1] == op:
            l, r = other[2], other[3]
            if r == (inv_op, l) or l == (inv_op, r):
                return True
    return False


def _property_check_commutative(lhs, rhs, op) -> bool:
    if lhs[0] == "bin" and rhs[0] == "bin" and lhs[1] == op and rhs[1] == op:
        l1, r1 = lhs[2], lhs[3]
        l2, r2 = rhs[2], rhs[3]
        if l1[0] != "bin" and r1[0] != "bin" and l2[0] != "bin" and r2[0] != "bin":
            if l1 == r2 and r1 == l2:
                return True
    return False


def _property_flatten(n, op) -> list:
    if n[0] == "bin" and n[1] == op:
        return _property_flatten(n[2], op) + _property_flatten(n[3], op)
    return [n]


def _property_check_associative(lhs, rhs, op) -> bool:
    if lhs[0] == "bin" and rhs[0] == "bin" and lhs[1] == op and rhs[1] == op:
        nested = any(
            side[0] == "bin" and side[1] == op
            for side in (lhs[2], lhs[3], rhs[2], rhs[3])
        )
        if nested and lhs != rhs:
            return _property_flatten(lhs, op) == _property_flatten(rhs, op)
    return False


def _property_classify(lhs, rhs):
    op = lhs[1] if lhs[0] == "bin" else (rhs[1] if rhs[0] == "bin" else None)
    if op is None:
        raise VerificationError("properties: no operator found in equation")
    matches = []
    if _property_check_identity(lhs, rhs, op):
        matches.append("identity")
    if _property_check_inverse(lhs, rhs, op):
        matches.append("inverse")
    if _property_check_commutative(lhs, rhs, op):
        matches.append("commutative")
    if _property_check_associative(lhs, rhs, op):
        matches.append("associative")
    if len(matches) != 1:
        raise VerificationError(
            f"properties: equation classifies as {matches} (expected exactly one match)"
        )
    return matches[0], op


def _v_property(p: Problem) -> None:
    m = re.search(r"\$(.*?)\$", p.question_latex, re.S)
    if not m:
        raise VerificationError(f"{p.topic}/{p.subskill}: no equation found in {p.question_latex!r}")
    eq = m.group(1)
    if "=" not in eq:
        raise VerificationError(f"{p.topic}/{p.subskill}: no '=' in equation {eq!r}")
    lhs_text, rhs_text = eq.split("=", 1)
    lhs = _property_parse_side(lhs_text)
    rhs = _property_parse_side(rhs_text)

    prop, op = _property_classify(lhs, rhs)
    op_name = _OP_NAME[op]
    derived_label = f"{_PROP_NAME[prop]} Property of {op_name}"

    mp = re.search(r"\\begin\{minipage\}.*?\n(.*?)\\end\{minipage\}", p.question_latex, re.S)
    if not mp:
        raise VerificationError(f"{p.topic}/{p.subskill}: no choice block found")
    raw_lines = [ln.strip() for ln in re.split(r"\\\\", mp.group(1)) if ln.strip()]
    choices = {}
    for ln in raw_lines:
        cm = re.match(r"([A-D])\)\s*(.+)$", ln)
        if not cm:
            raise VerificationError(f"{p.topic}/{p.subskill}: unparsable choice line {ln!r}")
        choices[cm.group(1)] = cm.group(2).strip()
    if len(choices) != 4:
        raise VerificationError(f"{p.topic}/{p.subskill}: expected 4 choices, got {choices}")

    labels = list(choices.values())
    if len(set(labels)) != 4:
        raise VerificationError(f"{p.topic}/{p.subskill}: duplicate choices {labels}")

    matching_letters = [ltr for ltr, lbl in choices.items() if lbl == derived_label]
    if len(matching_letters) != 1:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: derived property {derived_label!r} not found exactly "
            f"once among printed choices {labels}"
        )
    correct_letter = matching_letters[0]

    am = re.match(r"([A-D])\)\s*(.+)$", p.answer_latex.strip())
    if not am:
        raise VerificationError(f"{p.topic}/{p.subskill}: unparsable answer_latex {p.answer_latex!r}")
    if am.group(1) != correct_letter or am.group(2).strip() != derived_label:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: printed answer {p.answer_latex!r} does not point at the "
            f"derived property {correct_letter}) {derived_label}"
        )

    expected_others = {
        f"{_PROP_NAME[pr]} Property of {op_name}" for pr in ("commutative", "associative", "identity", "inverse")
        if pr != prop
    }
    other_labels = {lbl for ltr, lbl in choices.items() if ltr != correct_letter}
    if other_labels != expected_others:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: distractor choices {other_labels} are not the other "
            f"three {op_name} properties {expected_others}"
        )

    expected_answer_expr = f"{prop}_{_OP_KEY[op]}"
    if p.answer_expr != expected_answer_expr:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: answer_expr {p.answer_expr!r} does not match derived "
            f"property {expected_answer_expr!r}"
        )
