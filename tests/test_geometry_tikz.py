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

import random
import shutil

import pytest

from forge.core.problem import DIFFICULTIES
from forge.core.registry import all_generators
from forge.core.render import compile_pdf, render_tex
from forge.core.verify import verify_all

FUZZ_RANGE = 1000
STRIDE = 17  # ~59 seeds per subskill, spread across the whole fuzz range

GEOMETRY_SUBSKILLS = (
    "area_rectangle", "area_square", "area_triangle", "area_trapezoid",
    "volume_rect_prism", "surface_area_rect_prism",
    "volume_tri_prism", "surface_area_tri_prism",
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
