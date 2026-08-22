import random
import re

from forge.core.registry import get
from forge.core.verify import verify_problem

GEN = get("linear_equations", "combine_then_solve")

SEEDS = range(500)
DIFFICULTIES = ("easy", "medium", "hard")


def test_verifies_across_seeds_and_difficulties():
    for difficulty in DIFFICULTIES:
        for seed in SEEDS:
            verify_problem(GEN(random.Random(seed), difficulty))


def test_both_families_reachable():
    # family 1: "x = " appears once as a lone variable term on each side is
    # hard to detect directly, so instead check for the structural marker --
    # family 2 always has three terms on the un-combined side (var + 2
    # constants), family 1 always has exactly two variable terms and no bare
    # constant term beside them. We detect family 2 by two consecutive
    # constant terms following a variable term.
    saw_two_var_terms = False
    saw_two_constants = False
    for seed in range(300):
        p = GEN(random.Random(seed), "medium")
        q = p.question_latex
        # crude but effective: family 2 has two "+"/"-" separated bare
        # numbers after the x term; family 1 has two x terms.
        if q.count("x") == 2:
            saw_two_var_terms = True
        if q.count("x") == 1:
            saw_two_constants = True
    assert saw_two_var_terms, "never saw the two-variable-term family"
    assert saw_two_constants, "never saw the one-variable-two-constant family"


def test_both_sides_occur():
    left_expr = False   # expression on the left, e.g. "$4x + 7x = ..."
    right_expr = False  # expression on the right, e.g. "$-16 = x + 7x$"
    for seed in range(300):
        p = GEN(random.Random(seed), "medium")
        q = p.question_latex.strip("$")
        lhs, rhs = q.split("=", 1)
        if "x" in lhs:
            left_expr = True
        if "x" in rhs:
            right_expr = True
    assert left_expr, "the un-combined expression never appeared on the left"
    assert right_expr, "the un-combined expression never appeared on the right"


def test_no_coefficient_one_or_plus_minus_bugs():
    bad_patterns = [
        re.compile(r"(?<![0-9\}])1x\b"),
        re.compile(r"-1x\b"),
        re.compile(r"\+\s*-"),
    ]
    for difficulty in DIFFICULTIES:
        for seed in range(500):
            p = GEN(random.Random(seed), difficulty)
            for pat in bad_patterns:
                assert not pat.search(p.question_latex), (
                    f"bad rendering {pat.pattern!r} in {p.question_latex!r}"
                )
                assert not pat.search(p.answer_latex), (
                    f"bad rendering {pat.pattern!r} in {p.answer_latex!r}"
                )
