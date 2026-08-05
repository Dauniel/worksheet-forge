"""Spec -> problems -> verified -> .tex -> PDF."""

from __future__ import annotations

import random
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import yaml

from .core.problem import Problem
from .core.render import compile_pdf, render_tex
from .core.sampling import Ledger, NullLedger, draw
from .core.verify import verify_all

DEFAULT_WORKSPACE = "1.1cm"
DEFAULT_COLUMNS = 1


def _contains_figure(problems: List[Problem]) -> bool:
    """A TikZ figure needs the full text width; it can never share a column."""
    return any("tikzpicture" in p.question_latex for p in problems)


@dataclass
class BuiltWorksheet:
    title: str
    seed: int
    sections: List[dict]
    problems: List[Problem]
    key_tex: str
    student_tex: str


def load_spec(path: Path) -> dict:
    spec = yaml.safe_load(Path(path).read_text())
    if not spec or "sections" not in spec:
        raise ValueError(f"{path}: spec needs a top-level 'sections' list")
    return spec


def generate(spec: dict, seed: int, ledger: Optional[Ledger] = None) -> BuiltWorksheet:
    """Sample and verify every problem. Raises before any rendering on mismatch."""
    ledger = ledger if ledger is not None else NullLedger()
    rng = random.Random(seed)
    blocked = ledger.blocked
    seen: set = set()

    sections: List[dict] = []
    all_problems: List[Problem] = []

    for sec in spec["sections"]:
        items: List[Problem] = []
        for req in sec.get("problems", []):
            count = int(req.get("count", 1))
            items.extend(
                draw(
                    rng,
                    topic=req["topic"],
                    subskill=req["subskill"],
                    difficulty=req.get("difficulty", "medium"),
                    count=count,
                    blocked=blocked,
                    seen=seen,
                )
            )
        columns = int(sec.get("columns", DEFAULT_COLUMNS) or DEFAULT_COLUMNS)
        if columns > 1 and _contains_figure(items):
            warnings.warn(
                f"section {sec['name']!r} requested {columns} columns but "
                "contains a TikZ figure, which needs the full text width; "
                "forcing 1 column.",
                stacklevel=2,
            )
            columns = 1

        sections.append(
            {
                "name": sec["name"],
                "directions": sec.get("directions", ""),
                "workspace": sec.get("workspace", DEFAULT_WORKSPACE),
                "columns": columns,
                "problems": items,
            }
        )
        all_problems.extend(items)

    # Nothing renders until every answer has been independently re-derived.
    verify_all(all_problems)

    title = spec.get("title", "Worksheet")
    # Optional short header, for when the title is too long for the header rule.
    header = spec.get("header", title)
    return BuiltWorksheet(
        title=title,
        seed=seed,
        sections=sections,
        problems=all_problems,
        key_tex=render_tex(header, sections, include_key=True),
        student_tex=render_tex(header, sections, include_key=False),
    )


def build(
    spec_path: Path,
    seed: int,
    out_dir: Path,
    label: str = "",
    ledger: Optional[Ledger] = None,
    make_pdf: bool = True,
    allow_download: bool = True,
) -> dict:
    spec = load_spec(spec_path)
    ws = generate(spec, seed, ledger=ledger)

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(spec_path).stem + (f"_{label}" if label else "") + f"_seed{seed}"

    paths = {}
    for kind, source in (("key", ws.key_tex), ("student", ws.student_tex)):
        tex_path = out_dir / f"{stem}_{kind}.tex"
        tex_path.write_text(source)
        paths[f"{kind}_tex"] = tex_path
        if make_pdf:
            paths[f"{kind}_pdf"] = compile_pdf(
                source, out_dir / f"{stem}_{kind}.pdf", allow_download=allow_download
            )

    if ledger is not None:
        ledger.record(p.fingerprint for p in ws.problems)

    paths["worksheet"] = ws
    return paths
