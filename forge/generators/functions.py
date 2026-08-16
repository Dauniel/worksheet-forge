"""Inverse functions, composition, and transformations of a parent function.

Every problem is built from the pieces that make the answer exact: an inverse
is drawn from a slope that divides cleanly, a composition is expanded by
sympy, and a transformation is applied to a named parent function rather than
described in prose.

Transformations are stated as an equation to write, not a sentence to
describe. "Shifted right 3 and up 2" as an *answer* cannot be checked
symbolically; ``g(x) = (x - 3)^2 + 2`` can.
"""

from __future__ import annotations

import random

import sympy as sp

from ..core.latexfmt import coeff, linear, num, poly, terms
from ..core.problem import Problem
from ..core.registry import register
from ..core.sampling import nonzero_int, pick

X = sp.Symbol("x")
RANGES = {"easy": (1, 6), "medium": (2, 9), "hard": (2, 12)}
# Explicit per-tier bands rather than min(hi, N) caps: a cap that is smaller
# than both medium and hard silently collapses the two tiers into one, which
# is exactly what tests/test_variance.py's tier-collapse guard catches.
SLOPE = {"easy": (2, 7), "medium": (2, 10), "hard": (3, 14)}
INTERCEPT = {"easy": 7, "medium": 10, "hard": 14}
SHIFT = {"easy": 5, "medium": 9, "hard": 14}
STRETCH = {"easy": (1, 1), "medium": (2, 4), "hard": (2, 7)}
# Parent functions a transformation can act on, as (name, expression builder).
PARENTS = {
    "x^{2}": lambda e: e**2,
    "x^{3}": lambda e: e**3,
    "|x|": lambda e: sp.Abs(e),
}


def _mk(question: str, answer: str, answer_expr, subskill: str, difficulty: str,
        kind: str = "simplify") -> Problem:
    return Problem(
        question_latex=f"${question}$",
        answer_latex=f"${answer}$",
        answer_expr=answer_expr,
        topic="functions",
        subskill=subskill,
        difficulty=difficulty,
        verify={"kind": kind},
    )


@register("functions", "inverse_linear")
def inverse_linear(rng: random.Random, difficulty: str) -> Problem:
    """``f(x) = mx + b`` -> ``f^-1(x) = (x - b)/m``.

    ``b`` is drawn as a multiple of ``m`` so the inverse has integer
    coefficients: (x - b)/m stays tidy and the answer needs no nested
    fraction.
    """
    m = nonzero_int(rng, *SLOPE[difficulty])
    span = INTERCEPT[difficulty]
    b = m * nonzero_int(rng, -span, span)

    question = f"f(x) = {linear(m, b)}"
    # f^-1(x) = x/m - b/m, with b/m an exact integer by construction
    inverse = X / m - sp.Integer(b) / m
    answer = rf"f^{{-1}}(x) = \dfrac{{{linear(1, -b)}}}{{{m}}}"
    return Problem(
        question_latex=f"${question}$",
        answer_latex=f"${answer}$",
        answer_expr=inverse,
        topic="functions",
        subskill="inverse_linear",
        difficulty=difficulty,
        verify={"kind": "inverse_function"},
    )


@register("functions", "composition")
def composition(rng: random.Random, difficulty: str) -> Problem:
    """``f(g(x))`` for two linear functions, expanded.

    At hard the inner function is quadratic, which is where students stop
    being able to do it by inspection.
    """
    _, hi = RANGES[difficulty]
    a, b = nonzero_int(rng, 1, min(hi, 6)), nonzero_int(rng, -hi, hi)
    c, d = nonzero_int(rng, 1, min(hi, 6)), nonzero_int(rng, -hi, hi)

    if difficulty == "hard":
        g_expr = c * X**2 + d
        g_text = poly([c, 0, d])
    else:
        g_expr = c * X + d
        g_text = linear(c, d)

    f_text = linear(a, b)
    result = sp.expand(a * g_expr + b)
    degree = sp.degree(result, X)
    coeffs = [int(result.coeff(X, k)) for k in range(degree, -1, -1)]

    question = rf"f(x) = {f_text}, \quad g(x) = {g_text}, \quad f(g(x))"
    return _mk(question, poly(coeffs), result, "composition", difficulty,
               kind="composition")


