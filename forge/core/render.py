"""LaTeX emission and pdflatex invocation."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List

from jinja2 import Environment, FileSystemLoader, StrictUndefined

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_DIR = ROOT / "templates"


class LatexError(RuntimeError):
    pass


_ESCAPES = {"&": r"\&", "%": r"\%", "#": r"\#"}


def tex_escape(text: str) -> str:
    """Escape the characters that are never intentional in spec prose.

    Spec titles, section names and directions are LaTeX-capable by design --
    "Solve each equation for $x$" must keep its inline math -- so ``$``, braces
    and backslashes pass through untouched. Only ``&``, ``%`` and ``#``, which
    can only ever be typos in prose, are escaped. Problem and answer bodies are
    never escaped: generators emit LaTeX there by contract.
    """
    out = str(text)
    for ch, rep in _ESCAPES.items():
        out = out.replace(ch, rep)
    return out


def _env(template_dir: Path = TEMPLATE_DIR) -> Environment:
    # LaTeX-safe delimiters: {{ }} and {% %} collide with braces everywhere.
    return Environment(
        loader=FileSystemLoader(str(template_dir)),
        variable_start_string="(((",
        variable_end_string=")))",
        block_start_string="((*",
        block_end_string="*))",
        comment_start_string="((=",
        comment_end_string="=))",
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )


def render_tex(
    title: str,
    sections: List[dict],
    include_key: bool,
    template: str = "worksheet.tex.j2",
    template_dir: Path = TEMPLATE_DIR,
) -> str:
    """Render the .tex source. ``sections`` holds dicts of rendered Problems."""
    env = _env(template_dir)
    env.filters["tex"] = tex_escape
    tmpl = env.get_template(template)
    # The header sits opposite the Name rule, so it must stay short enough to
    # never wrap into it. The combined teacher-key PDF carries the problems and
    # the key in one document, so it needs *two* running headers -- a plain
    # student header for the problem pages, and a "--- Teacher Key" header that
    # only takes effect once the key's \newpage is reached (see the template:
    # \fancyhead[L] is redefined right at that boundary, never issued twice
    # up front, so it cannot retroactively affect the earlier pages).
    student_budget = 46
    key_budget = 38

    def _fit(budget: int) -> str:
        return title if len(title) <= budget else title[: budget - 3].rstrip() + "..."

    header_student = _fit(student_budget)
    header_key = _fit(key_budget) + " --- Teacher Key"
    return tmpl.render(
        header_left=header_student,
        header_left_key=header_key,
        sections=sections,
        include_key=include_key,
    )


def compile_pdf(tex_source: str, out_pdf: Path) -> Path:
    """Compile with pdflatex (twice, for the page-count in the footer)."""
    if shutil.which("pdflatex") is None:
        raise LatexError(
            "pdflatex not found on PATH. Install a TeX distribution (MacTeX/TeX Live) "
            "or run with --no-pdf to emit .tex only."
        )
    out_pdf = Path(out_pdf)
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    stem = out_pdf.stem

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        (tmp / f"{stem}.tex").write_text(tex_source)
        for _ in range(2):
            proc = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", f"{stem}.tex"],
                cwd=tmp,
                capture_output=True,
                text=True,
            )
            if proc.returncode != 0:
                log = (tmp / f"{stem}.log")
                tail = log.read_text(errors="replace")[-3000:] if log.exists() else proc.stdout[-3000:]
                (out_pdf.parent / f"{stem}.failed.tex").write_text(tex_source)
                raise LatexError(
                    f"pdflatex failed for {stem}. Source kept at "
                    f"{out_pdf.parent / f'{stem}.failed.tex'}\n{tail}"
                )
        shutil.copy(tmp / f"{stem}.pdf", out_pdf)
    return out_pdf
