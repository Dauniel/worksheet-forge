"""Topic catalog: turns a bare list of topics into a full worksheet spec.

This is what makes ``forge quick negatives fractions slope`` work. Each entry
supplies the section grouping, the directions, the work-space, the column
count, and a default progression of subskills -- the editorial defaults a
tutor would otherwise write out by hand in YAML.

A topic emits *one section per group*, because directions are stated once per
section and items are bare. Two subskills can only share a section if one set
of directions honestly covers both: "Evaluate each expression" covers all four
negatives subskills, but "solve the proportion" and "find the percent change"
are different instructions and get their own parts.

Nothing here selects *problems*; it only selects which generators run and how
many times. Problem selection stays in seeded code.

## Column defaults

Two columns is a layout choice, not a topic label -- the test is whether the
longest item in a section fits comfortably in half the text width. Short,
purely symbolic items (order of operations, one-line equations/inequalities,
exponent rules, roots, classifying a single number, combining/factoring a
short expression) default to two columns; anything with real prose (word
problems, percent applications framed as a sentence, unit-rate comparisons)
or a TikZ figure (every geometry subskill) stays single-column. See
``forge/build.py`` for the runtime guard that forces a figure-bearing section
back to one column even if a hand-written spec asks for more.
"""

from __future__ import annotations

from typing import Dict, List

from .core.registry import all_generators


def _s(subskill: str, difficulty: str, group: str = "", directions: str = "",
       workspace: str = "", share: int = 1, columns: int = 0) -> dict:
    return {
        "subskill": subskill,
        "difficulty": difficulty,
        "share": share,
        "group": group,
        "directions": directions,
        "workspace": workspace,
        "columns": columns,
    }


