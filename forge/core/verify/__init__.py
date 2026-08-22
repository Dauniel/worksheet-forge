"""Independent re-derivation of every answer.

The rule: verification must not trust the generator's arithmetic. Wherever
possible we parse ``question_latex`` back into sympy from the *rendered string
the student will see* and re-derive the answer from scratch. A mismatch fails
the build; no PDF is ever emitted with an unverified key.

This package was one 1,600-line module. It is split by subject --
``parsing`` (LaTeX -> sympy and exact comparison), then ``algebra``,
``geometry`` and ``data`` for the strategies themselves -- with the strategy
registry and the entry points below. ``verify_all`` and ``VerificationError``
import from here exactly as they did before the split.
"""

from __future__ import annotations

import re
import tokenize
from typing import List

import sympy as sp

from ..problem import Problem, normalize

from .parsing import VerificationError, latex_relation_to_sympy, latex_to_sympy  # noqa: F401

from .parsing import (
    VerificationError,
    _equal,
    _mixed_to_sympy,
)
from .algebra import (
    _v_classify_polynomial,
    _v_standard_form,
    _v_simplify_radical_vars,
    _v_vertex_and_direction,
    _v_vertex_form_complete_square,
    _v_complete_square_blanks,
    _v_solve_quadratic_no_real,
    _v_composition,
    _v_property,
    _v_compound_or,
    _v_domain_range,
    _v_evaluate_function,
    _v_literal_equation,
    _v_substitution,
    _v_trig_amplitude,
    _v_trig_period,
    _v_trig_phase_shift,
    _v_inverse_function,
    _v_transformation,
    _v_abs_inequality,
    _v_abs_solve,
    _v_arithmetic_nth_term,
    _v_arithmetic_series_sum,
    _v_classify_system,
    _v_complex_arith,
    _v_compound_inequality,
    _v_condense_log,
    _v_evaluate,
    _v_geometric_nth_term,
    _v_inequality,
    _v_line_through_points,
    _v_multiply_rational,
    _v_point_in_inequality,
    _v_point_slope,
    _v_power_of_i,
    _v_quadratic_vertex,
    _v_simplify,
    _v_simplify_rational,
    _v_slope_and_line,
    _v_slope_from_points,
    _v_slope_intercept,
    _v_slope_intercept_standard,
    _v_solve,
    _v_solve_exponential,
    _v_solve_logarithmic,
    _v_solve_quadratic,
    _v_solve_system,
    _v_system_point_in_inequality,
)
from .geometry import (
    _v_angle_complementary,
    _v_angle_polygon_sum,
    _v_angle_supplementary,
    _v_angle_transversal,
    _v_angle_triangle,
    _v_coord_distance,
    _v_coord_midpoint,
    _v_coord_reflect,
    _v_coord_translate,
    _v_geo_cone_volume,
    _v_geo_cylinder_sa,
    _v_geo_cylinder_volume,
    _v_geo_sphere_volume,
    _v_trig_law_of_cosines,
    _v_trig_law_of_sines,
    _v_degree_radian_conversion,
    _v_exact_trig_value,
    _v_geo_circle_area,
    _v_geo_circle_circumference,
    _v_geo_pythagorean,
    _v_geo_rect_prism_sa,
    _v_geo_rect_prism_volume,
    _v_geo_rectangle_area,
    _v_geo_square_area,
    _v_geo_trapezoid_area,
    _v_geo_tri_prism_sa,
    _v_geo_tri_prism_volume,
    _v_geo_triangle_area,
    _v_right_triangle_find_angle,
    _v_special_triangle_hyp,
)
from .data import (
    _v_growth_decay,
    _v_count_combination,
    _v_count_permutation,
    _v_stat_five_number,
    _v_lcm,
    _v_prime_factorization,
    _v_decimal_to_percent,
    _v_percent_to_decimal,
    _v_classify,
    _v_gcf,
    _v_commission,
    _v_estimate_percent,
    _v_markup_discount,
    _v_percent_change,
    _v_percent_error,
    _v_percent_of,
    _v_prob_dependent,
    _v_prob_independent,
    _v_prob_simple,
    _v_sci_from_scientific,
    _v_sci_multiply_divide,
    _v_sci_to_scientific,
    _v_stat_mean,
    _v_stat_median,
    _v_stat_mode,
    _v_stat_range,
    _v_tax_tip,
    _v_unit_price_comparison,
    _v_unit_rate,
    _v_word,
)


