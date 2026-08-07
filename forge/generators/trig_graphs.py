"""Amplitude, period, and phase shift of a sinusoid.

The equation is printed in the factored form ``y = a sin(b(x - c)) + d`` so
every property can be read off it directly, and the verifier re-reads the
same printed coefficients rather than trusting the generator.

Periods stay exact multiples of pi: ``b`` is a small integer, so ``2*pi/b``
is never a decimal.
"""

from __future__ import annotations

import random

import sympy as sp

from ..core.latexfmt import num, terms
from ..core.problem import Problem
from ..core.registry import register
from ..core.sampling import nonzero_int, pick

AMPLITUDE = {"easy": (2, 6), "medium": (2, 10), "hard": (2, 15)}
# b > 1 changes the period; easy keeps it at 1 so the period stays 2*pi and
# the subskill is purely "read the amplitude".
B_VALUES = {"easy": (1,), "medium": (1, 2, 3, 4), "hard": (2, 3, 4, 5, 6)}
SHIFT = {"easy": (1, 4), "medium": (1, 8), "hard": (2, 12)}
FUNCS = ("sin", "cos")


def _mk(question: str, value, subskill: str, difficulty: str, kind: str) -> Problem:
    return Problem(
        question_latex=question,
        answer_latex=f"${sp.latex(value)}$",
        answer_expr=value,
        topic="trig_graphs",
        subskill=subskill,
        difficulty=difficulty,
        verify={"kind": kind},
    )


def _equation(rng: random.Random, difficulty: str):
    """Print ``y = a f(b(x - c)) + d`` and return its four parameters."""
    lo, hi = AMPLITUDE[difficulty]
    a = rng.randint(lo, hi)
    if difficulty != "easy" and rng.random() < 0.35:
        a = -a
    b = pick(rng, B_VALUES[difficulty])
    c = nonzero_int(rng, -SHIFT[difficulty][1], SHIFT[difficulty][1])
    d = nonzero_int(rng, -SHIFT[difficulty][1], SHIFT[difficulty][1])
    func = pick(rng, FUNCS)

    inner = f"x - {c}" if c > 0 else f"x + {-c}"
    inner = inner if b == 1 else f"{b}({inner})"
    body = rf"\{func}\left({inner}\right)"
    lead = "-" if a == -1 else ("" if a == 1 else str(a))
    text = terms(f"{lead}{body}", num(d))
    return f"$y = {text}$", a, b, c, d


@register("trig_graphs", "amplitude")
def amplitude(rng: random.Random, difficulty: str) -> Problem:
    question, a, b, c, d = _equation(rng, difficulty)
    return _mk(question, sp.Integer(abs(a)), "amplitude", difficulty, "trig_amplitude")


@register("trig_graphs", "period")
def period(rng: random.Random, difficulty: str) -> Problem:
    question, a, b, c, d = _equation(rng, difficulty)
    return _mk(question, sp.nsimplify(2 * sp.pi / b), "period", difficulty,
               "trig_period")


@register("trig_graphs", "phase_shift")
def phase_shift(rng: random.Random, difficulty: str) -> Problem:
    """The horizontal shift ``c``, signed: positive is a shift right."""
    question, a, b, c, d = _equation(rng, difficulty)
    return _mk(question, sp.Integer(c), "phase_shift", difficulty,
               "trig_phase_shift")
