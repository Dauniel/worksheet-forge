"""LaTeX formatting primitives.

These exist because the naive string builds (``f"{m}x + {b}"``) produce the
classic worksheet-smell bugs: ``1y``, ``-1x``, ``0x``, ``+ -3``. Every
generator must build linear/polynomial text through these helpers.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Iterable

import sympy as sp


def num(value) -> str:
    """Render a rational as an integer or a \\frac, never a float."""
    f = Fraction(sp.nsimplify(value)) if not isinstance(value, Fraction) else value
    if f.denominator == 1:
        return str(f.numerator)
    sign = "-" if f.numerator < 0 else ""
    return rf"{sign}\frac{{{abs(f.numerator)}}}{{{f.denominator}}}"


def dnum(value) -> str:
    """Same as :func:`num` but display-style, for question bodies."""
    return num(value).replace(r"\frac", r"\dfrac")


def mixed(value, display: bool = False) -> str:
    """Improper fractions with magnitude > 1 render as mixed numbers."""
    f = value if isinstance(value, Fraction) else Fraction(sp.nsimplify(value))
    if f.denominator == 1:
        return str(f.numerator)
    sign = "-" if f < 0 else ""
    a = abs(f)
    whole, rem = divmod(a.numerator, a.denominator)
    frac = r"\dfrac" if display else r"\frac"
    if whole == 0:
        return rf"{sign}{frac}{{{rem}}}{{{a.denominator}}}"
    return rf"{sign}{whole}{frac}{{{rem}}}{{{a.denominator}}}"


def coeff(c, var: str, display: bool = False) -> str:
    """A single coefficient-times-variable term: ``1y`` -> ``y``, ``-1x`` -> ``-x``.

    Returns the empty string when the coefficient is zero; callers drop the term.
    """
    f = c if isinstance(c, Fraction) else Fraction(sp.nsimplify(c))
    if f == 0:
        return ""
    if f == 1:
        return var
    if f == -1:
        return f"-{var}"
    body = dnum(f) if display else num(f)
    return f"{body}{var}"


def _join(parts: Iterable[str]) -> str:
    out = ""
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if not out:
            out = p
        elif p.startswith("-"):
            out += f" - {p[1:].strip()}"
        else:
            out += f" + {p}"
    return out or "0"


def terms(*parts: str) -> str:
    """Join pre-rendered terms with correct + / - infix spacing."""
    return _join(parts)


def linear(m, b, var: str = "x", display: bool = False) -> str:
    """``m*var + b`` with all degenerate cases handled.

    ``linear(0, 5)`` -> ``5``; ``linear(-1, -3)`` -> ``-x - 3``.
    """
    const = dnum if display else num
    return _join([coeff(m, var, display), const(b) if b != 0 else ""])


def var_pow(var: str, power) -> str:
    """A single ``var^power`` factor, for juxtaposed (multiplied) monomial
    factors -- not +/- joined terms. ``power == 1`` drops the exponent
    (``var_pow("x", 1) == "x"``); ``power == 0`` drops the variable entirely
    (``var_pow("x", 0) == ""``), so callers can concatenate factors directly
    without special-casing either edge.
    """
    if power == 0:
        return ""
    if power == 1:
        return var
    return f"{var}^{{{power}}}"


def poly(coeffs, var: str = "x", display: bool = False) -> str:
    """Render a polynomial from a highest-degree-first coefficient sequence."""
    coeffs = list(coeffs)
    deg = len(coeffs) - 1
    parts = []
    for i, c in enumerate(coeffs):
        power = deg - i
        if power == 0:
            const = dnum if display else num
            parts.append(const(c) if c != 0 else "")
        elif power == 1:
            parts.append(coeff(c, var, display))
        else:
            parts.append(coeff(c, f"{var}^{{{power}}}", display))
    return _join(parts)