STRATEGIES = {
    "evaluate": _v_evaluate,
    "simplify": _v_simplify,
    "solve": _v_solve,
    "inverse_function": _v_inverse_function,
    "composition": _v_composition,
    "property": _v_property,
    "transformation": _v_transformation,
    "evaluate_function": _v_evaluate_function,
    "substitution": _v_substitution,
    "domain_range": _v_domain_range,
    "literal_equation": _v_literal_equation,
    "trig_amplitude": _v_trig_amplitude,
    "trig_period": _v_trig_period,
    "trig_phase_shift": _v_trig_phase_shift,
    "inequality": _v_inequality,
    "abs_solve": _v_abs_solve,
    "slope_from_points": _v_slope_from_points,
    "line_through_points": _v_line_through_points,
    "slope_intercept": _v_slope_intercept,
    "slope_and_line": _v_slope_and_line,
    "slope_intercept_standard": _v_slope_intercept_standard,
    "point_slope": _v_point_slope,
    "percent_of": _v_percent_of,
    "percent_change": _v_percent_change,
    "word": _v_word,
    "geo_rectangle_area": _v_geo_rectangle_area,
    "geo_square_area": _v_geo_square_area,
    "compound_inequality": _v_compound_inequality,
    "compound_or": _v_compound_or,
    "sci_to_scientific": _v_sci_to_scientific,
    "sci_from_scientific": _v_sci_from_scientific,
    "sci_multiply_divide": _v_sci_multiply_divide,
    "growth_decay": _v_growth_decay,
    "count_permutation": _v_count_permutation,
    "count_combination": _v_count_combination,
    "stat_five_number": _v_stat_five_number,
    "prob_simple": _v_prob_simple,
    "prob_independent": _v_prob_independent,
    "prob_dependent": _v_prob_dependent,
    "lcm": _v_lcm,
    "prime_factorization": _v_prime_factorization,
    "decimal_to_percent": _v_decimal_to_percent,
    "percent_to_decimal": _v_percent_to_decimal,
    "stat_mean": _v_stat_mean,
    "stat_median": _v_stat_median,
    "stat_mode": _v_stat_mode,
    "stat_range": _v_stat_range,
    "geo_pythagorean": _v_geo_pythagorean,
    "angle_complementary": _v_angle_complementary,
    "angle_supplementary": _v_angle_supplementary,
    "angle_triangle": _v_angle_triangle,
    "angle_polygon_sum": _v_angle_polygon_sum,
    "angle_transversal": _v_angle_transversal,
    "coord_distance": _v_coord_distance,
    "coord_midpoint": _v_coord_midpoint,
    "coord_translate": _v_coord_translate,
    "coord_reflect": _v_coord_reflect,
    "geo_cylinder_volume": _v_geo_cylinder_volume,
    "geo_cone_volume": _v_geo_cone_volume,
    "geo_sphere_volume": _v_geo_sphere_volume,
    "geo_cylinder_sa": _v_geo_cylinder_sa,
    "trig_law_of_cosines": _v_trig_law_of_cosines,
    "trig_law_of_sines": _v_trig_law_of_sines,
    "geo_circle_area": _v_geo_circle_area,
    "geo_circle_circumference": _v_geo_circle_circumference,
    "geo_triangle_area": _v_geo_triangle_area,
    "geo_trapezoid_area": _v_geo_trapezoid_area,
    "geo_rect_prism_volume": _v_geo_rect_prism_volume,
    "geo_rect_prism_sa": _v_geo_rect_prism_sa,
    "geo_tri_prism_volume": _v_geo_tri_prism_volume,
    "geo_tri_prism_sa": _v_geo_tri_prism_sa,
    "classify": _v_classify,
    "gcf": _v_gcf,
    "estimate_percent": _v_estimate_percent,
    "markup_discount": _v_markup_discount,
    "percent_error": _v_percent_error,
    "commission": _v_commission,
    "tax_tip": _v_tax_tip,
    "unit_rate": _v_unit_rate,
    "unit_price_comparison": _v_unit_price_comparison,
    "solve_system": _v_solve_system,
    "classify_system": _v_classify_system,
    "solve_quadratic": _v_solve_quadratic,
    "quadratic_vertex": _v_quadratic_vertex,
    "simplify_rational": _v_simplify_rational,
    "multiply_rational": _v_multiply_rational,
    "abs_inequality": _v_abs_inequality,
    "point_in_inequality": _v_point_in_inequality,
    "system_point_in_inequality": _v_system_point_in_inequality,
    "complex_arith": _v_complex_arith,
    "power_of_i": _v_power_of_i,
    "solve_exponential": _v_solve_exponential,
    "solve_logarithmic": _v_solve_logarithmic,
    "condense_log": _v_condense_log,
    "arithmetic_nth_term": _v_arithmetic_nth_term,
    "geometric_nth_term": _v_geometric_nth_term,
    "arithmetic_series_sum": _v_arithmetic_series_sum,
    "special_triangle_hypotenuse": _v_special_triangle_hyp,
    "right_triangle_find_angle": _v_right_triangle_find_angle,
    "degree_radian_conversion": _v_degree_radian_conversion,
    "exact_trig_value": _v_exact_trig_value,
    "classify_polynomial": _v_classify_polynomial,
    "standard_form": _v_standard_form,
    "simplify_radical_vars": _v_simplify_radical_vars,
    "vertex_and_direction": _v_vertex_and_direction,
    "vertex_form_complete_square": _v_vertex_form_complete_square,
    "complete_square_blanks": _v_complete_square_blanks,
    "solve_quadratic_no_real": _v_solve_quadratic_no_real,
}

