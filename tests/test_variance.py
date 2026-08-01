"""The -8 + 5 test: problem selection must actually vary run to run."""

from __future__ import annotations

import math
import random
from collections import Counter

import pytest

from forge.core.registry import all_generators
from forge.core.sampling import Ledger, NullLedger, draw

RUNS = 50

# Subskills whose *entire* reachable output space (at the "easy" difficulty
# this test exercises) is smaller than the generic 60%-distinct floor below
# can ever reach -- not a tuning problem, a fact about how few values satisfy
# the pedagogical constraints. `roots.square_root` and `roots.cube_root` are
# deliberately plain (see forge/generators/roots.py's module docstring): a
# bare radical of a perfect square/cube, positive only, no coefficient, no
# fraction, no sign. Under the shared 225/216 radicand cap that leaves only
# as many outputs as there are bases in the "easy" range.
#
# Each entry is (topic, subskill) -> (exact reachable count at "easy",
# reason). For these subskills the test below swaps the generic 60%-spread
# check for one that verifies the generator reaches at/near its *true*
# ceiling and that no single value swamps the others -- so a generator that
# hardcodes or collapses onto a handful of favorites within that small space
# is still caught, it's just held to the real ceiling instead of an
# unreachable generic floor.
SMALL_REACHABLE_SPACE = {
    ("roots", "square_root"): (
        11,  # bases 2..12 (SQUARE_BASE["easy"]), bare sqrt(n^2) = n only
        "positive perfect squares only, bases 2-12 at easy difficulty "
        "(<=15 across all tiers); no coefficient/fraction/sign forms",
    ),
    ("roots", "cube_root"): (
        4,  # bases 2..5 (CUBE_BASE["easy"]), bare cbrt(n^3) = n only
        "positive perfect cubes only, bases 2-5 at easy difficulty "
        "(<=6 across all tiers); no coefficient/fraction/sign forms",
    ),
    ("roots", "simplify_radical"): (
        55,  # sqrt(a^2*b) -> a*sqrt(b), a in [2,8], b squarefree <=30 at
        # easy (SQUAREFREE_MAX/COEF_TIER_MAX["easy"]), product a^2*b <= 225.
        # See tests/test_generators.py's SMALL_REACHABLE_SPACE entry for the
        # same subskill: the absolute max under the cap (72, any tier) is
        # itself close enough to the generic floor that ordinary
        # birthday-paradox variance can dip under it in a fixed run.
        "squarefree radicand + coefficient product capped at 225; even the "
        "72-value absolute max the cap allows sits close to the generic "
        "spread floor",
    ),
}


def _first_problems(topic, subskill, difficulty="easy"):
    return [
        draw(random.Random(seed), topic, subskill, difficulty, 1, set(), set())[0]
        for seed in range(RUNS)
    ]


@pytest.mark.parametrize("key", sorted(all_generators()))
def test_first_problem_does_not_repeat(key):
    topic, subskill = key
    firsts = Counter(p.question_latex for p in _first_problems(topic, subskill))
    top_text, top_count = firsts.most_common(1)[0]
    distinct = len(firsts)

    if key in SMALL_REACHABLE_SPACE:
        ceiling, reason = SMALL_REACHABLE_SPACE[key]
        # The space is provably bounded -- compare against the coupon
        # collector expectation for RUNS draws of `ceiling` equally likely
        # values, not the raw ceiling. For a small ceiling (e.g. 4) that
        # expectation is ~= ceiling, so this still demands near-full
        # coverage; for a larger-but-still-bounded ceiling (e.g. 55) it
        # correctly allows for the birthday-paradox gap a uniform draw
        # leaves even at the true ceiling.
        assert distinct <= ceiling, (
            f"{topic}/{subskill}: saw {distinct} distinct first problems but "
            f"the documented reachable ceiling is {ceiling} ({reason}); "
            f"update SMALL_REACHABLE_SPACE if the generator legitimately "
            f"grew its space"
        )
        expected_distinct = ceiling * (1 - (1 - 1 / ceiling) ** RUNS)
        assert distinct >= 0.7 * expected_distinct, (
            f"{topic}/{subskill}: only {distinct} distinct first problems in "
            f"{RUNS} runs, well under the ~{expected_distinct:.0f} expected "
            f"from uniformly sampling {ceiling} reachable values ({reason}) "
            f"-- the generator may be favoring a subset instead of sampling "
            f"uniformly"
        )
        # No single value may swamp the others. With `ceiling` equally
        # likely values across RUNS draws the expected count per value is
        # RUNS/ceiling; allow generous slack for birthday-paradox variance
        # but still flag a generator that collapses onto a few favorites.
        expected = RUNS / ceiling
        skew_cap = math.ceil(expected * 3) + 2
        assert top_count <= skew_cap, (
            f"{topic}/{subskill}: {top_text!r} was first in {top_count} of "
            f"{RUNS} runs, far more than the ~{expected:.1f} expected across "
            f"the {ceiling} reachable values ({reason}) -- looks skewed, not "
            f"just small"
        )
        return

    # The property that matters: no single problem is the archetype.
    assert top_count <= 3, (
        f"{topic}/{subskill}: {top_text!r} was first in {top_count} of {RUNS} runs"
    )
    # A loose floor on spread. It cannot be near 1.0: with a sample space of a
    # few dozen (which "easy" subskills legitimately have), the birthday
    # paradox alone puts expected distinct draws well below RUNS. The
    # top_count assertion above is what actually guards against archetypes.
    assert distinct >= RUNS * 0.6, (
        f"{topic}/{subskill}: only {distinct} distinct first problems in {RUNS} runs"
    )


def test_minus_eight_plus_five_is_not_the_archetype():
    """The specific regression this project exists to fix."""
    firsts = Counter(
        p.question_latex for p in _first_problems("negatives", "add_sub_integers")
    )
    for variant in ("$-8 + 5$", "$-8 + (5)$", "$-8+5$"):
        assert firsts.get(variant, 0) <= 1, f"{variant} appeared first {firsts[variant]}x"


def test_ledger_blocks_recent_fingerprints(tmp_path):
    ledger = Ledger(path=tmp_path / "used.json", lookback=5)
    seen: set = set()
    first = draw(random.Random(1), "negatives", "add_sub_integers", "easy", 8,
                 ledger.blocked, seen)
    ledger.record(p.fingerprint for p in first)

    blocked = ledger.blocked
    assert blocked == {p.fingerprint for p in first}

    second = draw(random.Random(1), "negatives", "add_sub_integers", "easy", 8,
                  blocked, set())
    assert not ({p.fingerprint for p in second} & blocked), (
        "ledger let a recently-used problem through"
    )


def test_ledger_expires_beyond_lookback(tmp_path):
    ledger = Ledger(path=tmp_path / "used.json", lookback=2)
    ledger.record(["aaa"])
    assert "aaa" in ledger.blocked
    ledger.record(["bbb"])
    ledger.record(["ccc"])
    assert "aaa" not in ledger.blocked, "fingerprint outlived its lookback window"


def test_null_ledger_blocks_nothing(tmp_path):
    ledger = NullLedger()
    ledger.record(["aaa"])
    assert ledger.blocked == set()
