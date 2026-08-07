"""worksheet-forge command line interface."""

from __future__ import annotations

import argparse
import random
import shutil
import string
import sys
from datetime import datetime
from pathlib import Path

import yaml

from .build import build
from .catalog import DEFAULT_COUNT, describe_topics, spec_from_topics
from .core.render import LatexError
from .core.sampling import DEFAULT_HISTORY, DEFAULT_LOOKBACK, Ledger, NullLedger
from .core.verify import VerificationError

ROOT = Path(__file__).resolve().parents[1]


def _resolve_out(args: argparse.Namespace) -> Path:
    """Each run gets its own out/<timestamp>/ folder unless --out is given."""
    if args.out:
        return Path(args.out)
    return ROOT / "out" / datetime.now().strftime("%Y-%m-%d_%I-%M-%S-%p")


def _run(args: argparse.Namespace, spec_path: Path) -> int:
    ledger = (
        NullLedger()
        if args.no_history
        else Ledger(path=Path(args.history), lookback=args.lookback)
    )
    base_seed = args.seed if args.seed is not None else random.randrange(1, 10**9)
    out_dir = _resolve_out(args)

    for i in range(args.versions):
        # Fully independent draws per version: a distinct seed, nothing shared.
        seed = base_seed + i * 7919
        label = string.ascii_uppercase[i] if args.versions > 1 else ""
        paths = build(
            spec_path=spec_path,
            seed=seed,
            out_dir=out_dir,
            label=label,
            ledger=ledger,
            make_pdf=not args.no_pdf,
            allow_download=not args.no_download,
        )
        ws = paths["worksheet"]
        tag = f"version {label} " if label else ""
        print(f"{tag}seed={seed}  {len(ws.problems)} problems, all verified")
        for key in ("key_pdf", "key_tex"):
            if key in paths:
                print(f"  {key:12s} {paths[key]}")
    return 0


def _build_cmd(args: argparse.Namespace) -> int:
    return _run(args, Path(args.spec))


def _quick_cmd(args: argparse.Namespace) -> int:
    """Type a list of topics, get a worksheet -- no YAML to write."""
    tokens = []
    for chunk in args.topics:
        tokens.extend(t for t in chunk.replace(",", " ").split() if t)

    spec = spec_from_topics(
        tokens,
        title=args.title or "",
        header=args.header or "",
        difficulty=args.difficulty or "",
    )

    # Refuse a taken delivery slot before writing or building anything.
    prepared = _prepare_delivery(args, args.deliver_to) if args.deliver_to else None
    if args.deliver_to and prepared is None:
        return 1

    out_dir = _resolve_out(args)
    args.out = str(out_dir)  # so _run resolves to this same folder, not a new timestamp
    out_dir.mkdir(parents=True, exist_ok=True)
    # The generated spec is written out so a good worksheet can be rebuilt,
    # edited, or committed later.
    spec_path = Path(args.save) if args.save else out_dir / f"{args.name}.yaml"
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.write_text(yaml.safe_dump(spec, sort_keys=False, width=100))
    print(f"spec  {spec_path}")

    rc = _run(args, spec_path)
    if rc != 0 or not prepared:
        return rc

    # The filed spec is the one that gets kept, so the staged copy is scratch.
    _file_delivery(args, spec_path, out_dir, *prepared)
    return 0


WORKSHEETS = ROOT / "tutor" / "worksheets"


def _prepare_delivery(args: argparse.Namespace, student: str):
    """Settle where a delivery will land, and refuse early if it is taken.

    Returns ``(dest, stem)``, or ``None`` when the target already exists --
    checked *before* building, so a refusal costs no compile.
    """
    date = args.date or datetime.now().strftime("%Y-%m-%d")
    # Each delivery is self-contained in its own dated folder so multiple
    # worksheets and all of their companion artifacts never mingle.
    dest = WORKSHEETS / student / date
    stem = f"{date}_{student.split('_')[0]}"

    final_pdf = dest / f"{stem}.pdf"
    if final_pdf.exists() and not args.force:
        print(f"REFUSING to overwrite {final_pdf} (pass --force)", file=sys.stderr)
        return None

    # The ledger shifts draws between runs, so a delivered sheet built against
    # it stops reproducing from its seed. Never optional here.
    args.no_history = True
    args.versions = 1
    args.no_pdf = False
    if args.seed is None:
        args.seed = random.randrange(1, 10**9)
    return dest, stem


def _file_delivery(args, spec_path: Path, out_dir: Path, dest: Path, stem: str) -> None:
    """Copy the built trio out of staging and into its dated folder."""
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(next(out_dir.glob("*_key.pdf")), dest / f"{stem}.pdf")
    shutil.copy2(next(out_dir.glob("*_key.tex")), dest / f"{stem}_key.tex")

    # Persist the seed into the filed spec so the sheet is reproducible from
    # the folder alone -- without it the seed lives only in a console line.
    spec = yaml.safe_load(spec_path.read_text())
    spec["seed"] = args.seed
    (dest / f"{stem}_spec.yaml").write_text(
        yaml.safe_dump(spec, sort_keys=False, width=100)
    )

    print(f"\ndelivered to {dest}")
    for suffix in (".pdf", "_key.tex", "_spec.yaml"):
        print(f"  {stem}{suffix}")
    print(f"reproduce with: forge build {dest / f'{stem}_spec.yaml'} "
          f"--seed {args.seed} --no-history")


