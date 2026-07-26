"""Seeded sampling helpers and the anti-repetition ledger.

Problem *selection* lives here, in code, driven by a seeded ``random.Random``.
No generator may ever choose from a hardcoded list of problems.
"""

from __future__ import annotations

import json
import random
import warnings
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Sequence

from .problem import Problem
from .registry import get as get_generator

DEFAULT_HISTORY = Path(__file__).resolve().parents[2] / "history" / "used.json"
DEFAULT_LOOKBACK = 5
MAX_ATTEMPTS = 200


# --------------------------------------------------------------------------
# RNG helpers
# --------------------------------------------------------------------------

def nonzero_int(rng: random.Random, lo: int, hi: int) -> int:
    """Uniform integer in [lo, hi] excluding 0."""
    while True:
        v = rng.randint(lo, hi)
        if v != 0:
            return v


def signed(rng: random.Random, lo: int, hi: int) -> int:
    """Magnitude in [lo, hi] with a random sign."""
    return rng.choice((-1, 1)) * rng.randint(lo, hi)


def distinct(rng: random.Random, lo: int, hi: int, k: int, exclude_zero: bool = False) -> List[int]:
    pool = [v for v in range(lo, hi + 1) if not (exclude_zero and v == 0)]
    if len(pool) < k:
        raise ValueError("range too small for k distinct values")
    return rng.sample(pool, k)


def pick(rng: random.Random, seq: Sequence):
    return seq[rng.randrange(len(seq))]


# --------------------------------------------------------------------------
# Ledger
# --------------------------------------------------------------------------

@dataclass
class Ledger:
    """Global fingerprint history: block anything used in the last N runs."""

    path: Path = DEFAULT_HISTORY
    lookback: int = DEFAULT_LOOKBACK
    runs: List[dict] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        self.path = Path(self.path)
        self.runs = []
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text() or "{}")
                self.runs = list(data.get("runs", []))
            except json.JSONDecodeError:
                warnings.warn(f"corrupt ledger at {self.path}; starting fresh")

    @property
    def blocked(self) -> set:
        recent = self.runs[-self.lookback:] if self.lookback > 0 else []
        out: set = set()
        for run in recent:
            out.update(run.get("fingerprints", []))
        return out

    def record(self, fingerprints: Iterable[str]) -> None:
        self.runs.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "fingerprints": sorted(set(fingerprints)),
            }
        )
        # Keep the file bounded; anything older than the window is inert.
        keep = max(self.lookback * 4, 20)
        self.runs = self.runs[-keep:]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"runs": self.runs}, indent=2))


class NullLedger(Ledger):
    """Ledger that blocks nothing and persists nothing (tests, --no-history)."""

    def __init__(self) -> None:
        self.path = Path("/dev/null")
        self.lookback = 0
        self.runs = []

    @property
    def blocked(self) -> set:
        return set()

    def record(self, fingerprints: Iterable[str]) -> None:
        return None


# --------------------------------------------------------------------------
# Quota-enforcing draw
# --------------------------------------------------------------------------

def draw(
    rng: random.Random,
    topic: str,
    subskill: str,
    difficulty: str,
    count: int,
    blocked: set,
    seen: set,
) -> List[Problem]:
    """Draw exactly ``count`` problems, avoiding ``blocked`` and ``seen``.

    Quotas are enforced: this returns ``count`` problems or raises. If the
    generator's space is too cramped to honour the ledger, the ledger
    constraint is relaxed (with a warning) rather than looping forever.
    """
    gen = get_generator(topic, subskill)
    out: List[Problem] = []
    relaxed = False

    while len(out) < count:
        attempts = 0
        while attempts < MAX_ATTEMPTS:
            attempts += 1
            p = gen(rng, difficulty)
            if not p.fingerprint:
                raise ValueError(f"{topic}/{subskill} produced an empty fingerprint")
            if p.fingerprint in seen:
                continue  # never duplicate within one worksheet
            if not relaxed and p.fingerprint in blocked:
                continue
            seen.add(p.fingerprint)
            out.append(p)
            break
        else:
            if relaxed:
                raise RuntimeError(
                    f"{topic}/{subskill} ({difficulty}) cannot produce {count} distinct "
                    f"problems; its sample space is too small."
                )
            warnings.warn(
                f"{topic}/{subskill} ({difficulty}): exhausted {MAX_ATTEMPTS} attempts "
                f"under the anti-repeat ledger; relaxing history constraint.",
                stacklevel=2,
            )
            relaxed = True

    return out
