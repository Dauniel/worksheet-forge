"""Mean, median, mode, and range of a small data set.

Every data set is sampled; the answer is recomputed from the printed list by
``forge/core/verify/``, so the question and the key cannot drift apart.

Backwards construction applies here too, but only where it buys something.
``mean`` picks the answer first and then builds a list summing to
``mean * n`` -- otherwise most random lists give a mean like 47/6, which is
arithmetic busywork rather than a lesson about averaging. ``median``,
``mode`` and ``range`` read straight off a sampled list, since their answers
are always tidy by construction.
"""

from __future__ import annotations

import random

import sympy as sp

from ..core.problem import Problem
from ..core.registry import register
from ..core.sampling import pick

# Set size and value spread. Odd counts only for median at easy/medium: the
# even case needs averaging the middle pair, which is the harder skill.
COUNT = {"easy": (5, 5), "medium": (5, 7), "hard": (6, 9)}
VALUE = {"easy": (1, 20), "medium": (2, 45), "hard": (5, 90)}
MEAN_VALUE = {"easy": (3, 15), "medium": (4, 30), "hard": (6, 50)}


def _mk(question: str, value, subskill: str, difficulty: str, kind: str) -> Problem:
    value = sp.nsimplify(value)
    return Problem(
        question_latex=question,
        answer_latex=f"${sp.latex(value)}$",
        answer_expr=value,
        topic="statistics",
        subskill=subskill,
        difficulty=difficulty,
        verify={"kind": kind},
    )


def _render(values) -> str:
    """A data set prints as a comma-separated list, in the given order.

    Each value gets its own ``$...$`` rather than one math block around the
    whole list: that is the form ``verify._NUM`` extracts, so the verifier
    reads back exactly the numbers the student sees.
    """
    return ", ".join(f"${v}$" for v in values)


@register("statistics", "mean")
def mean(rng: random.Random, difficulty: str) -> Problem:
    """Backwards from a whole-number mean, so the answer is not 47/6."""
    n = rng.randint(*COUNT[difficulty])
    lo, hi = MEAN_VALUE[difficulty]
    target = rng.randint(lo, hi)

    # Sample n-1 freely, then let the last value absorb the remainder. Redraw
    # if that lands out of range, rather than clamping -- a clamped last value
    # would quietly break the intended mean.
    for _ in range(60):
        head = [rng.randint(max(1, target - 8), target + 8) for _ in range(n - 1)]
        last = target * n - sum(head)
        if 1 <= last <= hi + 10:
            values = head + [last]
            rng.shuffle(values)
            return _mk(_render(values), target, "mean", difficulty, "stat_mean")
    # Degenerate fallback: a flat list always has exactly the target mean.
    return _mk(_render([target] * n), target, "mean", difficulty, "stat_mean")


@register("statistics", "median")
def median(rng: random.Random, difficulty: str) -> Problem:
    lo, hi = VALUE[difficulty]
    n = rng.randint(*COUNT[difficulty])
    if difficulty != "hard":
        n += 1 - (n % 2)  # force odd: no averaging of the middle pair yet
    values = [rng.randint(lo, hi) for _ in range(n)]
    rng.shuffle(values)
    ordered = sorted(values)
    mid = len(ordered) // 2
    answer = (
        sp.Rational(ordered[mid - 1] + ordered[mid], 2)
        if len(ordered) % 2 == 0
        else sp.Integer(ordered[mid])
    )
    return _mk(_render(values), answer, "median", difficulty, "stat_median")


@register("statistics", "mode")
def mode(rng: random.Random, difficulty: str) -> Problem:
    """One clear winner: a tie has no single answer to key."""
    lo, hi = VALUE[difficulty]
    n = rng.randint(*COUNT[difficulty])
    winner = rng.randint(lo, hi)
    repeats = 3 if difficulty == "hard" else 2

    others: list[int] = []
    while len(others) < n - repeats:
        v = rng.randint(lo, hi)
        # Every other value appears at most once, and never as often as the
        # winner, so the mode is unambiguous.
        if v != winner and v not in others:
            others.append(v)
    values = [winner] * repeats + others
    rng.shuffle(values)
    return _mk(_render(values), winner, "mode", difficulty, "stat_mode")


@register("statistics", "range_of_set")
def range_of_set(rng: random.Random, difficulty: str) -> Problem:
    lo, hi = VALUE[difficulty]
    n = rng.randint(*COUNT[difficulty])
    values = [rng.randint(lo, hi) for _ in range(n)]
    # A zero range would print "find the range" over a list of identical
    # numbers -- technically correct, pedagogically pointless.
    while max(values) == min(values):
        values = [rng.randint(lo, hi) for _ in range(n)]
    rng.shuffle(values)
    return _mk(_render(values), max(values) - min(values), "range_of_set",
               difficulty, "stat_range")
