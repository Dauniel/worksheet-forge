"""Verification strategies for figures: areas, volumes, surface areas,
circles, the Pythagorean theorem, and trigonometry.

Each one re-reads the *printed labels* off the rendered LaTeX rather than
trusting the generator, so a figure and its answer key cannot disagree.
"""

from __future__ import annotations

import re

import sympy as sp

from ..problem import Problem

from .parsing import (
    VerificationError,
    _equal,
    _nums,
    latex_to_sympy,
)


def _v_geo_rectangle_area(p: Problem) -> None:
    l, w = _nums(p.question_latex)
    if not _equal(l * w, p.answer_expr):
        raise VerificationError(f"{p.topic}/{p.subskill}: area should be {l * w}")

def _v_geo_square_area(p: Problem) -> None:
    (s,) = _nums(p.question_latex)
    if not _equal(s * s, p.answer_expr):
        raise VerificationError(f"{p.topic}/{p.subskill}: area should be {s * s}")

def _circle_radius(p: Problem) -> sp.Integer:
    """Read the radius back off the figure's own label.

    The figure prints ``r = 7`` or ``d = 14``; which one it is determines the
    answer, so it is re-read here rather than taken on the generator's word.
    A diameter that is not even would make the radius fractional and is a bug
    in the generator, not a legal problem.
    """
    m = re.search(r"([rd])\s*=\s*(\d+)", p.question_latex)
    if m is None:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: circle figure has no 'r =' or 'd =' label"
        )
    name, n = m.group(1), sp.Integer(m.group(2))
    if name == "r":
        return n
    if n % 2 != 0:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: odd diameter {n} gives a fractional radius"
        )
    return n / 2

def _v_geo_circle_area(p: Problem) -> None:
    r = _circle_radius(p)
    expected = sp.pi * r**2
    if not _equal(expected, p.answer_expr):
        raise VerificationError(f"{p.topic}/{p.subskill}: area should be {expected}")

def _v_geo_circle_circumference(p: Problem) -> None:
    r = _circle_radius(p)
    expected = 2 * sp.pi * r
    if not _equal(expected, p.answer_expr):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: circumference should be {expected}"
        )

_TRI_LABEL = re.compile(r"\{\$(x|-?\d+)\$\}")

def _v_geo_pythagorean(p: Problem) -> None:
    """Re-read the three side labels and solve for whichever one is ``x``.

    ``right_triangle_fig`` always emits base, vertical leg, hypotenuse in
    that order, so position identifies the side without trusting any
    generator metadata.
    """
    labels = _TRI_LABEL.findall(p.question_latex)
    if len(labels) != 3:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: expected 3 side labels, found {len(labels)}"
        )
    if labels.count("x") != 1:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: exactly one side must be unknown, got {labels}"
        )
    a, b, c = labels
    if c == "x":
        expected = sp.sqrt(sp.Integer(a) ** 2 + sp.Integer(b) ** 2)
    elif a == "x":
        expected = sp.sqrt(sp.Integer(c) ** 2 - sp.Integer(b) ** 2)
    else:
        expected = sp.sqrt(sp.Integer(c) ** 2 - sp.Integer(a) ** 2)
    if not _equal(expected, p.answer_expr):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: missing side should be {expected}"
        )

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

def _v_special_triangle_hyp(p: Problem) -> None:
    """Recompute the hypotenuse from the printed triangle type and leg."""
    text = p.question_latex
    is_306090 = "30" in text and "60" in text
    nums = _nums(text)
    if not nums:
        raise VerificationError(f"{p.topic}/{p.subskill}: no leg length found in {text!r}")
    leg = nums[-1]
    expected = 2 * leg if is_306090 else leg * sp.sqrt(2)

    printed = latex_to_sympy(p.answer_latex)
    if not _equal(expected, printed):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: hypotenuse should be {expected}, key says {printed}"
        )

