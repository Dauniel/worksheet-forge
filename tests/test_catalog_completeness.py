"""Every @register-ed generator must be reachable through the catalog.

A generator that verifies and fuzzes cleanly but never appears in any
CATALOG progression is a silent dead end: `forge topics` won't list it, and
no catalog-driven spec (`forge quick ...`) can ever select it -- only a
hand-written YAML spec naming its (topic, subskill) directly can reach it.
That's exactly the bug class found in commit a349a38, where
linear_equations.fractional/proportion and exponents.combined_rules were
registered but never wired into forge/catalog.py's progressions.

If a generator genuinely should stay catalog-only (reachable only by a
hand-written spec, never by `forge quick`/`forge topics`), add it to
ALLOWED_UNCATALOGED below with a comment explaining why -- don't just let
this test go quiet.
"""

from __future__ import annotations

from forge.catalog import CATALOG
from forge.core.registry import all_generators

# Intentionally empty: there is currently no generator with a legitimate
# reason to be unreachable from the catalog. Add entries here only with a
# comment justifying the exclusion -- an empty list is the healthy state.
ALLOWED_UNCATALOGED: set = set()


def _cataloged_pairs():
    pairs = set()
    for topic, entry in CATALOG.items():
        for e in entry["progression"]:
            pairs.add((topic, e["subskill"]))
    return pairs


def test_every_registered_generator_is_in_the_catalog():
    registered = set(all_generators())
    cataloged = _cataloged_pairs()
    missing = registered - cataloged - ALLOWED_UNCATALOGED
    assert not missing, (
        f"{len(missing)} generator(s) are registered via @register but never "
        f"appear in any forge/catalog.py progression, so `forge topics` won't "
        f"list them and no catalog-driven spec can select them: "
        f"{sorted(missing)}. Add them to a progression, or to "
        f"ALLOWED_UNCATALOGED with a reason if that's intentional."
    )


def test_allowed_uncataloged_list_has_no_stale_entries():
    """If a generator in the exclusion list gets wired in later (or removed),
    the list should be updated -- not left pointing at nothing real."""
    registered = set(all_generators())
    cataloged = _cataloged_pairs()
    stale = ALLOWED_UNCATALOGED & cataloged
    assert not stale, f"already cataloged, drop from ALLOWED_UNCATALOGED: {sorted(stale)}"
    unregistered = ALLOWED_UNCATALOGED - registered
    assert not unregistered, f"not even a registered generator: {sorted(unregistered)}"


def test_every_catalog_entry_has_a_registered_generator():
    """The inverse bug: a catalog entry pointing at a generator that doesn't
    exist would fail loudly at build time, but should fail here first."""
    registered = set(all_generators())
    cataloged = _cataloged_pairs()
    missing = cataloged - registered
    assert not missing, f"catalog references unregistered generator(s): {sorted(missing)}"
