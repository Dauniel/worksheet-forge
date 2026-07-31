"""TikZ figure builders for geometry problems.

These functions only *render* a picture from numbers the generator already
sampled and used to compute the answer -- they introduce no new randomness
and no new problem data. Every dimension label placed on a figure is the
same ``$n$`` token the verifier extracts from the rendered LaTeX (see
``forge/core/verify.py::_nums``), so the figure and the answer key can never
disagree: there is exactly one source of truth for each number.

Layout choices below (where the apex sits, how far the back face is offset,
where a right-angle tick is drawn) are cosmetic and are not sampled -- they
are fixed so every figure of a given shape looks the same way, just scaled
and labeled differently.
"""

from __future__ import annotations

import math

TARGET = 3.6  # cm -- the longest raw dimension in a 2-D figure maps to this


def _scale(*vals: float, target: float = TARGET) -> float:
    return target / max(vals)


def _wrap(body: str) -> str:
    return "\\begin{center}\n\\begin{tikzpicture}[line width=0.7pt]\n" + body + "\n\\end{tikzpicture}\n\\end{center}\n"


def _right_angle(x: float, y: float, size: float = 0.22) -> str:
    """A small open-square tick marking a right angle at (x, y)."""
    return rf"\draw ({x:.3f},{y:.3f}) ++({size:.3f},0) -- ++(0,{size:.3f}) -- ++({-size:.3f},0);"


def rectangle_fig(l: int, w: int) -> str:
    u = _scale(l, w)
    lu, wu = l * u, w * u
    body = (
        rf"\draw (0,0) rectangle ({lu:.3f},{wu:.3f});" "\n"
        rf"\node at ({lu / 2:.3f},{-0.35:.3f}) {{${l}$}};" "\n"
        rf"\node[rotate=90] at ({-0.35:.3f},{wu / 2:.3f}) {{${w}$}};"
    )
    return _wrap(body)


def square_fig(s: int) -> str:
    u = _scale(s)
    su = s * u
    body = (
        rf"\draw (0,0) rectangle ({su:.3f},{su:.3f});" "\n"
        rf"\node at ({su / 2:.3f},{-0.35:.3f}) {{${s}$}};"
    )
    return _wrap(body)


def triangle_fig(b: int, h: int) -> str:
    u = _scale(b, h)
    bu, hu = b * u, h * u
    apex_x = 0.4 * bu
    body = (
        rf"\draw (0,0) -- ({bu:.3f},0) -- ({apex_x:.3f},{hu:.3f}) -- cycle;" "\n"
        rf"\draw[dashed] ({apex_x:.3f},{hu:.3f}) -- ({apex_x:.3f},0);" "\n"
        + _right_angle(apex_x, 0.0) + "\n"
        rf"\node at ({bu / 2:.3f},{-0.35:.3f}) {{${b}$}};" "\n"
        rf"\node[anchor=west] at ({apex_x + 0.1:.3f},{hu / 2:.3f}) {{${h}$}};"
    )
    return _wrap(body)


def trapezoid_fig(b1: int, b2: int, h: int) -> str:
    u = _scale(b1, b2, h)
    b1u, b2u, hu = b1 * u, b2 * u, h * u
    top_offset = (b1u - b2u) / 2
    body = (
        rf"\draw (0,0) -- ({b1u:.3f},0) -- ({top_offset + b2u:.3f},{hu:.3f}) -- ({top_offset:.3f},{hu:.3f}) -- cycle;" "\n"
        rf"\draw[dashed] ({top_offset:.3f},{hu:.3f}) -- ({top_offset:.3f},0);" "\n"
        + _right_angle(top_offset, 0.0) + "\n"
        rf"\node at ({b1u / 2:.3f},{-0.35:.3f}) {{${b1}$}};" "\n"
        rf"\node at ({top_offset + b2u / 2:.3f},{hu + 0.35:.3f}) {{${b2}$}};" "\n"
        rf"\node[anchor=west] at ({top_offset + 0.1:.3f},{hu / 2:.3f}) {{${h}$}};"
    )
    return _wrap(body)


_ANGLE = math.radians(30)


