"""``forge quick topic/subskill`` -- targeting part of a topic's progression.

Without a selector a topic emits its whole progression, which is the right
default for review but wrong for drilling: a student stuck on slope-from-two-
points does not want six of the eight problems to be something else. The
selector narrows which generators run; it never touches how problems are
drawn.
"""

from __future__ import annotations

import pytest

from forge.catalog import CATALOG, parse_request, spec_from_topics, topic_subskills


def _subskills_in(spec) -> list:
    return [p["subskill"] for sec in spec["sections"] for p in sec["problems"]]


def _total(spec) -> int:
    return sum(p["count"] for sec in spec["sections"] for p in sec["problems"])


def test_no_selector_keeps_the_full_progression():
    topic, count, difficulty, subskills = parse_request("slope:12")
    assert (topic, count, difficulty, subskills) == ("slope", 12, None, None)
    spec = spec_from_topics(["slope:12"])
    assert set(_subskills_in(spec)) == set(topic_subskills("slope"))


def test_single_subskill_is_the_only_one_generated():
    spec = spec_from_topics(["slope/slope_from_two_points:10"])
    assert _subskills_in(spec) == ["slope_from_two_points"]
    assert _total(spec) == 10


def test_several_subskills_join_with_plus_and_split_the_count():
    spec = spec_from_topics(["exponents/product_rule+quotient_rule:12"])
    assert set(_subskills_in(spec)) == {"product_rule", "quotient_rule"}
    assert _total(spec) == 12


def test_selector_composes_with_count_and_difficulty():
    topic, count, difficulty, subskills = parse_request(
        "linear_equations/two_step+fractional:14:hard"
    )
    assert (topic, count, difficulty) == ("linear_equations", 14, "hard")
    assert subskills == ["two_step", "fractional"]

    spec = spec_from_topics(["linear_equations/two_step+fractional:14:hard"])
    assert _total(spec) == 14
    assert all(
        p["difficulty"] == "hard"
        for sec in spec["sections"]
        for p in sec["problems"]
    )


def test_selected_subskills_keep_their_catalog_section_grouping():
    """A subskill that owns a group in the catalog still gets that group's
    directions and workspace when selected on its own -- the selector must not
    silently fall back to the topic-level directions."""
    spec = spec_from_topics(["slope/slope_from_two_points:6"])
    section = spec["sections"][0]
    assert "Slope Through Two Points" in section["name"]
    assert section["directions"] == (
        "Find the slope of the line through each pair of points."
    )
    assert section["workspace"] == "1.6cm"


def test_order_follows_the_catalog_not_the_typed_order():
    """Sections merge *consecutive* same-group entries, so honoring an
    arbitrary typed order would split one group into repeated sections."""
    typed = spec_from_topics(["exponents/quotient_rule+product_rule:8"])
    catalog_order = [
        s for s in topic_subskills("exponents")
        if s in {"product_rule", "quotient_rule"}
    ]
    assert _subskills_in(typed) == catalog_order


def test_duplicate_subskills_collapse():
    spec = spec_from_topics(["slope/slope_from_two_points+slope_from_two_points:6"])
    assert _subskills_in(spec) == ["slope_from_two_points"]
    assert _total(spec) == 6


def test_same_topic_twice_with_different_subskills():
    spec = spec_from_topics(
        ["slope/identify_slope_intercept:4", "slope/slope_from_two_points:6"]
    )
    assert set(_subskills_in(spec)) == {
        "identify_slope_intercept", "slope_from_two_points"
    }
    assert _total(spec) == 10
    # The topic name should not be repeated in the generated title.
    assert spec["title"] == "Slope and Linear Graphs"


def test_unknown_subskill_names_the_available_ones():
    with pytest.raises(KeyError) as e:
        parse_request("slope/rise_over_run")
    message = str(e.value)
    assert "rise_over_run" in message
    assert "slope_from_two_points" in message


def test_empty_selector_is_an_error_not_a_silent_full_topic():
    with pytest.raises(ValueError):
        parse_request("slope/")


def test_subskill_of_another_topic_is_rejected():
    """``multi_step`` exists under radical_equations but not under slope."""
    with pytest.raises(KeyError):
        parse_request("slope/multi_step")


def test_every_cataloged_subskill_is_selectable():
    for topic in CATALOG:
        for subskill in topic_subskills(topic):
            _, _, _, parsed = parse_request(f"{topic}/{subskill}")
            assert parsed == [subskill]
