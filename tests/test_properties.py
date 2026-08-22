"""Targeted tests for the properties topic: same-operation distractors,
excluded degenerate forms, and the structural verifier."""

from __future__ import annotations

import random
import re

import pytest

from forge.core.problem import Problem
from forge.core.registry import get, load_generators
from forge.core.verify import VerificationError
from forge.core.verify.algebra import _v_property

load_generators()

SEEDS = range(400)


def _choices(question_latex: str) -> dict:
    mp = re.search(r"\\begin\{minipage\}.*?\n(.*?)\\end\{minipage\}", question_latex, re.S)
    assert mp is not None
    out = {}
    for ln in re.split(r"\\\\", mp.group(1)):
        ln = ln.strip()
        if not ln:
            continue
        m = re.match(r"([A-D])\)\s*(.+)$", ln)
        assert m is not None, ln
        out[m.group(1)] = m.group(2).strip()
    return out


def _equation(question_latex: str) -> str:
    m = re.search(r"\$(.*?)\$", question_latex, re.S)
    assert m is not None
    return m.group(1)


SUBSKILLS = ("commutative", "associative", "identity", "inverse", "mixed")


def test_all_eight_combos_reachable():
    seen = set()
    for subskill in SUBSKILLS:
        gen = get("properties", subskill)
        for seed in SEEDS:
            p = gen(random.Random(seed), "hard")
            seen.add(tuple(p.answer_expr.split("_")))
    expected = {
        (prop, op)
        for prop in ("commutative", "associative", "identity", "inverse")
        for op in ("add", "mul")
    }
    assert seen == expected, f"missing combos: {expected - seen}"


def test_choices_share_one_operation_and_are_distinct():
    for subskill in SUBSKILLS:
        gen = get("properties", subskill)
        for seed in SEEDS:
            for difficulty in ("easy", "medium", "hard"):
                p = gen(random.Random(seed), difficulty)
                choices = _choices(p.question_latex)
                assert len(choices) == 4
                labels = list(choices.values())
                assert len(set(labels)) == 4, labels
                ops = {lbl.rsplit(" ", 1)[-1] for lbl in labels}
                assert ops in ({"Addition"}, {"Multiplication"}), labels


def test_correct_answer_among_choices():
    for subskill in SUBSKILLS:
        gen = get("properties", subskill)
        for seed in SEEDS:
            p = gen(random.Random(seed), "medium")
            choices = _choices(p.question_latex)
            m = re.match(r"([A-D])\)\s*(.+)$", p.answer_latex.strip())
            assert m is not None
            letter, label = m.group(1), m.group(2).strip()
            assert choices.get(letter) == label


def test_no_degenerate_forms():
    for subskill in SUBSKILLS:
        gen = get("properties", subskill)
        for seed in SEEDS:
            for difficulty in ("easy", "medium", "hard"):
                p = gen(random.Random(seed), difficulty)
                eq = _equation(p.question_latex)
                if r"\cdot" in eq:
                    # no multiplication operand may be a literal 0
                    tokens = re.findall(r"(?<![A-Za-z0-9])-?\d+(?![A-Za-z0-9])", eq)
                    assert "0" not in tokens, eq
                if p.answer_expr.startswith("commutative"):
                    lhs, rhs = eq.split("=", 1)
                    op = r"\cdot" if r"\cdot" in lhs else "+"
                    a, b = [t.strip() for t in lhs.split(op, 1)]
                    assert a != b, eq


def test_verifier_accepts_generated_problems():
    for subskill in SUBSKILLS:
        gen = get("properties", subskill)
        for seed in SEEDS:
            p = gen(random.Random(seed), "hard")
            _v_property(p)  # must not raise


def test_verifier_rejects_broken_zero_product_item():
    """Regression: the reference worksheet's `9 * 0 = 0` item offered four
    property choices, none of which is the correct answer (Zero Product,
    not one of the four listed properties). The verifier must reject this
    shape rather than silently accepting a wrong/missing key."""
    question_latex = (
        r"$9 \cdot 0 = 0$"
        "\n\\\\[2pt]\n"
        "\\begin{minipage}{\\linewidth}\n"
        "A) Identity Property of Multiplication \\\\\n"
        "B) Commutative Property of Multiplication \\\\\n"
        "C) Associative Property of Multiplication \\\\\n"
        "D) Inverse Property of Multiplication\n"
        "\\end{minipage}"
    )
    bad = Problem(
        question_latex=question_latex,
        answer_latex="A) Identity Property of Multiplication",
        answer_expr="identity_mul",
        topic="properties",
        subskill="identity",
        difficulty="medium",
        verify={"kind": "property"},
    )
    with pytest.raises(VerificationError):
        _v_property(bad)
