"""Greatest-common-factor practice for integers and one-variable monomials."""
from __future__ import annotations
import math
import random
import sympy as sp
from ..core.latexfmt import coeff
from ..core.problem import Problem
from ..core.registry import register

X = sp.Symbol("x")
GCF_RANGE = {"easy": (2, 6), "medium": (3, 12), "hard": (4, 20)}
COFACTOR_MAX = {"easy": 8, "medium": 12, "hard": 18}
EXP_RANGE = {"easy": (1, 3), "medium": (1, 5), "hard": (2, 8)}

def _coprime_pair(rng, difficulty):
    while True:
        a = rng.randint(1, COFACTOR_MAX[difficulty])
        b = rng.randint(1, COFACTOR_MAX[difficulty])
        if a != b and math.gcd(a, b) == 1:
            return a, b

def _mk(question, answer, subskill, difficulty):
    return Problem(question_latex=f"${question}$", answer_latex=f"${sp.latex(answer)}$",
                   answer_expr=answer, topic="gcf", subskill=subskill,
                   difficulty=difficulty, verify={"kind": "gcf"})

@register("gcf", "numerical")
def numerical(rng: random.Random, difficulty: str) -> Problem:
    g = rng.randint(*GCF_RANGE[difficulty])
    a, b = _coprime_pair(rng, difficulty)
    return _mk(rf"\operatorname{{GCF}}\left({g*a}, {g*b}\right)",
               sp.Integer(g), "numerical", difficulty)

@register("gcf", "monomial")
def monomial(rng: random.Random, difficulty: str) -> Problem:
    g = rng.randint(*GCF_RANGE[difficulty])
    a, b = _coprime_pair(rng, difficulty)
    lo, hi = EXP_RANGE[difficulty]
    p, q = rng.randint(lo, hi), rng.randint(lo, hi)
    if p == q:
        q = p + 1 if p < hi else p - 1
    left, right = coeff(g*a, rf"x^{{{p}}}"), coeff(g*b, rf"x^{{{q}}}")
    return _mk(rf"\operatorname{{GCF}}\left({left}, {right}\right)",
               sp.Integer(g) * X**min(p, q), "monomial", difficulty)
