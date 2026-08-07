"""LaTeX -> sympy parsing and exact comparison.

The shared bottom layer of verification: turning the rendered string a student
sees back into something sympy can reason about, and comparing two values
exactly. Everything here is subject-agnostic; the per-topic strategies live in
``algebra``, ``geometry`` and ``data``.
"""

from __future__ import annotations

import re
from typing import List

import sympy as sp
from sympy.parsing.sympy_parser import (
    implicit_multiplication,
    parse_expr,
    rationalize,
    standard_transformations,
)



# ``rationalize`` converts decimal literals to exact Rationals at tokenize
# time, before any arithmetic happens. Without it parse_expr evaluates
# 11.7 - 10.9 in binary floats to 0.7999999999999998, and no comparison
# afterwards can recover the 4/5 the worksheet actually means.
_TRANSFORMS = standard_transformations + (implicit_multiplication, rationalize)

class VerificationError(AssertionError):
    pass

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
    # Absolute value bars: |...| -> Abs(...). Our renderers never nest bars,
    # so a left-to-right non-greedy pairing is unambiguous.
    s = re.sub(r"\|([^|]+)\|", r"Abs(\1)", s)
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
    # A decimal printed on a worksheet denotes an exact value: 11.7 means
    # 117/10, not the nearest double. Converting at parse time keeps the
    # arithmetic exact all the way through -- otherwise 11.7 - 10.9 evaluates
    # to 0.7999999999999998 and no comparison can rescue it afterwards.
    # A point like "(3, 5)" parses to a plain Python tuple, which has no
    # .atoms -- only expressions get the float conversion.
    floats = expr.atoms(sp.Float) if hasattr(expr, "atoms") else ()
    if floats:
        expr = expr.xreplace({f: sp.Rational(str(f)) for f in floats})
    return expr

_REL_TOKEN = re.compile(r"\\geq|\\leq|\\ge|\\le|\\gt|\\lt|<=|>=|<|>")

_REL_OP = {
    r"\geq": ">=", r"\leq": "<=", r"\ge": ">=", r"\le": "<=",
    r"\gt": ">", r"\lt": "<", "<=": "<=", ">=": ">=", "<": "<", ">": ">",
}

_REL_CLASS = {"<": sp.Lt, "<=": sp.Le, ">": sp.Gt, ">=": sp.Ge}

def _split_relation(s: str):
    """Split ``lhs REL rhs`` on the first relation token, before the macro
    guard in :func:`latex_to_sympy` would trip on the backslash."""
    m = _REL_TOKEN.search(s)
    if not m:
        raise VerificationError(f"no relation symbol found in {s!r}")
    return s[: m.start()], _REL_OP[m.group()], s[m.end() :]

def latex_relation_to_sympy(latex: str) -> sp.core.relational.Relational:
    """Parse ``x \\ge 11`` (or ``<``, ``>``, ``\\le``) into a sympy relation."""
    s = latex.strip().strip("$").strip()
    lhs_text, op, rhs_text = _split_relation(s)
    lhs = latex_to_sympy(lhs_text)
    rhs = latex_to_sympy(rhs_text)
    return _REL_CLASS[op](lhs, rhs)

def _mixed_to_sympy(latex: str) -> sp.Expr:
    """Mixed numbers ``1\\frac{7}{12}`` mean 1 + 7/12, not 1 * 7/12."""
    s = latex.strip().strip("$").strip()
    m = re.fullmatch(r"(-?)(\d+)\s*(\\d?frac\{[^{}]*\}\{[^{}]*\})", s)
    if m:
        sign = -1 if m.group(1) == "-" else 1
        return sign * (sp.Integer(m.group(2)) + latex_to_sympy(m.group(3)))
    return latex_to_sympy(s)

def _exactify(x):
    """Replace every Float with the exact rational its digits denote.

    ``3.4`` on a worksheet means 17/5, not the nearest binary double, and
    comparisons have to be exact. Doing this *before* nsimplify also avoids a
    trap: bare ``nsimplify`` hunts for a closed form with radicals, and given
    a plain float it happily returns things like
    ``17640*5**(109/168)*6**(107/168)*7**(4/7)`` for 477000.0 -- which then
    compares equal to nothing at all.
    """
    expr = sp.sympify(x)
    floats = expr.atoms(sp.Float) if hasattr(expr, "atoms") else ()
    if not floats:
        return expr
    return expr.xreplace({f: sp.Rational(str(f)) for f in floats})

def _equal(a, b) -> bool:
    try:
        diff = sp.simplify(_exactify(a) - _exactify(b))
        return bool(diff == 0)
    except (TypeError, sp.SympifyError, AttributeError):
        return False

_POINT = re.compile(r"\(\s*(-?\d+)\s*,\s*(-?\d+)\s*\)")

# Matches a bare "$5$", a dollar amount "$\$5$", or a percent "$5\%$" --
# always the integer between the outer math delimiters, in reading order.
_NUM = re.compile(r"\$\\?\$?(-?\d+)\\?%?\$")

def _nums(text: str) -> List[sp.Integer]:
    """Pull every printed integer out of a prose question, in reading order."""
    return [sp.Integer(x) for x in _NUM.findall(text)]

_DECIMAL = re.compile(r"\$(-?\d+(?:\.\d+)?)\$")

def _nums_any(text: str) -> sp.Rational:
    """The single plain (possibly decimal) number in a ``$...$`` string.

    ``_nums`` only reads integers; scientific notation needs the decimal form
    too, and exactly one of them, so a malformed question fails loudly rather
    than silently verifying against the wrong token.
    """
    found = _DECIMAL.findall(text)
    if len(found) != 1:
        raise VerificationError(
            f"expected exactly one plain number, found {len(found)} in {text!r}"
        )
    return sp.Rational(found[0])