@register("functions", "transformation_equation")
def transformation_equation(rng: random.Random, difficulty: str) -> Problem:
    """Apply a stated shift/stretch/reflection to a parent function.

    The answer is the transformed *equation*, which sympy can check, rather
    than a sentence describing the motion, which it cannot.
    """
    name = pick(rng, tuple(PARENTS))
    build = PARENTS[name]

    span = SHIFT[difficulty]
    h = nonzero_int(rng, -span, span)   # horizontal shift
    k = nonzero_int(rng, -span, span)   # vertical shift
    a = 1
    lo_a, hi_a = STRETCH[difficulty]
    if hi_a > 1:
        a = nonzero_int(rng, lo_a, hi_a)
        if rng.random() < 0.4:
            a = -a

    inner = X - h
    expr = sp.expand(a * build(inner) + k)

    inner_text = linear(1, -h)
    body = name.replace("x", f"({inner_text})")
    scaled = body if a == 1 else f"{coeff(a, '')}{body}"
    answer = terms(scaled, num(k))

    moves = []
    moves.append(f"shifted right {h}" if h > 0 else f"shifted left {-h}")
    if a != 1:
        if a < 0:
            moves.append("reflected over the $x$-axis")
        if abs(a) != 1:
            moves.append(f"vertically stretched by {abs(a)}")
    moves.append(f"shifted up {k}" if k > 0 else f"shifted down {-k}")
    description = ", ".join(moves)

    question = (
        f"The parent function ${name}$ is transformed as follows: "
        f"{description}. "
        f"Write the equation of the transformed function."
    )
    return Problem(
        question_latex=question,
        answer_latex=f"$g(x) = {answer}$",
        answer_expr=expr,
        topic="functions",
        subskill="transformation_equation",
        difficulty=difficulty,
        verify={"kind": "transformation"},
    )


SUB_VARS = ("a", "b", "c", "h", "j", "k", "m", "n", "p", "q", "x", "y")
SUB_VAL_SPAN = {"easy": 6, "medium": 8, "hard": 9}
SUB_COEF = {"easy": (1, 3), "medium": (1, 4), "hard": (1, 5)}
SUB_CONST = {"easy": 6, "medium": 9, "hard": 12}


@register("functions", "substitution")
def substitution(rng: random.Random, difficulty: str) -> Problem:
    """Multi-variable substitution, Kuta-style: evaluate an expression in two
    named variables at given integer values.

    The expression *structure* is sampled, not fixed: easy stays linear in
    each variable, medium adds a squared variable, and hard adds a squared
    parenthesized binomial or a product of two binomials -- the point where
    students have to expand before substituting (or substitute first and
    avoid expanding at all). Every term is built from real sympy symbols, so
    the printed key is safe by construction; no f-string coefficient joins.
    """
    v1_name, v2_name = sorted(rng.sample(SUB_VARS, 2))
    s1, s2 = sp.Symbol(v1_name), sp.Symbol(v2_name)

    span = SUB_VAL_SPAN[difficulty]
    if difficulty == "easy":
        val1, val2 = rng.randint(1, span), rng.randint(1, span)
    else:
        val1, val2 = nonzero_int(rng, -span, span), nonzero_int(rng, -span, span)

    lo, hi = SUB_COEF[difficulty]
    const_span = SUB_CONST[difficulty]

    def rand_coeff():
        return rng.choice((-1, 1)) * rng.randint(lo, hi)

    terms = [rand_coeff() * s1]  # guarantees v1 appears

    if difficulty == "easy":
        terms.append(rand_coeff() * s2)  # guarantees v2 appears
    elif difficulty == "medium":
        v = pick(rng, (s1, s2))
        other = s2 if v is s1 else s1
        terms.append(rand_coeff() * v ** 2)
        terms.append(rand_coeff() * other)  # guarantees the other var appears
    else:  # hard
        sign = rng.choice((1, -1))
        if rng.random() < 0.5:
            coeff = rng.randint(1, 2)
            terms.append(coeff * (s1 + sign * s2) ** 2)
        else:
            const = nonzero_int(rng, -3, 3)
            terms.append((s1 + s2) * (s1 - s2 + const))
        if rng.random() < 0.5:
            terms.append(rand_coeff() * s1 * s2)

    if difficulty != "easy" and rng.random() < 0.5:
        terms.append(rand_coeff() * pick(rng, (s1, s2)))

    if difficulty == "easy" or rng.random() < 0.7:
        terms.append(sp.Integer(nonzero_int(rng, -const_span, const_span)))

    display_expr = sp.Add(*terms, evaluate=False)
    answer = sum(int(t.subs({s1: val1, s2: val2})) for t in terms)
    answer_expr = sp.Integer(answer)

    question = (
        f"{sp.latex(display_expr)}, \\quad "
        f"{v1_name} = {val1},\\ {v2_name} = {val2}"
    )
    return _mk(question, sp.latex(answer_expr), answer_expr, "substitution",
               difficulty, kind="substitution")


EVAL_INPUT = {"easy": 6, "medium": 10, "hard": 15}