def _deliver_cmd(args: argparse.Namespace) -> int:
    """Build a worksheet and file it for a student in one step.

    Three conventions used to live only in CLAUDE.md, and all three were broken
    the first time an agent followed the prose: build with ``--no-history`` so
    the seed alone reproduces the sheet, write the trio (spec, key .tex, PDF)
    into ``tutor/worksheets/<Student>/<YYYY-MM-DD>/``, and leave nothing behind
    in ``out/``.
    This command is the executable version of that paragraph.
    """
    prepared = _prepare_delivery(args, args.student)
    if prepared is None:
        return 1
    dest, stem = prepared

    # Pin the staging dir before building: _resolve_out stamps a fresh
    # timestamp on every call, so asking for it twice yields two directories.
    out_dir = _resolve_out(args)
    args.out = str(out_dir)

    spec_path = Path(args.spec)
    rc = _run(args, spec_path)
    if rc != 0:
        return rc

    _file_delivery(args, spec_path, out_dir, dest, stem)
    return 0


def _topics_cmd(args: argparse.Namespace) -> int:
    print("Available topics (use topic, topic:count, or topic:count:difficulty):\n")
    print(describe_topics())
    print(f"\nDefault count per topic: {DEFAULT_COUNT}. Difficulties: easy, medium, hard.")
    print("Target subskills with topic/subskill, joining several with '+':")
    print("  forge quick slope/slope_from_two_points+equation_from_two_points:12")
    return 0


def _add_common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--seed", type=int, default=None, help="seed (random if omitted)")
    p.add_argument("--versions", type=int, default=1, help="number of A/B/C variants")
    p.add_argument("--out", default="",
                   help="output directory (default: a fresh out/<timestamp>/ per run)")
    p.add_argument("--history", default=str(DEFAULT_HISTORY))
    p.add_argument("--lookback", type=int, default=DEFAULT_LOOKBACK,
                   help="reject fingerprints used in the last N runs")
    p.add_argument("--no-history", action="store_true",
                   help="ignore and do not update the anti-repeat ledger")
    p.add_argument("--no-pdf", action="store_true", help="emit .tex only")
    p.add_argument("--no-download", action="store_true",
                   help="never auto-download a LaTeX compiler; fail if none is found")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="forge")
    sub = parser.add_subparsers(dest="command", required=True)

    b = sub.add_parser("build", help="build worksheets from a YAML spec")
    b.add_argument("spec", help="path to a YAML spec")
    _add_common(b)
    b.set_defaults(func=_build_cmd)

    q = sub.add_parser(
        "quick",
        help="build a worksheet from a list of topics, no spec file needed",
        description=(
            "Examples:\n"
            "  forge quick negatives fractions linear_equations:12:hard\n"
            "  forge quick slope/slope_from_two_points:10\n"
            "  forge quick exponents/product_rule+quotient_rule:12:hard"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    q.add_argument("topics", nargs="+",
                   help=("topics, optionally topic:count or topic:count:difficulty; "
                         "add /subskill (or /sub1+sub2) to target subskills"))
    q.add_argument("--title", default="", help="worksheet title")
    q.add_argument("--header", default="", help="short header text")
    q.add_argument("--difficulty", default="", choices=["", "easy", "medium", "hard"],
                   help="override the difficulty of every section")
    q.add_argument("--name", default="quick", help="basename for the generated spec")
    q.add_argument("--save", default="", help="write the generated spec here")
    q.add_argument("--deliver-to", default="", metavar="STUDENT",
                   help=("file the result under tutor/worksheets/STUDENT/DATE/ as a "
                         "delivered worksheet, exactly as `forge deliver` would"))
    q.add_argument("--date", default="", help="YYYY-MM-DD for --deliver-to (default: today)")
    q.add_argument("--force", action="store_true",
                   help="with --deliver-to, overwrite an existing sheet for that date")
    _add_common(q)
    q.set_defaults(func=_quick_cmd)

    d = sub.add_parser(
        "deliver",
        help="build a worksheet and file it under tutor/worksheets/<Student>/<Date>/",
        description=(
            "Examples:\n"
            "  forge deliver specs/rachel.yaml --student Rachel_Math\n"
            "  forge deliver specs/rachel.yaml --student Rachel_Math --seed 806"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    d.add_argument("spec", help="path to a YAML spec")
    d.add_argument("--student", required=True,
                   help="folder name under tutor/worksheets/, e.g. Rachel_Math")
    d.add_argument("--date", default="", help="YYYY-MM-DD (default: today)")
    d.add_argument("--force", action="store_true",
                   help="overwrite an already-delivered sheet for this date")
    _add_common(d)
    d.set_defaults(func=_deliver_cmd)

    t = sub.add_parser("topics", help="list available topics and subskills")
    t.set_defaults(func=_topics_cmd)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (KeyError, ValueError) as e:
        print(f"BUILD FAILED - bad request: {e}", file=sys.stderr)
        return 1
    except VerificationError as e:
        print(f"BUILD FAILED - answer verification:\n{e}", file=sys.stderr)
        return 2
    except LatexError as e:
        print(f"BUILD FAILED - LaTeX:\n{e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
