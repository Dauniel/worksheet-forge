"""Spec-level guarantees: quotas, uniqueness, determinism, and the PDFs."""

from __future__ import annotations

import shutil
from collections import Counter

import pytest

from forge.build import build, generate, load_spec
from forge.core.sampling import NullLedger
from forge.core.verify import VerificationError, verify_all


def test_quotas_are_enforced_exactly(spec_path):
    spec = load_spec(spec_path)
    ws = generate(spec, seed=99)
    got = Counter((p.topic, p.subskill) for p in ws.problems)
    want = Counter()
    for sec in spec["sections"]:
        for req in sec["problems"]:
            want[(req["topic"], req["subskill"])] += req["count"]
    assert got == want


def test_no_duplicate_fingerprints_within_a_worksheet(spec_path):
    spec = load_spec(spec_path)
    for seed in (1, 2, 3, 17, 500):
        ws = generate(spec, seed=seed)
        fps = [p.fingerprint for p in ws.problems]
        assert len(fps) == len(set(fps)), f"seed {seed} repeated a problem"


def test_same_seed_is_byte_identical(spec_path):
    spec = load_spec(spec_path)
    a = generate(spec, seed=2024)
    b = generate(spec, seed=2024)
    assert a.key_tex == b.key_tex
    assert a.student_tex == b.student_tex


def test_different_seeds_differ(spec_path):
    spec = load_spec(spec_path)
    assert generate(spec, seed=1).student_tex != generate(spec, seed=2).student_tex


def test_every_answer_is_verified(spec_path):
    spec = load_spec(spec_path)
    ws = generate(spec, seed=7)
    verify_all(ws.problems)  # raises on any mismatch


def test_a_wrong_key_fails_the_build(spec_path):
    """Sabotage one answer and confirm verification catches it."""
    import dataclasses

    spec = load_spec(spec_path)
    ws = generate(spec, seed=7)
    bad = dataclasses.replace(ws.problems[0], answer_expr=ws.problems[0].answer_expr + 1)
    with pytest.raises(VerificationError):
        verify_all([bad])


def test_student_copy_contains_no_answers(spec_path):
    spec = load_spec(spec_path)
    ws = generate(spec, seed=11)
    assert "Answer Key" not in ws.student_tex
    assert "Answer Key" in ws.key_tex
    for p in ws.problems:
        assert p.question_latex in ws.student_tex


def test_teacher_copy_states_each_problem_exactly_once(spec_path):
    """The teacher copy IS the deliverable -- problems once, then the key.

    It already contains every problem, so concatenating it onto the student
    copy to make a "combined" hand-out prints the whole worksheet twice.
    That shipped once. Nothing downstream should ever need to merge the two
    PDFs: student_tex is the clean copy, key_tex is the copy with the key.
    """
    spec = load_spec(spec_path)
    ws = generate(spec, seed=5)
    body = ws.key_tex.split("Answer Key")[0]
    for p in ws.problems:
        assert body.count(p.question_latex) == 1, (
            f"{p.topic}/{p.subskill}: question appears "
            f"{body.count(p.question_latex)} times in the teacher copy body"
        )
    # The name recurs once more as the key's \subsection* per part, which is
    # the documented layout -- so this counts the problem body only.
    for sec in spec["sections"]:
        assert body.count(sec["name"]) == 1, f"{sec['name']} appears twice"
        assert ws.student_tex.count(sec["name"]) == 1


def test_no_title_block_and_no_newpage_between_sections(spec_path):
    spec = load_spec(spec_path)
    ws = generate(spec, seed=3)
    for banned in (r"\maketitle", r"\title{", r"\author", r"\date{"):
        assert banned not in ws.student_tex
    # The only \newpage in the teacher copy is the one before the key.
    assert ws.student_tex.count(r"\newpage") == 0
    assert ws.key_tex.count(r"\newpage") == 1


def test_workspace_follows_every_item(spec_path):
    spec = load_spec(spec_path)
    ws = generate(spec, seed=3)
    workspaces = {sec.get("workspace", "1.1cm") for sec in spec["sections"]}
    for w in workspaces:
        assert rf"\vspace{{{w}}}" in ws.student_tex
    assert ws.student_tex.count(r"\vspace{") == len(ws.problems)


@pytest.mark.skipif(shutil.which("pdflatex") is None, reason="pdflatex not installed")
def test_end_to_end_pdfs(spec_path, tmp_path):
    paths = build(spec_path, seed=42, out_dir=tmp_path, ledger=NullLedger())
    pdf = paths["key_pdf"]
    assert pdf.exists(), "key_pdf was not written"
    assert pdf.stat().st_size > 10_000, "key_pdf is suspiciously small"


def test_build_emits_exactly_one_tex_and_one_pdf(spec_path, tmp_path):
    """A worksheet is one document: problems, then the key the student checks against.

    The answer-free copy was emitted alongside it for a while, which made every
    build four files and left the filing rule ambiguous about which PDF counted.
    """
    paths = build(spec_path, seed=42, out_dir=tmp_path, ledger=NullLedger(),
                  make_pdf=False)
    assert set(paths) == {"key_tex", "worksheet"}
    assert not list(tmp_path.glob("*student*"))
    assert [p.name for p in tmp_path.glob("*.tex")] == [paths["key_tex"].name]


def test_empty_section_fails_loudly():
    """A section with no resolvable problems must not build a broken PDF.

    Rendering one emits an empty ``enumerate``, which LaTeX rejects with a
    "missing \\item" error pointing at a line the spec author never wrote.
    """
    spec = {
        "title": "Empty",
        "sections": [{"name": "Part A: Nothing", "directions": "Evaluate."}],
    }
    with pytest.raises(ValueError, match="no problems"):
        generate(spec, seed=1, ledger=NullLedger())
