"""Fuzz every registered generator: it must never throw and never lie."""

from __future__ import annotations

import random

import pytest

from forge.core.problem import DIFFICULTIES
from forge.core.registry import all_generators
from forge.core.verify import verify_problem

SEEDS = 1000


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
    assert len(seen) >= 50, f"{key} produced only {len(seen)} distinct problems in 100 seeds"
