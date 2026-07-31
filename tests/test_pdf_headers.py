"""Regression test for the running header on the combined teacher-key PDF.

The key PDF is one document: problem pages, then a \\newpage, then the
answer key. The header must switch at that boundary -- "Teacher Key" may
never appear on a student problem page, and must appear on every key page.
This is checked by extracting real per-page text with ``pdftotext``, not by
eyeballing a render or asserting on the template source.
"""

from __future__ import annotations

import re
import shutil
import subprocess

import pytest

from forge.build import build
from forge.core.sampling import NullLedger

pytestmark = pytest.mark.skipif(
    shutil.which("pdflatex") is None
    or shutil.which("pdftotext") is None
    or shutil.which("pdfinfo") is None,
    reason="pdflatex/pdftotext/pdfinfo not installed",
)


def _page_count(pdf_path) -> int:
    info = subprocess.run(["pdfinfo", str(pdf_path)], capture_output=True, text=True).stdout
    m = re.search(r"Pages:\s+(\d+)", info)
    assert m, f"couldn't read page count from pdfinfo output:\n{info}"
    return int(m.group(1))


def _page_text(pdf_path, page: int) -> str:
    return subprocess.run(
        ["pdftotext", "-f", str(page), "-l", str(page), str(pdf_path), "-"],
        capture_output=True, text=True,
    ).stdout


def test_teacher_key_header_only_appears_from_the_key_onward(spec_path, tmp_path):
    paths = build(spec_path, seed=42, out_dir=tmp_path, ledger=NullLedger())
    pdf = paths["key_pdf"]
    pages = _page_count(pdf)
    assert pages >= 2, "expected the combined PDF to have problem pages plus a key page"

    page_texts = [_page_text(pdf, i) for i in range(1, pages + 1)]

    key_start = next((i for i, t in enumerate(page_texts, start=1) if "Answer Key" in t), None)
    assert key_start is not None, "never found the 'Answer Key' section in any page"
    assert key_start > 1, "the key must not start on page 1 -- there should be problem pages first"

    report = []
    for i, text in enumerate(page_texts, start=1):
        has_teacher_key = "Teacher Key" in text
        report.append((i, has_teacher_key))
        if i < key_start:
            assert not has_teacher_key, (
                f"page {i} is before the answer key (which starts on page {key_start}) "
                f"but its header says 'Teacher Key':\n{text[:200]}"
            )
        else:
            assert has_teacher_key, (
                f"page {i} is on or after the answer key (page {key_start}) but its "
                f"header is missing 'Teacher Key':\n{text[:200]}"
            )

    # Every page -- key or not -- keeps the Name line for the student to fill in.
    for i, text in enumerate(page_texts, start=1):
        assert "Name:" in text, f"page {i} is missing the Name: header"