def _v_right_triangle_find_angle(p: Problem) -> None:
    """Classify which ratio applies from the printed wording (never from
    generator state), then re-derive the angle with the matching inverse
    trig function."""
    text = p.question_latex
    nums = _nums(text)
    has_opp, has_adj, has_hyp = "opposite" in text, "adjacent" in text, "hypotenuse" in text

    if has_opp and has_adj and not has_hyp:
        expected = (180 / sp.pi) * sp.atan(sp.Rational(nums[0], nums[1]))
    elif has_opp and has_hyp:
        expected = (180 / sp.pi) * sp.asin(sp.Rational(nums[0], nums[1]))
    elif has_adj and has_hyp:
        expected = (180 / sp.pi) * sp.acos(sp.Rational(nums[0], nums[1]))
    else:
        raise VerificationError(f"{p.topic}/{p.subskill}: cannot classify triangle in {text!r}")
    expected = sp.nsimplify(expected)

    m = re.search(r"(-?\d+)\^\\circ", p.answer_latex)
    if not m:
        raise VerificationError(f"{p.topic}/{p.subskill}: cannot read key {p.answer_latex!r}")
    printed = sp.Integer(m.group(1))
    if not _equal(expected, printed):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: angle should be {expected}, key says {printed}"
        )

_PI_FRAC = re.compile(r"\\dfrac\{(-?\d*)\\pi\}\{(\d+)\}")

_PI_PLAIN = re.compile(r"^(-?\d*)\\pi$")

def _parse_pi_multiple(text: str) -> sp.Rational:
    """Parse a bare ``"0"``, ``"\\pi"``/``"-\\pi"``/``"2\\pi"``, or
    ``"\\dfrac{n\\pi}{d}"`` fragment into the rational multiple of pi it
    represents."""
    text = text.strip().strip("$")
    if text == "0":
        return sp.Integer(0)

    def _coef(s: str) -> int:
        return 1 if s == "" else (-1 if s == "-" else int(s))

    m = _PI_FRAC.match(text)
    if m:
        return sp.Rational(_coef(m.group(1)), int(m.group(2)))
    m = _PI_PLAIN.match(text)
    if m:
        return sp.Integer(_coef(m.group(1)))
    raise VerificationError(f"cannot parse pi-fraction {text!r}")

def _v_degree_radian_conversion(p: Problem) -> None:
    direction = p.verify.get("direction")
    if direction == "to_radians":
        m = re.match(r"\$(-?\d+)\^\\circ\$", p.question_latex)
        if not m:
            raise VerificationError(f"{p.topic}/{p.subskill}: cannot parse {p.question_latex!r}")
        deg = int(m.group(1))
        want = sp.Rational(deg, 180)
        got = _parse_pi_multiple(p.answer_latex)
    else:
        got_frac = _parse_pi_multiple(p.question_latex)
        want = got_frac * 180
        m = re.match(r"\$(-?\d+)\^\\circ\$", p.answer_latex)
        if not m:
            raise VerificationError(f"{p.topic}/{p.subskill}: cannot read key {p.answer_latex!r}")
        got = sp.Integer(m.group(1))

    if want != got:
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {p.question_latex} -> expected {want}, key gives {got}"
        )

def _v_exact_trig_value(p: Problem) -> None:
    m = re.match(r"\$\\(sin|cos|tan)\((-?\d+)\^\\circ\)\$", p.question_latex)
    if not m:
        raise VerificationError(f"{p.topic}/{p.subskill}: cannot parse {p.question_latex!r}")
    func = {"sin": sp.sin, "cos": sp.cos, "tan": sp.tan}[m.group(1)]
    angle = int(m.group(2))
    expected = sp.nsimplify(func(sp.rad(angle)))
    printed = latex_to_sympy(p.answer_latex)
    if not _equal(expected, printed):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: {p.question_latex} = {expected}, key says {printed}"
        )