def _check_verify_fragments(p: Problem) -> None:
    """Any ``expr``/``lhs``/``rhs`` stored in ``p.verify`` must literally
    appear in the printed ``question_latex`` -- otherwise nothing enforces
    that the verified string is what the student actually sees. The one
    legitimate exception is prose (word problems), where the model is
    intentionally not literal text in the sentence; those opt out explicitly
    with ``"prose": True``.
    """
    if p.verify.get("prose") is True:
        return
    qn = normalize(p.question_latex)
    for key in ("expr", "lhs", "rhs"):
        if key in p.verify:
            frag = normalize(str(p.verify[key]))
            if frag not in qn:
                raise VerificationError(
                    f"{p.topic}/{p.subskill}: verify[{key!r}] = {p.verify[key]!r} does not "
                    f"appear in the printed question {p.question_latex!r}"
                )

def verify_problem(p: Problem) -> None:
    kind = p.verify.get("kind", "evaluate")
    try:
        strategy = STRATEGIES[kind]
    except KeyError:
        raise VerificationError(f"unknown verification kind {kind!r}") from None
    strategy(p)
    _check_verify_fragments(p)
    _check_answer_latex(p)

def _check_answer_latex(p: Problem) -> None:
    """The *printed* key must agree with the verified symbolic answer."""
    text = p.verify.get("answer_check", p.answer_latex)
    if text is None:
        return
    s = text.strip().strip("$").strip()
    s = re.sub(r"^[A-Za-z]\s*=\s*", "", s)
    try:
        printed = _mixed_to_sympy(s)
    except (VerificationError, sp.SympifyError, TypeError, SyntaxError, tokenize.TokenError):
        return  # non-numeric keys (e.g. inequalities) are checked by their strategy
    target = p.answer_expr
    # Sets, relations, multi-part keys, and plain-string answers (e.g. "Option
    # A") are their strategy's job, not this check -- only plain numeric or
    # algebraic expressions compare meaningfully as sympy objects here.
    opaque = (list, tuple, frozenset, set, sp.Set, sp.core.relational.Relational, str)
    if isinstance(target, opaque) or isinstance(printed, opaque):
        return
    if not _equal(printed, target):
        raise VerificationError(
            f"{p.topic}/{p.subskill}: printed key {p.answer_latex!r} reads as {printed}, "
            f"but the verified answer is {target}"
        )

def verify_all(problems: List[Problem]) -> None:
    errors = []
    for p in problems:
        try:
            verify_problem(p)
        except VerificationError as e:
            errors.append(str(e))
        except Exception as e:
            # Any other exception (IndexError, KeyError, ...) means a
            # generator produced something malformed -- fail this one
            # problem cleanly instead of crashing the whole build with a
            # bare traceback.
            errors.append(
                f"{p.topic}/{p.subskill}: unexpected {type(e).__name__} during "
                f"verification: {e}"
            )
    if errors:
        raise VerificationError(
            f"{len(errors)} answer(s) failed verification:\n  - "
            + "\n  - ".join(errors)
        )
