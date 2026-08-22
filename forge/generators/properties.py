"""Identifying algebraic properties (commutative, associative, identity,
inverse) of addition and multiplication.

Each problem shows one equation demonstrating exactly one property of one
operation, then offers four multiple-choice labels for the student to pick
from -- the correct property plus the other three properties, all stated for
*the same operation as the equation*. Choices never mix operations (an
addition equation never offers "... of Multiplication" as a distractor):
that would let the student answer by spotting the operation instead of by
recognizing the property, which is the actual skill being tested.

Operands are sampled integers or single-letter variables (never a hardcoded
pool -- see CLAUDE.md invariant 1). Several shapes are excluded by
construction because they make the "correct" choice ambiguous or wrong:

- Commutative with equal operands (``a + a = a + a`` demonstrates nothing).
- Identity where the non-identity operand already equals the identity
  element (``0 + 0 = 0`` also reads as an identity-times-itself degenerate).
- Inverse (multiplication) with ``a in {1, -1}`` -- ``1 * 1/1 = 1`` also
  reads as an identity statement; inverse (addition) with ``a == 0`` for the
  same reason.
- Associative where two of the three operands coincide in a way that also
  reads as commutative (e.g. any two of a, b, c equal).
- Any multiplication equation with a ``0`` operand. The reference worksheet
  this generator is modeled on shipped a broken item, ``9 * 0 = 0``, whose
  four offered choices did not include the actual property demonstrated
  (Zero Product) -- multiplication by zero is excluded entirely so that
  never recurs.
"""

from __future__ import annotations

import random

from ..core.problem import Problem
from ..core.registry import register
from ..core.sampling import pick

PROPERTIES = ("commutative", "associative", "identity", "inverse")
OPERATIONS = ("addition", "multiplication")

MAGNITUDE = {"easy": 9, "medium": 15, "hard": 30}
# Probability of using a variable instead of an integer operand, and of a
# negative integer, scaled by difficulty.
VAR_CHANCE = {"easy": 0.15, "medium": 0.3, "hard": 0.45}
NEG_CHANCE = {"easy": 0.0, "medium": 0.35, "hard": 0.55}

_LETTERS = "xyzab"

_LABELS = {
    ("commutative", "addition"): "Commutative Property of Addition",
    ("associative", "addition"): "Associative Property of Addition",
    ("identity", "addition"): "Identity Property of Addition",
    ("inverse", "addition"): "Inverse Property of Addition",
    ("commutative", "multiplication"): "Commutative Property of Multiplication",
    ("associative", "multiplication"): "Associative Property of Multiplication",
    ("identity", "multiplication"): "Identity Property of Multiplication",
    ("inverse", "multiplication"): "Inverse Property of Multiplication",
}


def _operand(rng: random.Random, difficulty: str, *, allow_zero: bool = True,
             allow_var: bool = True) -> tuple[str, int | None]:
    """Sample one operand. Returns (latex, int_value_or_None_if_variable)."""
    hi = MAGNITUDE[difficulty]
    if allow_var and rng.random() < VAR_CHANCE[difficulty]:
        letter = pick(rng, _LETTERS)
        return letter, None
    lo = 1 if not allow_zero else 0
    n = rng.randint(lo, hi)
    if n != 0 and rng.random() < NEG_CHANCE[difficulty]:
        n = -n
    return str(n), n


def _neg_latex(latex: str, val: int | None) -> str:
    if val is not None:
        return str(-val)
    return f"-{latex}"


def _fmt(latex: str, val: int | None, *, leading: bool) -> str:
    """Render one operand occurrence, parenthesizing a negative integer that
    is not the very first token of its equation side. ``a - b`` conventions
    aside, a bare `+ -8` (or `\\cdot -8`) reads as a typo in this repo's other
    generators; only the leading position of a side is allowed to carry a
    sign unparenthesized (mirrors ``y = -x - 3`` elsewhere in the codebase).
    """
    if not leading and val is not None and val < 0:
        return f"({latex})"
    return latex


def _frac_inv_latex(latex: str) -> str:
    # Question bodies must use \dfrac (display style), never inline \frac --
    # see tests/test_generators.py::test_question_bodies_use_display_fractions.
    return rf"\dfrac{{1}}{{{latex}}}"


def _mul_op_ok(val: int | None) -> bool:
    """Reject a sampled multiplication operand of literal 0."""
    return val != 0


def _build_commutative(rng: random.Random, difficulty: str, op: str) -> str:
    while True:
        a_lat, a_val = _operand(rng, difficulty, allow_zero=(op == "addition"))
        b_lat, b_val = _operand(rng, difficulty, allow_zero=(op == "addition"))
        if op == "multiplication" and (not _mul_op_ok(a_val) or not _mul_op_ok(b_val)):
            continue
        if a_lat == b_lat:
            continue
        break
    sym = "+" if op == "addition" else r"\cdot"
    return (
        f"{_fmt(a_lat, a_val, leading=True)} {sym} {_fmt(b_lat, b_val, leading=False)} = "
        f"{_fmt(b_lat, b_val, leading=True)} {sym} {_fmt(a_lat, a_val, leading=False)}"
    )


