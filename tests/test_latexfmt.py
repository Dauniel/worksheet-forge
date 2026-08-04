"""Coefficient rendering edge cases -- the classic worksheet-smell bugs."""

from __future__ import annotations

from fractions import Fraction

import pytest

from forge.core.latexfmt import coeff, linear, mixed, num, poly, terms


@pytest.mark.parametrize(
    "c,var,expected",
    [
        (1, "y", "y"),
        (-1, "x", "-x"),
        (0, "x", ""),
        (3, "x", "3x"),
        (-4, "x", "-4x"),
    ],
)
def test_coeff(c, var, expected):
    assert coeff(c, var) == expected


def test_one_coefficient_is_implicit():
    # 3x + 1y = 9  ->  3x + y = 9
    assert f"{terms(coeff(3, 'x'), coeff(1, 'y'))} = 9" == "3x + y = 9"


def test_negative_one_coefficient():
    # y = -1x - 3  ->  y = -x - 3
    assert linear(-1, -3) == "-x - 3"


def test_zero_slope_drops_the_variable():
    # y = 0x + 5  ->  y = 5
    assert linear(0, 5) == "5"


def test_zero_intercept_drops_the_constant():
    assert linear(4, 0) == "4x"


def test_all_zero_is_zero():
    assert linear(0, 0) == "0"


def test_no_plus_negative():
    assert "+ -" not in linear(2, -7)
    assert linear(2, -7) == "2x - 7"


def test_fractional_slope():
    assert linear(Fraction(2, 3), -1) == r"\frac{2}{3}x - 1"
    assert linear(Fraction(2, 3), -1, display=True) == r"\dfrac{2}{3}x - 1"


def test_num_never_emits_a_float():
    assert num(Fraction(6, 3)) == "2"
    assert num(Fraction(-3, 4)) == r"-\frac{3}{4}"
    assert "." not in num(Fraction(1, 8))


def test_mixed_numbers():
    # Improper fractions greater than 1 display as mixed numbers.
    assert mixed(Fraction(19, 12)) == r"1\frac{7}{12}"
    assert mixed(Fraction(19, 12), display=True) == r"1\dfrac{7}{12}"
    assert mixed(Fraction(7, 12)) == r"\frac{7}{12}"
    assert mixed(Fraction(-19, 12)) == r"-1\frac{7}{12}"
    assert mixed(Fraction(4, 2)) == "2"


def test_poly_edge_cases():
    assert poly([1, -1, 0]) == "x^{2} - x"
    assert poly([0, 3, -5]) == "3x - 5"
    assert poly([2, 0, 0, 1]) == "2x^{3} + 1"


def test_display_mode_scales_the_constant_too():
    r"""A display-style line must not mix \dfrac and \frac on one line.

    ``linear(m, b, display=True)`` used to pass ``display`` only to the
    variable term and render the constant with plain ``num``, so
    ``-2x + 5 >= -x/3 - 10/3`` printed a full-size coefficient fraction next
    to a shrunken constant fraction.
    """
    out = linear(Fraction(-1, 3), Fraction(-10, 3), display=True)
    assert r"\dfrac" in out
    assert r"-\frac" not in out
    assert out == r"-\dfrac{1}{3}x - \dfrac{10}{3}"


def test_poly_display_mode_scales_the_constant_too():
    out = poly([2, Fraction(-7, 2)], display=True)
    assert out == r"2x - \dfrac{7}{2}"


def test_non_display_constant_stays_inline():
    assert linear(Fraction(1, 2), Fraction(3, 4)) == r"\frac{1}{2}x + \frac{3}{4}"