@register("functions", "evaluate_function")
def evaluate_function(rng: random.Random, difficulty: str) -> Problem:
    """``f(x) = ...``, find ``f(k)`` -- the first thing students meet.

    Quadratic at medium and up, so substituting a negative input actually
    matters: f(-3) with an x^2 term is where sign errors surface.
    """
    _, hi = RANGES[difficulty]
    span = EVAL_INPUT[difficulty]
    k = nonzero_int(rng, -span, span)

    if difficulty == "easy":
        a, b = nonzero_int(rng, 1, hi), nonzero_int(rng, -hi, hi)
        expr = a * X + b
        text = linear(a, b)
    else:
        a = nonzero_int(rng, 1, min(hi, 6))
        b, c = nonzero_int(rng, -hi, hi), nonzero_int(rng, -hi, hi)
        expr = a * X**2 + b * X + c
        text = poly([a, b, c])

    value = sp.Integer(expr.subs(X, k))
    question = f"f(x) = {text}, \\quad f({k})"
    return _mk(question, sp.latex(value), value, "evaluate_function", difficulty,
               kind="evaluate_function")


@register("functions", "domain_range")
def domain_range(rng: random.Random, difficulty: str) -> Problem:
    """Domain and range of a finite relation given as ordered pairs.

    A finite set has an exactly checkable answer; "all reals except 3" would
    need interval parsing for no extra pedagogical value at this level.
    """
    span = EVAL_INPUT[difficulty]
    size = {"easy": 4, "medium": 5, "hard": 6}[difficulty]
    xs = rng.sample(range(-span, span + 1), size)
    ys = [nonzero_int(rng, -span, span) for _ in xs]

    pairs = ", ".join(f"({x}, {y})" for x, y in zip(xs, ys))
    domain = ", ".join(str(v) for v in sorted(xs))
    rng_text = ", ".join(str(v) for v in sorted(set(ys)))
    question = f"$\\{{{pairs}\\}}$"
    answer = f"domain: $\\{{{domain}\\}}$; range: $\\{{{rng_text}\\}}$"
    return Problem(
        question_latex=question,
        answer_latex=answer,
        answer_expr=(tuple(sorted(xs)), tuple(sorted(set(ys)))),
        topic="functions",
        subskill="domain_range",
        difficulty=difficulty,
        verify={"kind": "domain_range"},
    )


# Coefficient ranges for the literal-equation family below.
LITERAL_COEF = {"easy": (2, 6), "medium": (2, 10), "hard": (2, 15)}
LITERAL_VARS = ("a", "b", "c", "k", "n", "p", "q", "r", "s", "t", "u", "v")


@register("functions", "literal_equation")
def literal_equation(rng: random.Random, difficulty: str) -> Problem:
    """Rearrange an equation in several variables for one of them.

    A fixed bank of real formulas (A = lw, d = rt, ...) would be a hardcoded
    problem list, which invariant 1 forbids -- eight formulas is eight
    problems, forever. Instead the *shape* is fixed and everything in it is
    sampled: coefficients, variable names, and which variable to isolate.
    The shapes mirror the formulas students actually rearrange.
    """
    lo, hi = LITERAL_COEF[difficulty]
    y, x, z = rng.sample(LITERAL_VARS, 3)
    a = nonzero_int(rng, lo, hi)
    style = rng.randrange(3)

    if style == 0:
        # a*x + b*y = c  ->  solve for y
        b = nonzero_int(rng, lo, hi)
        formula = f"{coeff(a, x)} + {coeff(b, y)} = {z}"
        solution = rf"\dfrac{{{z} - {coeff(a, x)}}}{{{b}}}"
    elif style == 1:
        # z = a*x*y  ->  solve for y
        formula = f"{z} = {coeff(a, f'{x}{y}')}"
        solution = rf"\dfrac{{{z}}}{{{coeff(a, x)}}}"
    else:
        # z = a*(x + y)  ->  solve for y
        formula = f"{z} = {coeff(a, '')}({x} + {y})"
        solution = rf"\dfrac{{{z}}}{{{a}}} - {x}"

    question = f"${formula}$, solve for ${y}$"
    return Problem(
        question_latex=question,
        answer_latex=f"${y} = {solution}$",
        # A string, deliberately: the real check is _v_literal_equation, which
        # solves the printed equation with sympy and confirms the printed key
        # is one of its solutions. Storing a sympy expression here would give
        # the generic key check something to compare against, but it would be
        # comparing the generator to itself.
        answer_expr=f"{y} = {solution}",
        topic="functions",
        subskill="literal_equation",
        difficulty=difficulty,
        verify={"kind": "literal_equation"},
    )