CATALOG: Dict[str, dict] = {
    "negatives": {
        "name": "Negative Number Operations",
        "directions": "Evaluate each expression completely.",
        "workspace": "1.1cm",
        "progression": [
            _s("add_sub_integers", "easy", columns=2),
            _s("mul_div_integers", "easy", columns=2),
            _s("mixed_operations", "medium", columns=2),
            _s("order_of_operations", "medium", columns=2),
        ],
    },
    "fractions": {
        "name": "Fractions",
        "directions": "Evaluate. Write every answer in lowest terms.",
        "workspace": "1.4cm",
        "progression": [
            _s("add_sub_fractions", "easy", columns=2),
            _s("mul_div_fractions", "easy", columns=2),
            _s("mixed_numbers", "medium", columns=2),
            _s("simplify_fractions", "medium",
               group="Writing Fractions in Lowest Terms",
               directions="Write each fraction in lowest terms.",
               workspace="1.1cm", columns=2),
        ],
    },
    "like_terms": {
        "name": "Simplifying Expressions",
        "directions": "Simplify each expression.",
        "workspace": "1.3cm",
        "progression": [
            _s("combine_like_terms", "easy", columns=2),
            _s("distribute_and_combine", "medium", columns=2),
            _s("add_subtract_linear", "medium",
               group="Adding and Subtracting Linear Expressions",
               directions="Add or subtract, then simplify.",
               workspace="1.4cm", columns=2),
            _s("factor_gcf", "medium",
               group="Factoring Linear Expressions",
               directions="Factor out the greatest common factor.",
               workspace="1.3cm", columns=2),
        ],
    },
    "linear_equations": {
        "name": "Solving Linear Equations",
        "directions": "Solve each equation for $x$. Show your steps.",
        "workspace": "2.0cm",
        "progression": [
            _s("one_step", "easy", columns=2),
            _s("two_step", "easy", columns=2),
            _s("with_distribution", "medium", columns=2),
            _s("multi_step_both_sides", "medium", columns=2),
            # Fractional coefficients / variable-over-a-denominator forms and
            # cross-multiplying proportions are the two hardest equation
            # shapes here -- same "solve for x" directions as the rest, so
            # they stay in the same section rather than getting their own.
            # Their \dfrac stacks are only ever a single numerator/denominator
            # deep (never a fraction of a fraction), so they read fine at
            # half the text width -- checked visually before setting this.
            _s("fractional", "hard", columns=2),
            _s("proportion", "hard", columns=2),
        ],
    },
    "slope": {
        "name": "Slope and Linear Graphs",
        "directions": "Identify the slope $m$ and the $y$-intercept $b$ of each line.",
        "workspace": "1.2cm",
        "progression": [
            _s("identify_slope_intercept", "easy", columns=2),
            _s("slope_from_two_points", "easy",
               group="Slope Through Two Points",
               directions="Find the slope of the line through each pair of points.",
               workspace="1.6cm", columns=2),
            _s("equation_from_two_points", "medium",
               group="Equations From Two Points",
               directions=(
                   "Write the equation of the line through each pair of points "
                   "in slope-intercept form."
               ),
               workspace="2.0cm", columns=2),
            _s("point_slope_to_equation", "medium",
               group="Equations From a Slope and a Point",
               directions=(
                   "Write the equation of each line in slope-intercept form."
               ),
               workspace="2.0cm", columns=2),
            _s("slope_and_equation", "medium",
               group="Slope and Equation From Two Points",
               directions=(
                   "Find the slope of the line through each pair of points, then write "
                   "the equation of the line in slope-intercept form."
               ),
               workspace="2.0cm", columns=2),
            _s("identify_from_standard", "medium",
               group="Rewriting in Slope-Intercept Form",
               directions=(
                   "Rewrite each equation in slope-intercept form, then identify the "
                   "slope $m$ and the $y$-intercept $b$."
               ),
               workspace="1.8cm", columns=2),
        ],
    },
    "ratios_percents": {
        "name": "Proportions",
        "directions": "Solve each proportion for $x$.",
        "workspace": "1.5cm",
        "progression": [
            _s("proportions", "easy", columns=2),
            _s("percent_of", "easy",
               group="Percent of a Number",
               directions="Find each value.",
               workspace="1.3cm", columns=2),
            _s("percent_change", "medium",
               group="Percent Change",
               directions=(
                   "Find the percent change from the first value to the second. "
                   "An increase is positive, a decrease is negative."
               ),
               workspace="1.6cm", columns=2),
        ],
    },
    "exponents": {
        "name": "Exponent Rules",
        "directions": "Simplify. Write answers with positive exponents.",
        "workspace": "1.3cm",
        "progression": [
            _s("product_rule", "easy", columns=2),
            _s("quotient_rule", "easy", columns=2),
            _s("power_rule", "medium", columns=2),
            _s("negative_exponents", "medium", columns=2),
            _s("zero_and_negative_powers", "medium", columns=2),
            # Stacks several rules at once (nested powers, two-variable
            # quotients) -- the hardest tier here. Still a single line, no
            # taller than power_rule's own parenthesized-power items, so it
            # reads fine at half width; checked visually before setting this.
            _s("combined_rules", "hard", columns=2),
        ],
    },
    "inequalities": {
        "name": "Linear Inequalities",
        "directions": "Solve each inequality for $x$.",
        "workspace": "1.8cm",
        "progression": [
            _s("one_step", "easy", columns=2),
            _s("two_step", "easy", columns=2),
            _s("multi_step_both_sides", "medium", columns=2),
            _s("fractional", "hard", columns=2),
            _s("fractional_both_sides", "hard", columns=2),
        ],
    },
    "word_problems": {
        "name": "Word Problems",
        "directions": "Define a variable, write an equation, and solve.",
        "workspace": "3.2cm",
        "progression": [
            _s("linear_model", "easy", columns=1),
            _s("rate_model", "easy", columns=1),
            _s("percent_model", "medium", columns=1),
            _s("comparison_model", "medium", columns=1),
        ],
    },
    "number_sense": {
        "name": "Classifying Numbers",
        "directions": (
            "Classify each number using all that apply: rational, irrational, "
            "whole, integer."
        ),
        "workspace": "1.3cm",
        "progression": [
            _s("classify", "easy", columns=2),
        ],
    },
    "roots": {
        "name": "Roots",
        "directions": "Evaluate each root.",
        "workspace": "1.2cm",
        "progression": [
            _s("square_root", "easy", columns=2),
            _s("cube_root", "easy", columns=2),
            _s("simplify_radical", "medium",
               group="Simplifying Radicals",
               directions="Simplify each radical completely.",
               workspace="1.3cm", columns=2),
            _s("simplify_cube_radical", "medium",
               group="Simplifying Radicals",
               directions="Simplify each radical completely.",
               workspace="1.3cm", columns=2),
        ],
    },
    "geometry": {
        "name": "Geometry",
        "directions": "Find the area of each figure.",
        "workspace": "1.6cm",
        "progression": [
            # Every geometry subskill renders a TikZ figure that needs the
            # full text width -- always 1 column. forge/build.py also
            # enforces this at runtime regardless of what a spec requests.
            _s("area_rectangle", "easy", columns=1),
            _s("area_square", "easy", columns=1),
            _s("area_triangle", "easy", columns=1),
            _s("area_trapezoid", "medium", columns=1),
            # Circles get their own parts: "leave it in terms of pi" is a real
            # instruction that must not appear over the rectangles, and area
            # and circumference cannot share one honest sentence either.
            _s("area_circle", "medium",
               group="Area of Circles",
               directions=("Find the area of each circle. Leave your answer "
                           "in terms of $\\pi$."),
               workspace="1.6cm", columns=1),
            _s("circumference_circle", "medium",
               group="Circumference of Circles",
               directions=("Find the circumference of each circle. Leave your "
                           "answer in terms of $\\pi$."),
               workspace="1.6cm", columns=1),
            _s("volume_rect_prism", "medium",
               group="Volume of Prisms",
               directions="Find the volume of each prism.",
               workspace="1.8cm", columns=1),
            _s("volume_tri_prism", "medium",
               group="Volume of Prisms",
               directions="Find the volume of each prism.",
               workspace="1.8cm", columns=1),
            _s("surface_area_rect_prism", "hard",
               group="Surface Area of Prisms",
               directions="Find the surface area of each prism.",
               workspace="1.8cm", columns=1),
            _s("surface_area_tri_prism", "hard",
               group="Surface Area of Prisms",
               directions="Find the surface area of each prism.",
               workspace="1.8cm", columns=1),
        ],
    },
    "percent_apps": {
        "name": "Percent Applications",
        "directions": "Solve the percent proportion for $x$.",
        "workspace": "1.5cm",
        "progression": [
            # Symbolic, same shape as ratios_percents.proportions -- fits two columns.
            _s("percent_proportion", "easy", columns=2),
            # Everything below is a full sentence -- needs the full width.
            _s("estimate_percent", "easy",
               group="Estimating Percents",
               directions="Estimate using the friendly benchmark given.",
               workspace="1.4cm", columns=1),
            _s("markup_discount", "medium",
               group="Markup and Discount",
               directions="Find the new price.",
               workspace="2.0cm", columns=1),
            _s("percent_error", "medium",
               group="Percent Error",
               directions="Find the percent error.",
               workspace="2.0cm", columns=1),
            _s("commission", "medium",
               group="Commission",
               directions="Find the commission earned.",
               workspace="2.0cm", columns=1),
            _s("tax_tip", "medium",
               group="Tax and Tip",
               directions="Find the total, including tax or tip.",
               workspace="2.0cm", columns=1),
        ],
    },
    "absolute_value": {
        "name": "Absolute Value",
        "directions": "Solve each equation for $x$.",
        "workspace": "1.8cm",
        "progression": [
            _s("evaluate", "easy",
               group="Evaluating Absolute Value Expressions",
               directions="Evaluate each expression completely.",
               workspace="1.2cm", columns=2),
            _s("solve_basic", "medium", columns=2),
            _s("solve_with_coefficient", "hard", columns=2),
            _s("multi_step", "hard", columns=2),
            _s("solve_inequality", "hard",
               group="Absolute Value Inequalities",
               directions="Solve each inequality for $x$.",
               workspace="1.8cm", columns=2),
        ],
    },
    "unit_rates": {
        "name": "Unit Rates",
        "directions": "Find the unit rate.",
        "workspace": "1.8cm",
        "progression": [
            _s("unit_rate", "easy", columns=1),
            _s("unit_price_comparison", "medium",
               group="Unit Price Comparison",
               directions="Determine which option is the better price per unit.",
               workspace="2.0cm", columns=1),
        ],
    },
    "systems": {
        "name": "Systems of Linear Equations",
        "directions": "Solve each system of equations.",
        "workspace": "2.4cm",
        "progression": [
            _s("substitution", "easy",
               group="Solving by Substitution",
               directions="Solve each system by substitution.",
               workspace="2.4cm", columns=1),
            _s("elimination", "medium",
               group="Solving by Elimination",
               directions="Solve each system by elimination.",
               workspace="2.4cm", columns=1),
            _s("classify", "hard",
               group="Classifying Systems",
               directions=(
                   "State whether each system has one solution, no solution, or "
                   "infinitely many. If there is one solution, give it as a point."
               ),
               workspace="2.4cm", columns=1),
        ],
    },
    "quadratics": {
        "name": "Quadratic Equations",
        "directions": "Solve each equation for $x$.",
        "workspace": "2.4cm",
        "progression": [
            _s("solve_by_factoring", "easy",
               group="Solving by Factoring",
               directions="Solve each equation by factoring.",
               workspace="2.2cm", columns=2),
            _s("quadratic_formula", "medium",
               group="The Quadratic Formula",
               directions="Solve each equation using the quadratic formula.",
               workspace="2.8cm", columns=2),
            _s("find_vertex", "medium",
               group="Vertex of a Parabola",
               directions="Find the vertex of each parabola.",
               workspace="1.8cm", columns=2),
        ],
    },
    "rational_expressions": {
        "name": "Rational Expressions",
        "directions": "Simplify each expression. State any excluded values.",
        "workspace": "1.8cm",
        "progression": [
            _s("simplify", "easy", columns=2),
            _s("multiply", "medium",
               group="Multiplying Rational Expressions",
               directions="Multiply and simplify each expression.",
               workspace="1.8cm", columns=2),
        ],
    },
    "polynomials": {
        "name": "Polynomials",
        "directions": "Multiply each pair of binomials.",
        "workspace": "1.6cm",
        "progression": [
            _s("multiply_binomials", "easy", columns=2),
            _s("factor_trinomial", "medium",
               group="Factoring Trinomials",
               directions="Factor each trinomial completely.",
               workspace="1.6cm", columns=2),
            _s("difference_of_squares", "medium",
               group="Factoring a Difference of Squares",
               directions="Factor each expression completely.",
               workspace="1.6cm", columns=2),
        ],
    },
    "variation": {
        "name": "Direct and Inverse Variation",
        "directions": "Solve each variation problem.",
        "workspace": "2.0cm",
        "progression": [
            _s("direct_variation", "easy", columns=1),
            _s("inverse_variation", "medium",
               group="Inverse Variation",
               directions="Solve each variation problem.",
               workspace="2.0cm", columns=1),
        ],
    },
    "radical_equations": {
        "name": "Radical Equations",
        "directions": "Solve each equation for $x$.",
        "workspace": "2.2cm",
        "progression": [
            _s("basic", "easy", columns=2),
            _s("multi_step", "medium",
               group="Isolating the Radical",
               directions="Solve each equation for $x$. Isolate the radical first.",
               workspace="2.2cm", columns=2),
            _s("check_extraneous", "hard",
               group="Checking for Extraneous Solutions",
               directions=(
                   "Solve each equation for $x$. Check your solution in the "
                   "original equation and reject it if it does not work."
               ),
               workspace="2.2cm", columns=2),
        ],
    },
    "graphing": {
        "name": "Graphing Linear Inequalities",
        "directions": "Determine whether the given point is a solution. Answer Yes or No.",
        "workspace": "1.0cm",
        "progression": [
            _s("point_in_solution", "easy", columns=1),
            _s("system_point_in_solution", "medium",
               group="Systems of Inequalities",
               directions=(
                   "Determine whether the given point is a solution to the system. "
                   "Answer Yes or No."
               ),
               workspace="1.0cm", columns=1),
        ],
    },
    "complex_numbers": {
        "name": "Complex Numbers",
        "directions": "Simplify each expression.",
        "workspace": "1.4cm",
        "progression": [
            _s("add_subtract", "easy", columns=2),
            _s("multiply", "medium",
               group="Multiplying Complex Numbers",
               directions="Multiply and simplify each expression.",
               workspace="1.4cm", columns=2),
            _s("powers_of_i", "hard",
               group="Powers of i",
               directions="Simplify each power of $i$.",
               workspace="1.2cm", columns=2),
        ],
    },
    "exponential_logarithms": {
        "name": "Exponential and Logarithmic Equations",
        "directions": "Solve each equation for $x$.",
        "workspace": "1.8cm",
        "progression": [
            _s("solve_exponential", "easy", columns=2),
            _s("solve_logarithmic", "medium",
               group="Solving Logarithmic Equations",
               directions="Solve each equation for $x$.",
               workspace="1.8cm", columns=2),
            _s("condense_log", "hard",
               group="Condensing Logarithms",
               directions="Write each expression as a single logarithm.",
               workspace="1.4cm", columns=2),
        ],
    },
    "sequences_series": {
        "name": "Sequences and Series",
        "directions": "Solve each problem.",
        "workspace": "1.8cm",
        "progression": [
            _s("arithmetic_nth_term", "easy", columns=1),
            _s("geometric_nth_term", "medium",
               group="Geometric Sequences",
               directions="Solve each problem.",
               workspace="1.8cm", columns=1),
            _s("arithmetic_series_sum", "hard",
               group="Arithmetic Series",
               directions="Solve each problem.",
               workspace="1.8cm", columns=1),
        ],
    },
    "right_triangle_trig": {
        "name": "Right Triangle Trigonometry",
        "directions": "Solve each problem. Give an exact answer.",
        "workspace": "2.0cm",
        "progression": [
            _s("special_triangle_hypotenuse", "easy", columns=1),
            _s("find_angle", "medium",
               group="Finding a Missing Angle",
               directions="Solve each problem. Give the angle in degrees.",
               workspace="2.0cm", columns=1),
        ],
    },
    "unit_circle": {
        "name": "The Unit Circle",
        "directions": "Convert each angle.",
        "workspace": "1.4cm",
        "progression": [
            _s("degree_radian_conversion", "easy", columns=2),
            _s("exact_trig_value", "medium",
               group="Exact Trig Values",
               directions="Evaluate each expression exactly.",
               workspace="1.4cm", columns=2),
        ],
    },
}

