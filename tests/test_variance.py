"""The -8 + 5 test: problem selection must actually vary run to run."""

from __future__ import annotations

import random
from collections import Counter

import pytest

from forge.core.registry import all_generators
from forge.core.sampling import Ledger, NullLedger, draw

RUNS = 50


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
    # The property that matters: no single problem is the archetype.
    assert top_count <= 3, (
        f"{topic}/{subskill}: {top_text!r} was first in {top_count} of {RUNS} runs"
    )
    # A loose floor on spread. It cannot be near 1.0: with a sample space of a
    # few dozen (which "easy" subskills legitimately have), the birthday
    # paradox alone puts expected distinct draws well below RUNS. The
    # top_count assertion above is what actually guards against archetypes.
    assert len(firsts) >= RUNS * 0.6, (
        f"{topic}/{subskill}: only {len(firsts)} distinct first problems in {RUNS} runs"
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
