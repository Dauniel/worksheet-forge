"""Fuzz every registered generator: it must never throw and never lie."""

from __future__ import annotations

import re
import random

import pytest

from forge.core.problem import DIFFICULTIES
from forge.core.registry import all_generators
from forge.core.verify import verify_problem

SEEDS = 1000

# Subskills whose entire reachable output space (at "medium" difficulty,
# which this file's 100-seed fuzz uses) is smaller than the generic 50%
# floor below -- not a tuning problem, a fact about how few values satisfy
# the pedagogical constraints. `roots.square_root` and `roots.cube_root` are
# deliberately plain (see forge/generators/roots.py's module docstring): a
# bare radical of a perfect square/cube, positive only, no coefficient, no
# fraction, no sign. `roots.simplify_radical` is also exempt here -- its
# product cap (<=108) keeps its true reachable ceiling small at every tier;
# see its own entry's comment for the exact brute-forced count.
#
# Each entry is (topic, subskill) -> (exact reachable count at "medium",
# reason). For these subskills the test swaps the generic 50-distinct floor
# for one that verifies the generator reaches at/near its *true* ceiling --
# so a generator that hardcodes or collapses onto a handful of favorites
# within that small space is still caught, it's just held to the real
# ceiling instead of an unreachable generic floor. Mirrors the
# ALLOWED_UNCATALOGED pattern in tests/test_catalog_completeness.py.
SMALL_REACHABLE_SPACE = {
    ("roots", "square_root"): (
        9,  # bases 2..10 (SQUARE_BASE["medium"]), bare sqrt(n^2) = n only
        "positive perfect squares only, bases 2-10 at medium difficulty "
        "(<=12 across all tiers); no coefficient/fraction/sign forms",
    ),
    ("roots", "cube_root"): (
        4,  # bases 2..5 (CUBE_BASE["medium"]), bare cbrt(n^3) = n only
        "positive perfect cubes only, bases 2-5 at medium difficulty "
        "(<=6 across all tiers); no coefficient/fraction/sign forms",
    ),
    ("roots", "simplify_radical"): (
        32,  # sqrt(a^2*b) -> a*sqrt(b), a in [2,9], b squarefree <= cap//4
        # = 27 at medium (SQUAREFREE_MAX/COEF_TIER_MAX/PRODUCT_CAP["medium"]),
        # product a^2*b <= 108. Brute-force enumerated: 32 distinct printed
        # radicands k = a^2*b are reachable at medium tier.
        "squarefree radicand + coefficient product capped at 108 (medium "
        "tier); brute-force enumeration gives exactly 32 distinct reachable "
        "radicands",
    ),
}


def _keys():
    return sorted(all_generators())


@pytest.mark.parametrize("key", _keys())
def test_fuzz_generator(key):
    topic, subskill = key
    gen = all_generators()[key]
    for seed in range(SEEDS):
        difficulty = DIFFICULTIES[seed % len(DIFFICULTIES)]
        rng = random.Random(seed)
        p = gen(rng, difficulty)
        assert p.fingerprint, f"{key} seed {seed}: empty fingerprint"
        assert p.topic == topic and p.subskill == subskill
        assert p.difficulty == difficulty
        assert p.question_latex.strip()
        assert p.answer_latex.strip()
        verify_problem(p)  # raises VerificationError on any mismatch


@pytest.mark.parametrize("key", _keys())
def test_generator_is_deterministic(key):
    gen = all_generators()[key]
    for seed in (0, 7, 12345):
        a = gen(random.Random(seed), "medium")
        b = gen(random.Random(seed), "medium")
        assert a.question_latex == b.question_latex
        assert a.answer_latex == b.answer_latex
        assert a.fingerprint == b.fingerprint


@pytest.mark.parametrize("key", _keys())
def test_no_hardcoded_problem_lists(key):
    """A generator whose output barely varies is a hardcoded list in disguise."""
    gen = all_generators()[key]
    seen = {gen(random.Random(s), "medium").question_latex for s in range(100)}

    if key in SMALL_REACHABLE_SPACE:
        ceiling, reason = SMALL_REACHABLE_SPACE[key]
        counts = {}
        for s in range(100):
            text = gen(random.Random(s), "medium").question_latex
            counts[text] = counts.get(text, 0) + 1
        assert len(seen) <= ceiling, (
            f"{key}: saw {len(seen)} distinct problems but the documented "
            f"reachable ceiling is {ceiling} ({reason}); update "
            f"SMALL_REACHABLE_SPACE if the generator legitimately grew"
        )
        # Compare against the coupon collector expectation for 100 draws of
        # `ceiling` equally likely values, not the raw ceiling -- for a
        # small ceiling that's close to `ceiling` itself; for a
        # larger-but-still-bounded one it correctly allows for the
        # birthday-paradox gap a uniform draw leaves even at the true
        # ceiling.
        expected_distinct = ceiling * (1 - (1 - 1 / ceiling) ** 100)
        assert len(seen) >= 0.7 * expected_distinct, (
            f"{key}: only {len(seen)} distinct problems in 100 seeds, well "
            f"under the ~{expected_distinct:.0f} expected from uniformly "
            f"sampling {ceiling} reachable values ({reason}) -- generator "
            f"may be favoring a subset instead of sampling uniformly"
        )
        top_count = max(counts.values())
        expected = 100 / ceiling
        skew_cap = int(expected * 3) + 3
        assert top_count <= skew_cap, (
            f"{key}: a single value appeared {top_count} of 100 times, far "
            f"more than the ~{expected:.1f} expected across {ceiling} "
            f"reachable values ({reason}) -- looks skewed, not just small"
        )
        return

    assert len(seen) >= 50, f"{key} produced only {len(seen)} distinct problems in 100 seeds"


@pytest.mark.parametrize("key", _keys())
def test_question_bodies_do_not_mix_fraction_sizes(key):
    r"""One line must not carry both a \dfrac and a \frac.

    Question bodies are display-style, so every fraction on the line has to
    be \dfrac. Mixing renders a full-size coefficient beside a shrunken
    constant -- e.g. ``-2x + 5 \ge -\dfrac{1}{3}x - \frac{10}{3}``, which
    shipped on a worksheet before latexfmt.linear/poly scaled the constant
    along with the variable term. Answer keys are exempt: CLAUDE.md keeps
    them on inline \frac by convention.
    """
    inline = re.compile(r"(?<!d)\\frac")
    gen = all_generators()[key]
    for seed in range(SEEDS):
        difficulty = DIFFICULTIES[seed % len(DIFFICULTIES)]
        q = gen(random.Random(seed), difficulty).question_latex
        if r"\dfrac" in q and inline.search(q):
            pytest.fail(f"{key} seed {seed}: mixed fraction sizes in {q!r}")
