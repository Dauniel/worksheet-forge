"""Fuzz every registered generator: it must never throw and never lie."""

from __future__ import annotations

import dataclasses
import os
import re
import random

import pytest

from forge.core.problem import DIFFICULTIES
from forge.core.registry import all_generators
from forge.core.verify import VerificationError, verify_problem

# Full 1000-seed sweep is thorough but slow (~3.9ms/verification * ~67k calls
# in this file alone, ~8 min of the suite's ~10 min). Default to a fast
# 250-seed pass for local iteration; set FORGE_FULL_FUZZ=1 for the full
# sweep (CI / pre-release / after touching a generator or verify.py).
SEEDS = 1000 if os.environ.get("FORGE_FULL_FUZZ") == "1" else 250

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
    ("geometry", "pythagorean_hypotenuse"): (
        55,  # 6 triples x 5 UNITS x SCALE["medium"] = (1, 2), minus 3-4-5
             # scaled colliding with 6-8-10 unscaled
        "both legs are given and the hypotenuse must come out a whole "
        "number, so the sides can only be a Pythagorean triple -- 6 "
        "well-proportioned primitives times the unit label, scaled per "
        "tier. Widening it means accepting irrational hypotenuses (that "
        "is simplify_radical) or triangles that draw as slivers",
    ),
    ("geometry", "pythagorean_leg"): (
        110,  # as above, doubled: either leg may be the unknown
        "same triple pool as pythagorean_hypotenuse, doubled because "
        "either leg may be the unknown",
    ),
    ("angles", "polygon_interior_sum"): (
        14,  # SIDES["medium"] = 5..18
        "a polygon interior-angle sum varies only in the number of sides -- "
        "there is nothing else in the sentence to sample, so the reachable "
        "space is exactly the size of the side-count range",
    ),
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
    ("roots", "simplify_cube_radical"): (
        16,  # cbrt(a^3*b) -> a*cbrt(b), a in [2,3], b cube-free <= cap//8
        # = 15 at medium (CUBEFREE_MAX/COEF_TIER_MAX_CUBE/PRODUCT_CAP_CUBE
        # ["medium"]), product a^3*b <= 125. Brute-force enumerated: 16
        # distinct printed radicands are reachable at medium tier.
        "cube-free radicand + coefficient product capped at 125 (medium "
        "tier); brute-force enumeration gives exactly 16 distinct reachable "
        "radicands",
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
    ("unit_circle", "degree_radian_conversion"): (
        34,  # 17 "nice" angles (multiples of 30/45 up to 360) x 2 directions
        "degrees/radians conversion is only ever asked for a fixed, small "
        "catalog of standard angles -- there is no wider range to draw from, "
        "and the reachable space doesn't grow with difficulty",
    ),
    ("unit_circle", "exact_trig_value"): (
        46,  # 16 nice angles x 3 funcs, minus tan at 270 (undefined)
        "exact trig values are only defined for the standard unit-circle "
        "angles; the reachable space doesn't grow with difficulty",
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
def test_question_bodies_use_display_fractions(key):
    r"""A question body may not contain an inline \frac at all.

    Question bodies are display-style, so every fraction in one has to be
    \dfrac. This started as a narrower check for lines mixing \dfrac with
    \frac, which let a second bug ship: a body whose *only* fraction was
    inline is uniformly shrunken, mixes nothing, and passed -- e.g.
    ``9x - 10 = -\frac{13}{4}`` reached a worksheet with the fraction set at
    footnote size. Any inline \frac is the defect; mixing is just the loudest
    symptom. Answer keys are exempt: CLAUDE.md keeps them on \frac by
    convention.
    """
    inline = re.compile(r"(?<!d)\\frac")
    gen = all_generators()[key]
    for seed in range(SEEDS):
        difficulty = DIFFICULTIES[seed % len(DIFFICULTIES)]
        q = gen(random.Random(seed), difficulty).question_latex
        if inline.search(q):
            pytest.fail(f"{key} seed {seed}: inline \\frac in question body {q!r}")


# Generators that legitimately cannot have their printed answer key
# corruption-tested this way. Kept empty on purpose: fix 2 made the printed
# key validated for every registered generator, so nothing needs to be here.
# If a generator is ever added whose printed key truly can't be checked, it
# must be listed here with a comment justifying why -- silence is never the
# default.
ALLOW_UNVALIDATED_KEY: set = set()


@pytest.mark.parametrize("key", _keys())
def test_corrupted_answer_latex_is_caught(key):
    """A plainly wrong printed key must fail verification for every generator.

    Mirrors probe_key.py: generate one valid problem, corrupt only
    `answer_latex` (never `answer_expr`), and assert verification catches it.
    """
    if key in ALLOW_UNVALIDATED_KEY:
        pytest.skip("explicitly allow-listed -- see ALLOW_UNVALIDATED_KEY")
    gen = all_generators()[key]
    p = gen(random.Random(0), "medium")
    verify_problem(p)  # sanity: the untouched problem must verify clean
    bad = dataclasses.replace(p, answer_latex="$99999$")
    with pytest.raises(VerificationError):
        verify_problem(bad)


_INEQ_SYMBOL_FLIP = {"<": ">", ">": "<", r"\le": r"\ge", r"\ge": r"\le"}
_INEQ_SYMBOL = re.compile(r"\\ge|\\le|<|>")


def test_inequality_wrong_direction_key_is_caught():
    """A printed key stating the opposite inequality direction must fail."""
    from forge.generators import inequalities as ineq

    p = ineq.one_step(random.Random(1), "hard")
    verify_problem(p)  # sanity
    m = _INEQ_SYMBOL.search(p.answer_latex)
    assert m, f"no relation symbol in {p.answer_latex!r}"
    bad_latex = p.answer_latex[: m.start()] + _INEQ_SYMBOL_FLIP[m.group()] + p.answer_latex[m.end() :]
    bad = dataclasses.replace(p, answer_latex=bad_latex)
    with pytest.raises(VerificationError):
        verify_problem(bad)


def test_inequality_shifted_boundary_key_is_caught():
    """A printed key with the boundary shifted by +1 must fail."""
    from forge.generators import inequalities as ineq

    p = ineq.two_step(random.Random(2), "hard")
    verify_problem(p)  # sanity
    nums = list(re.finditer(r"-?\d+", p.answer_latex))
    assert nums, f"no integer boundary in {p.answer_latex!r}"
    last = nums[-1]
    shifted = str(int(last.group()) + 1)
    bad_latex = p.answer_latex[: last.start()] + shifted + p.answer_latex[last.end() :]
    bad = dataclasses.replace(p, answer_latex=bad_latex)
    with pytest.raises(VerificationError):
        verify_problem(bad)
