import random
import sympy as sp
from forge.core.registry import get
from forge.core.verify import verify_problem

def test_new_gcf_generators_verify():
    for subskill in ("numerical", "monomial"):
        for seed in range(100):
            verify_problem(get("gcf", subskill)(random.Random(seed), "medium"))

def test_monomial_gcf_has_variable_factor():
    p = get("gcf", "monomial")(random.Random(4), "medium")
    assert p.answer_expr.has(sp.Symbol("x"))

def test_polynomial_like_terms_repeats_quadratic_terms():
    for difficulty in ("easy", "medium", "hard"):
        p = get("like_terms", "polynomial_like_terms")(random.Random(4), difficulty)
        verify_problem(p)
        assert p.question_latex.count("x^{2}") >= 2
