"""worksheet-forge command line interface."""

from __future__ import annotations

import argparse
import random
import string
import sys
from pathlib import Path

import yaml

from .build import build
from .catalog import DEFAULT_COUNT, describe_topics, spec_from_topics
from .core.render import LatexError
from .core.sampling import DEFAULT_HISTORY, DEFAULT_LOOKBACK, Ledger, NullLedger
from .core.verify import VerificationError

ROOT = Path(__file__).resolve().parents[1]


def _run(args: argparse.Namespace, spec_path: Path) -> int:
    ledger = (
        NullLedger()
        if args.no_history
        else Ledger(path=Path(args.history), lookback=args.lookback)
    )
    base_seed = args.seed if args.seed is not None else random.randrange(1, 10**9)

    for i in range(args.versions):
        # Fully independent draws per version: a distinct seed, nothing shared.
        seed = base_seed + i * 7919
        label = string.ascii_uppercase[i] if args.versions > 1 else ""
        paths = build(
            spec_path=spec_path,
            seed=seed,
            out_dir=Path(args.out),
            label=label,
            ledger=ledger,
            make_pdf=not args.no_pdf,
        )
        ws = paths["worksheet"]
        tag = f"version {label} " if label else ""
        print(f"{tag}seed={seed}  {len(ws.problems)} problems, all verified")
        for key in ("key_pdf", "student_pdf", "key_tex", "student_tex"):
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

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    # The generated spec is written out so a good worksheet can be rebuilt,
    # edited, or committed later.
    spec_path = Path(args.save) if args.save else out_dir / f"{args.name}.yaml"
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.write_text(yaml.safe_dump(spec, sort_keys=False, width=100))
    print(f"spec  {spec_path}")

    return _run(args, spec_path)


def _topics_cmd(args: argparse.Namespace) -> int:
    print("Available topics (use topic, topic:count, or topic:count:difficulty):\n")
    print(describe_topics())
    print(f"\nDefault count per topic: {DEFAULT_COUNT}. Difficulties: easy, medium, hard.")
    return 0


def _add_common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--seed", type=int, default=None, help="seed (random if omitted)")
    p.add_argument("--versions", type=int, default=1, help="number of A/B/C variants")
    p.add_argument("--out", default=str(ROOT / "out"))
    p.add_argument("--history", default=str(DEFAULT_HISTORY))
    p.add_argument("--lookback", type=int, default=DEFAULT_LOOKBACK,
                   help="reject fingerprints used in the last N runs")
    p.add_argument("--no-history", action="store_true",
                   help="ignore and do not update the anti-repeat ledger")
    p.add_argument("--no-pdf", action="store_true", help="emit .tex only")


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
            "Example: forge quick negatives fractions linear_equations:12:hard"
        ),
    )
    q.add_argument("topics", nargs="+",
                   help="topics, optionally topic:count or topic:count:difficulty")
    q.add_argument("--title", default="", help="worksheet title")
    q.add_argument("--header", default="", help="short header text")
    q.add_argument("--difficulty", default="", choices=["", "easy", "medium", "hard"],
                   help="override the difficulty of every section")
    q.add_argument("--name", default="quick", help="basename for the generated spec")
    q.add_argument("--save", default="", help="write the generated spec here")
    _add_common(q)
    q.set_defaults(func=_quick_cmd)

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