PART_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
DEFAULT_COUNT = 8


def known_topics() -> List[str]:
    return list(CATALOG)


def describe_topics() -> str:
    """Human-readable topic listing for ``forge topics``."""
    lines = []
    registered = all_generators()
    for topic, entry in CATALOG.items():
        subs = [
            e["subskill"] for e in entry["progression"]
            if (topic, e["subskill"]) in registered
        ]
        lines.append(f"  {topic:<18} {entry['name']}")
        lines.append(f"  {'':<18} subskills: {', '.join(subs)}")
    return "\n".join(lines)


def _apportion(total: int, shares: List[int]) -> List[int]:
    """Split ``total`` across shares, distributing the remainder from the top."""
    weight = sum(shares)
    base = [total * s // weight for s in shares]
    leftover = total - sum(base)
    i = 0
    while leftover > 0:
        base[i % len(base)] += 1
        leftover -= 1
        i += 1
    # A subskill allotted zero would silently vanish; give it at least one if
    # there is room to take from the largest bucket.
    for i, n in enumerate(base):
        if n == 0 and max(base) > 1:
            base[base.index(max(base))] -= 1
            base[i] = 1
    return base


def topic_subskills(topic: str) -> List[str]:
    """Subskill names available for ``topic``, in progression order."""
    return [e["subskill"] for e in CATALOG[topic]["progression"]]


def parse_request(token: str) -> tuple:
    """Parse a quick-mode topic token.

    ``negatives`` / ``negatives:12`` / ``negatives:12:hard``, optionally with
    a subskill selector attached to the topic with ``/``::

        slope/slope_from_two_points
        slope/slope_from_two_points+equation_from_two_points:12:hard

    Multiple subskills are joined with ``+`` -- not a comma, which the CLI
    already treats as a separator between whole tokens. Returns
    ``(topic, count, difficulty, subskills)``; ``subskills`` is ``None`` when
    no selector was given, meaning "use the topic's full progression".
    """
    text = str(token).strip()
    parts = [p.strip() for p in text.split(":")]
    head = parts[0]
    topic, _, sub_text = head.partition("/")
    topic = topic.strip()
    count = int(parts[1]) if len(parts) > 1 and parts[1] else DEFAULT_COUNT
    difficulty = parts[2] if len(parts) > 2 and parts[2] else None
    if topic not in CATALOG:
        raise KeyError(
            f"unknown topic {topic!r}. Known topics: {', '.join(known_topics())}"
        )
    if count < 1:
        raise ValueError(f"{topic}: count must be at least 1")
    if difficulty and difficulty not in ("easy", "medium", "hard"):
        raise ValueError(f"{topic}: unknown difficulty {difficulty!r}")

    subskills = None
    if "/" in head:
        subskills = [s.strip() for s in sub_text.split("+") if s.strip()]
        if not subskills:
            raise ValueError(
                f"{topic}: '/' given with no subskill. "
                f"Available: {', '.join(topic_subskills(topic))}"
            )
        available = topic_subskills(topic)
        unknown = [s for s in subskills if s not in available]
        if unknown:
            raise KeyError(
                f"{topic}: unknown subskill(s) {', '.join(repr(s) for s in unknown)}. "
                f"Available: {', '.join(available)}"
            )
        seen = set()
        subskills = [s for s in subskills if not (s in seen or seen.add(s))]
    return topic, count, difficulty, subskills


def spec_from_topics(
    tokens: List[str],
    title: str = "",
    header: str = "",
    difficulty: str = "",
) -> dict:
    """Build a full spec dict from a list of topic tokens."""
    if not tokens:
        raise ValueError("no topics given")

    sections = []
    for token in tokens:
        topic, count, topic_difficulty, subskills = parse_request(token)
        entry = CATALOG[topic]
        prog = entry["progression"]
        if subskills is not None:
            # Filtered in catalog order, not the order typed: the grouping
            # below merges *consecutive* entries sharing a group, so honoring
            # an arbitrary order would split a group into repeated sections.
            prog = [e for e in prog if e["subskill"] in set(subskills)]
        counts = _apportion(count, [e["share"] for e in prog])

        # One section per group; consecutive entries sharing a group merge.
        groups: List[dict] = []
        for e, n in zip(prog, counts):
            if n == 0:
                continue
            name = e["group"] or entry["name"]
            if not groups or groups[-1]["name"] != name:
                groups.append(
                    {
                        "name": name,
                        "directions": e["directions"] or entry["directions"],
                        "workspace": e["workspace"] or entry["workspace"],
                        "columns": e["columns"] or 1,
                        "problems": [],
                    }
                )
            groups[-1]["problems"].append(
                {
                    "topic": topic,
                    "subskill": e["subskill"],
                    "count": n,
                    "difficulty": topic_difficulty or difficulty or e["difficulty"],
                }
            )
        sections.extend(groups)

    for i, sec in enumerate(sections):
        sec["name"] = f"Part {PART_LETTERS[i % 26]}: {sec['name']}"

    names = list(dict.fromkeys(CATALOG[parse_request(t)[0]]["name"] for t in tokens))
    return {
        "title": title or ", ".join(names),
        "header": header or title or _short_header(names),
        "sections": sections,
    }


def _short_header(names: List[str]) -> str:
    joined = ", ".join(names)
    if len(joined) <= 38:
        return joined
    return f"{names[0]} + {len(names) - 1} more"