def _build_associative(rng: random.Random, difficulty: str, op: str) -> str:
    sym = "+" if op == "addition" else r"\cdot"
    while True:
        a_lat, a_val = _operand(rng, difficulty, allow_zero=(op == "addition"))
        b_lat, b_val = _operand(rng, difficulty, allow_zero=(op == "addition"))
        c_lat, c_val = _operand(rng, difficulty, allow_zero=(op == "addition"))
        if op == "multiplication" and not all(_mul_op_ok(v) for v in (a_val, b_val, c_val)):
            continue
        lits = [a_lat, b_lat, c_lat]
        if len(set(lits)) != 3:
            continue
        break
    a_l = _fmt(a_lat, a_val, leading=True)
    b_nc = _fmt(b_lat, b_val, leading=False)  # b never leads within either grouping
    c_nc = _fmt(c_lat, c_val, leading=False)
    return f"({a_l} {sym} {b_nc}) {sym} {c_nc} = {a_l} {sym} ({b_nc} {sym} {c_nc})"


def _build_identity(rng: random.Random, difficulty: str, op: str) -> str:
    identity_elem = "0" if op == "addition" else "1"
    sym = "+" if op == "addition" else r"\cdot"
    while True:
        a_lat, a_val = _operand(rng, difficulty, allow_zero=False)
        if a_lat == identity_elem:
            continue
        break
    left_first = rng.choice((True, False))
    if left_first:
        # a op elem = a -- a leads the LHS; the RHS is a lone atom, also leading.
        return f"{_fmt(a_lat, a_val, leading=True)} {sym} {identity_elem} = {_fmt(a_lat, a_val, leading=True)}"
    # elem op a = a -- a follows the identity element, so it is NOT leading on the LHS.
    return f"{identity_elem} {sym} {_fmt(a_lat, a_val, leading=False)} = {_fmt(a_lat, a_val, leading=True)}"


def _build_inverse(rng: random.Random, difficulty: str, op: str) -> str:
    if op == "addition":
        while True:
            a_lat, a_val = _operand(rng, difficulty, allow_zero=False, allow_var=True)
            if a_lat == "0":
                continue
            break
        # Parenthesize only when the additive inverse actually renders with a
        # leading "-" (`13 + (-13)`, `x + (-x)`). When ``a`` is negative its
        # inverse is positive, and `-5 + (5)` reads as a typo -- write `-5 + 5`.
        neg = _neg_latex(a_lat, a_val)
        return f"{a_lat} + {f'({neg})' if neg.startswith('-') else neg} = 0"
    else:
        while True:
            a_lat, a_val = _operand(rng, difficulty, allow_zero=False, allow_var=True)
            if a_val in (1, -1) or a_lat in ("1", "-1"):
                continue
            break
        inv = _frac_inv_latex(a_lat)
        return rf"{a_lat} \cdot {inv} = 1"


_BUILDERS = {
    "commutative": _build_commutative,
    "associative": _build_associative,
    "identity": _build_identity,
    "inverse": _build_inverse,
}


def _choice_block(rng: random.Random, equation: str, property_name: str, op: str) -> tuple[str, str]:
    """Build the shuffled A)-D) choice block. Returns (latex_block, answer_line)."""
    others = [pr for pr in PROPERTIES if pr != property_name]
    labels = [_LABELS[(property_name, op)]] + [_LABELS[(pr, op)] for pr in others]
    rng.shuffle(labels)
    correct_label = _LABELS[(property_name, op)]
    letters = "ABCD"
    lines = []
    answer_line = ""
    for letter, label in zip(letters, labels):
        lines.append(f"{letter}) {label}")
        if label == correct_label:
            answer_line = f"{letter}) {label}"
    choices_tex = " \\\\\n".join(lines)
    block = (
        f"${equation}$\n"
        "\\\\[2pt]\n"
        "\\begin{minipage}{\\linewidth}\n"
        f"{choices_tex}\n"
        "\\end{minipage}"
    )
    return block, answer_line


def _generate(rng: random.Random, difficulty: str, property_name: str) -> Problem:
    op = pick(rng, OPERATIONS)
    equation = _BUILDERS[property_name](rng, difficulty, op)
    question_latex, answer_line = _choice_block(rng, equation, property_name, op)
    answer_expr = f"{property_name}_{'add' if op == 'addition' else 'mul'}"
    return Problem(
        question_latex=question_latex,
        answer_latex=answer_line,
        answer_expr=answer_expr,
        topic="properties",
        subskill=property_name if property_name != "mixed" else "mixed",
        difficulty=difficulty,
        verify={"kind": "property"},
    )


@register("properties", "commutative")
def commutative(rng: random.Random, difficulty: str) -> Problem:
    return _generate(rng, difficulty, "commutative")


@register("properties", "associative")
def associative(rng: random.Random, difficulty: str) -> Problem:
    return _generate(rng, difficulty, "associative")


@register("properties", "identity")
def identity(rng: random.Random, difficulty: str) -> Problem:
    return _generate(rng, difficulty, "identity")


@register("properties", "inverse")
def inverse(rng: random.Random, difficulty: str) -> Problem:
    return _generate(rng, difficulty, "inverse")


@register("properties", "mixed")
def mixed(rng: random.Random, difficulty: str) -> Problem:
    property_name = pick(rng, PROPERTIES)
    p = _generate(rng, difficulty, property_name)
    return Problem(
        question_latex=p.question_latex,
        answer_latex=p.answer_latex,
        answer_expr=p.answer_expr,
        topic="properties",
        subskill="mixed",
        difficulty=difficulty,
        verify={"kind": "property"},
    )