def rect_prism_fig(l: int, w: int, h: int) -> str:
    """Oblique sketch: front face solid, hidden back-bottom-left edges dashed."""
    u = _scale(l, w, h)
    lu, wu, hu = l * u, w * u, h * u
    du = min(lu, wu, hu) * 0.9  # depth drawn along the diagonal, at a modest length
    dx, dy = du * math.cos(_ANGLE), du * math.sin(_ANGLE)

    fbl, fbr, ftr, ftl = (0, 0), (lu, 0), (lu, hu), (0, hu)
    bbl = (fbl[0] + dx, fbl[1] + dy)
    bbr = (fbr[0] + dx, fbr[1] + dy)
    btr = (ftr[0] + dx, ftr[1] + dy)
    btl = (ftl[0] + dx, ftl[1] + dy)

    def c(p):
        return f"({p[0]:.3f},{p[1]:.3f})"

    body = (
        rf"\draw {c(fbl)} -- {c(fbr)} -- {c(ftr)} -- {c(ftl)} -- cycle;" "\n"
        rf"\draw {c(fbr)} -- {c(bbr)} -- {c(btr)} -- {c(ftr)};" "\n"
        rf"\draw {c(ftl)} -- {c(btl)} -- {c(btr)};" "\n"
        rf"\draw[dashed] {c(fbl)} -- {c(bbl)} -- {c(bbr)};" "\n"
        rf"\draw[dashed] {c(bbl)} -- {c(btl)};" "\n"
        rf"\node at ({lu / 2:.3f},{-0.35:.3f}) {{${l}$}};" "\n"
        rf"\node[anchor=north west] at ({(fbr[0] + bbr[0]) / 2:.3f},{(fbr[1] + bbr[1]) / 2 - 0.1:.3f}) {{${w}$}};" "\n"
        rf"\node[anchor=east] at ({-0.15:.3f},{hu / 2:.3f}) {{${h}$}};"
    )
    return _wrap(body)


def tri_prism_fig(a: int, b: int, c: int, length: int) -> str:
    """Oblique sketch of a right-triangle prism; legs a (base), b (vertical),
    hypotenuse c, and prism length. All four are labeled, since surface-area
    problems need the full triangle perimeter, not just the two legs."""
    u = _scale(a, b, length)
    au, bu, lu = a * u, b * u, length * u
    du = min(au, bu, lu) * 0.9
    dx, dy = du * math.cos(_ANGLE), du * math.sin(_ANGLE)

    f1, f2, f3 = (0, 0), (au, 0), (0, bu)
    b1 = (f1[0] + dx, f1[1] + dy)
    b2 = (f2[0] + dx, f2[1] + dy)
    b3 = (f3[0] + dx, f3[1] + dy)
    hyp_mid = ((f2[0] + f3[0]) / 2, (f2[1] + f3[1]) / 2)

    def c_(p):
        return f"({p[0]:.3f},{p[1]:.3f})"

    body = (
        rf"\draw {c_(f1)} -- {c_(f2)} -- {c_(f3)} -- cycle;" "\n"
        rf"\draw {c_(f2)} -- {c_(b2)} -- {c_(b3)} -- {c_(f3)};" "\n"
        rf"\draw[dashed] {c_(f1)} -- {c_(b1)};" "\n"
        rf"\draw[dashed] {c_(b1)} -- {c_(b2)};" "\n"
        rf"\draw[dashed] {c_(b1)} -- {c_(b3)};" "\n"
        rf"\node at ({au / 2:.3f},{-0.35:.3f}) {{${a}$}};" "\n"
        rf"\node[anchor=east] at ({-0.15:.3f},{bu / 2:.3f}) {{${b}$}};" "\n"
        rf"\node[anchor=south west] at ({hyp_mid[0] + 0.12:.3f},{hyp_mid[1] + 0.05:.3f}) {{${c}$}};" "\n"
        rf"\node[anchor=north west] at ({(f2[0] + b2[0]) / 2:.3f},{(f2[1] + b2[1]) / 2 - 0.1:.3f}) {{${length}$}};"
    )
    return _wrap(body)
