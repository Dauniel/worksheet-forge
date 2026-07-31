"""Per-section column control: multicols wiring, defaults, and the figure guard."""

from __future__ import annotations

import re
import shutil
import subprocess
import warnings

import pytest

from forge.build import generate, load_spec
from forge.core.sampling import NullLedger


def _spec(sections):
    return {"title": "Column Test", "sections": sections}


def test_default_section_has_no_multicols():
    spec = _spec([
        {
            "name": "Part A",
            "directions": "Evaluate.",
            "workspace": "1.1cm",
            "problems": [{"topic": "negatives", "subskill": "order_of_operations",
                          "count": 4, "difficulty": "easy"}],
        },
    ])
    ws = generate(spec, seed=1)
    assert r"\begin{multicols}" not in ws.student_tex
    assert ws.sections[0]["columns"] == 1


def test_columns_key_emits_multicols():
    spec = _spec([
        {
            "name": "Part A",
            "directions": "Evaluate.",
            "workspace": "1.1cm",
            "columns": 2,
            "problems": [{"topic": "negatives", "subskill": "order_of_operations",
                          "count": 10, "difficulty": "easy"}],
        },
    ])
    ws = generate(spec, seed=1)
    assert r"\begin{multicols}{2}" in ws.student_tex
    assert r"\end{multicols}" in ws.student_tex
    assert ws.sections[0]["columns"] == 2
    # The section's own enumerate is inside the multicols, not the (still
    # hardcoded, 3-column) answer key -- check ordering, not just presence.
    mc_pos = ws.student_tex.index(r"\begin{multicols}{2}")
    enum_pos = ws.student_tex.index(r"\begin{enumerate}")
    assert mc_pos < enum_pos


def test_numbering_is_sequential_and_continuous_across_the_column_break():
    """LaTeX's enumerate counter doesn't reset at a column break, but this
    confirms the *source* only ever opens one enumerate per section (no
    \\begin{enumerate} split per column, no resetenumerate/setcounter), which
    is what continuous numbering here actually depends on."""
    spec = _spec([
        {
            "name": "Part A",
            "directions": "Evaluate.",
            "workspace": "1.1cm",
            "columns": 2,
            "problems": [{"topic": "negatives", "subskill": "order_of_operations",
                          "count": 20, "difficulty": "easy"}],
        },
    ])
    ws = generate(spec, seed=1)
    assert ws.student_tex.count(r"\begin{enumerate}") == 1
    assert ws.student_tex.count(r"\end{enumerate}") == 1
    assert "resetenumerate" not in ws.student_tex
    assert r"\setcounter{enumi}" not in ws.student_tex
    # Exactly 20 items inside that one list.
    assert ws.student_tex.count(r"\item ") - ws.student_tex.count(r"\item[") >= 20


def test_geometry_sections_are_never_two_column():
    """Every default geometry subskill renders a TikZ figure; the catalog
    must default it to 1 column, regardless of count/difficulty."""
    from forge.catalog import spec_from_topics

    spec = spec_from_topics(["geometry:16"])
    for sec in spec["sections"]:
        assert sec.get("columns", 1) == 1, f"{sec['name']} defaulted to >1 column"


def test_figure_bearing_section_forced_to_one_column_even_if_spec_asks_for_two():
    """A hand-written spec that (mistakenly) asks for 2 columns on a
    TikZ-figure section gets overridden, with a warning, not silently
    honoured or a hard crash."""
    spec = _spec([
        {
            "name": "Part L: Area",
            "directions": "Find the area of each figure.",
            "workspace": "1.6cm",
            "columns": 2,
            "problems": [{"topic": "geometry", "subskill": "area_square",
                          "count": 3, "difficulty": "easy"}],
        },
    ])
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        ws = generate(spec, seed=1)
        assert any("column" in str(w.message).lower() for w in caught)
    assert ws.sections[0]["columns"] == 1
    assert r"\begin{multicols}" not in ws.student_tex


def test_catalog_two_column_defaults_for_short_symbolic_topics():
    from forge.catalog import spec_from_topics

    for token in ("negatives:8", "fractions:8", "exponents:8", "roots:8",
                  "inequalities:8", "linear_equations:8", "number_sense:8"):
        spec = spec_from_topics([token])
        assert all(sec.get("columns", 1) == 2 for sec in spec["sections"]), (
            f"{token}: expected every section to default to 2 columns"
        )


def test_catalog_one_column_defaults_for_prose_topics():
    from forge.catalog import spec_from_topics

    for token in ("word_problems:8", "unit_rates:8"):
        spec = spec_from_topics([token])
        assert all(sec.get("columns", 1) == 1 for sec in spec["sections"]), (
            f"{token}: expected every section to default to 1 column"
        )

    # percent_apps mixes a short symbolic part (percent_proportion) with
    # several full-sentence parts -- only the symbolic one is 2-column.
    spec = spec_from_topics(["percent_apps:24"])
    for sec in spec["sections"]:
        subskills = {p["subskill"] for p in sec["problems"]}
        if "percent_proportion" in subskills:
            assert sec.get("columns", 1) == 2
        else:
            assert sec.get("columns", 1) == 1


@pytest.mark.skipif(
    shutil.which("pdflatex") is None, reason="pdflatex not installed",
)
def test_two_column_build_compiles(tmp_path):
    """A real multicols + enumerate + (separately) TikZ interaction, compiled
    once, so a regression here fails in CI rather than only at build time."""
    from forge.core.render import compile_pdf

    spec = _spec([
        {
            "name": "Part A: Short Symbolic",
            "directions": "Evaluate each expression.",
            "workspace": "1.1cm",
            "columns": 2,
            "problems": [{"topic": "negatives", "subskill": "order_of_operations",
                          "count": 20, "difficulty": "medium"}],
        },
        {
            "name": "Part B: Geometry (forced single column)",
            "directions": "Find the area of each figure.",
            "workspace": "1.6cm",
            "columns": 2,  # deliberately wrong, to exercise the guard end-to-end
            "problems": [{"topic": "geometry", "subskill": "area_triangle",
                          "count": 4, "difficulty": "easy"}],
        },
    ])
    ws = generate(spec, seed=7, ledger=NullLedger())
    pdf = compile_pdf(ws.key_tex, tmp_path / "columns_smoke.pdf")
    assert pdf.exists()
    assert pdf.stat().st_size > 10_000
