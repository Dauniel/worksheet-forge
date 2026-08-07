"""Geometry figures are TikZ, not prose: make sure they actually compile.

The generator fuzz suite (test_generators.py) checks that every geometry
problem verifies correctly across 1000 seeds, but verification never touches
pdflatex -- a bad brace or a stray token in a TikZ picture would only surface
the first time someone actually builds a PDF. This test renders a real,
compilable document containing a wide, evenly-spaced sample of the same
1000-seed fuzz range (every subskill, every difficulty) and compiles it once,
so a TikZ regression fails in CI, not on a tutor's laptop at seed 743.
"""

from __future__ import annotations

import dataclasses
import random
import re
import shutil

import pytest
import sympy as sp

from forge.core.problem import DIFFICULTIES
from forge.core.registry import all_generators
from forge.core.render import compile_pdf, render_tex
from forge.core.verify import VerificationError, verify_all

FUZZ_RANGE = 1000
STRIDE = 17  # ~59 seeds per subskill, spread across the whole fuzz range

# Every geometry subskill belongs here -- this list is what the compile smoke
# test actually renders, so a subskill missing from it is a subskill whose
# TikZ nobody checks.
GEOMETRY_SUBSKILLS = (
    "area_rectangle", "area_square", "area_triangle", "area_trapezoid",
    "area_circle", "circumference_circle",
    "volume_rect_prism", "surface_area_rect_prism",
    "volume_tri_prism", "surface_area_tri_prism",
)


def test_every_geometry_subskill_is_in_the_smoke_test():
    """Guards the list above from silently falling behind the registry."""
    registered = {sub for topic, sub in all_generators() if topic == "geometry"}
    assert registered == set(GEOMETRY_SUBSKILLS), (
        f"missing from smoke test: {sorted(registered - set(GEOMETRY_SUBSKILLS))}"
    )


def _sample_problems():
    gens = all_generators()
    sections = []
    all_problems = []
    for subskill in GEOMETRY_SUBSKILLS:
        gen = gens[("geometry", subskill)]
        items = [
            gen(random.Random(seed), DIFFICULTIES[seed % len(DIFFICULTIES)])
            for seed in range(0, FUZZ_RANGE, STRIDE)
        ]
        sections.append({
            "name": f"Geometry: {subskill.replace('_', ' ')}",
            "directions": "Find the requested measurement.",
            "workspace": "1.6cm",
            "columns": 1,
            "problems": items,
        })
        all_problems.extend(items)
    return sections, all_problems


def test_geometry_figures_verify_across_the_fuzz_range():
    _, problems = _sample_problems()
    assert len(problems) >= 400
    verify_all(problems)  # raises VerificationError on any mismatch


@pytest.mark.skipif(shutil.which("pdflatex") is None, reason="pdflatex not installed")
def test_geometry_tikz_compiles_across_the_fuzz_range(tmp_path):
    sections, problems = _sample_problems()
    verify_all(problems)
    tex = render_tex("Geometry TikZ Smoke Test", sections, include_key=False)
    pdf = compile_pdf(tex, tmp_path / "geometry_tikz_smoke.pdf")
    assert pdf.exists()
    assert pdf.stat().st_size > 10_000


def test_circle_figures_label_which_dimension_they_show():
    """A bare number would leave the picture ambiguous to reader and verifier."""
    fn = all_generators()[("geometry", "area_circle")]
    seen = set()
    for i in range(200):
        q = fn(random.Random(i), "medium").question_latex
        m = re.search(r"([rd]) = (\d+)", q)
        assert m, "circle figure must label r or d"
        seen.add(m.group(1))
    assert seen == {"r", "d"}, f"both cases should appear, saw {seen}"


def test_circle_diameters_are_always_even():
    """An odd diameter would make the radius fractional and the answer ugly."""
    for sub in ("area_circle", "circumference_circle"):
        fn = all_generators()[("geometry", sub)]
        for diff in ("easy", "medium", "hard"):
            for i in range(150):
                q = fn(random.Random(i), diff).question_latex
                m = re.search(r"d = (\d+)", q)
                if m:
                    assert int(m.group(1)) % 2 == 0, f"{sub}/{diff}: odd diameter"


def test_circle_answers_are_exact_multiples_of_pi():
    """No decimals: the answer stays symbolic so it is exactly checkable."""
    for sub in ("area_circle", "circumference_circle"):
        fn = all_generators()[("geometry", sub)]
        for i in range(150):
            p = fn(random.Random(i), "hard")
            coeff = p.answer_expr / sp.pi
            assert coeff.is_Integer, f"{sub}: {p.answer_expr} is not an integer times pi"


def test_circle_verifier_catches_a_wrong_area():
    """The diameter case is the one a student (or a bug) gets wrong."""
    fn = all_generators()[("geometry", "area_circle")]
    p = next(
        fn(random.Random(i), "medium")
        for i in range(100)
        if "d = " in fn(random.Random(i), "medium").question_latex
    )
    # Squaring the printed diameter instead of halving it first.
    d = sp.Integer(re.search(r"d = (\d+)", p.question_latex).group(1))
    wrong = dataclasses.replace(p, answer_expr=sp.pi * d**2)
    with pytest.raises(VerificationError):
        verify_all([wrong])
