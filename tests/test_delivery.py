"""Filing rules for delivered worksheets.

CLAUDE.md has described the filing convention in prose since the start, and it
drifted anyway: sheets landed with no spec (so no rebuild), with no key, and
once outside the repo entirely. These tests give the paragraph teeth.
"""

from __future__ import annotations

import yaml
import pytest

from forge.cli import WORKSHEETS, main

# Filed before `forge deliver` existed, and not reconstructible now. Where a
# spec survives, its seed does not -- so rebuilding would produce a key full of
# different problems than the PDF the student actually got, which is worse than
# no key at all. Grandfathered deliberately; do not add to this list. A new
# delivery that needs an exemption is a delivery that went out wrong.
LEGACY_INCOMPLETE = {
    ("Jean_English", "2026-07-30_Jean"),
    ("Jimmy_Math", "2026-07-30_Jimmy"),
    ("Jimmy_Math", "2026-07-31_Jimmy"),
    ("Mabel", "2026-07-30_Mabel"),
    ("Rachel_Math", "2026-07-30_Rachel"),
}


def _delivered_sets():
    """Every (folder, stem) that has a PDF filed under tutor/worksheets/."""
    for folder in sorted(p for p in WORKSHEETS.iterdir() if p.is_dir()):
        for pdf in sorted(folder.glob("*.pdf")):
            yield folder, pdf.stem


def test_every_delivered_sheet_has_spec_and_key():
    missing = []
    for folder, stem in _delivered_sets():
        if (folder.name, stem) in LEGACY_INCOMPLETE:
            continue
        for suffix in ("_spec.yaml", "_key.tex"):
            if not (folder / f"{stem}{suffix}").exists():
                missing.append(f"{folder.name}/{stem}{suffix}")
    assert not missing, "delivered worksheets missing artifacts:\n  " + "\n  ".join(missing)


def test_delivered_specs_record_their_seed():
    """Without the seed the sheet cannot be reproduced from the folder alone."""
    unseeded = []
    for folder, stem in _delivered_sets():
        spec_path = folder / f"{stem}_spec.yaml"
        if not spec_path.exists():
            continue  # covered by the test above
        spec = yaml.safe_load(spec_path.read_text())
        if "seed" not in spec:
            unseeded.append(f"{folder.name}/{spec_path.name}")
    if unseeded:
        pytest.xfail("specs filed before `forge deliver` recorded no seed: "
                     + ", ".join(unseeded))


def test_no_stray_files_at_the_worksheets_root():
    """Worksheets live in a student folder, never loose at the root."""
    stray = [p.name for p in WORKSHEETS.iterdir() if p.is_file()]
    assert not stray, f"files loose in tutor/worksheets/: {stray}"


def test_deliver_files_the_trio_and_records_the_seed(tmp_path, monkeypatch):
    spec = {
        "title": "Delivery Test",
        "sections": [
            {"name": "Part A: Negatives",
             "directions": "Evaluate each expression.",
             "problems": [{"topic": "negatives", "subskill": "add_sub_integers",
                           "count": 2, "difficulty": "easy"}]}
        ],
    }
    spec_path = tmp_path / "delivery_test.yaml"
    spec_path.write_text(yaml.safe_dump(spec, sort_keys=False))

    dest_root = tmp_path / "worksheets"
    monkeypatch.setattr("forge.cli.WORKSHEETS", dest_root)

    rc = main(["deliver", str(spec_path), "--student", "Testy_Math",
               "--date", "2026-08-06", "--seed", "5",
               "--out", str(tmp_path / "stage")])
    assert rc == 0

    dest = dest_root / "Testy_Math"
    assert (dest / "2026-08-06_Testy_key.tex").exists()
    filed = yaml.safe_load((dest / "2026-08-06_Testy_spec.yaml").read_text())
    assert filed["seed"] == 5, "delivered spec must record the seed"


def test_deliver_refuses_to_clobber_an_existing_sheet(tmp_path, monkeypatch):
    spec = {
        "title": "Clobber Test",
        "sections": [
            {"name": "Part A: Negatives",
             "directions": "Evaluate each expression.",
             "problems": [{"topic": "negatives", "subskill": "add_sub_integers",
                           "count": 2, "difficulty": "easy"}]}
        ],
    }
    spec_path = tmp_path / "clobber.yaml"
    spec_path.write_text(yaml.safe_dump(spec, sort_keys=False))

    dest_root = tmp_path / "worksheets"
    monkeypatch.setattr("forge.cli.WORKSHEETS", dest_root)
    dest = dest_root / "Testy_Math"
    dest.mkdir(parents=True)
    (dest / "2026-08-06_Testy.pdf").write_bytes(b"already delivered")

    rc = main(["deliver", str(spec_path), "--student", "Testy_Math",
               "--date", "2026-08-06", "--seed", "5",
               "--out", str(tmp_path / "stage")])
    assert rc == 1
    assert (dest / "2026-08-06_Testy.pdf").read_bytes() == b"already delivered"


def test_quick_can_deliver_directly(tmp_path, monkeypatch):
    """`quick --deliver-to` files the same trio as `deliver`, no --save hop."""
    dest_root = tmp_path / "worksheets"
    monkeypatch.setattr("forge.cli.WORKSHEETS", dest_root)

    rc = main(["quick", "negatives/add_sub_integers:3", "--deliver-to", "Testy_Math",
               "--date", "2026-08-07", "--seed", "11",
               "--out", str(tmp_path / "stage")])
    assert rc == 0

    dest = dest_root / "Testy_Math"
    for suffix in (".pdf", "_key.tex", "_spec.yaml"):
        assert (dest / f"2026-08-07_Testy{suffix}").exists(), suffix
    filed = yaml.safe_load((dest / "2026-08-07_Testy_spec.yaml").read_text())
    assert filed["seed"] == 11


def test_quick_deliver_refuses_before_building(tmp_path, monkeypatch):
    """A taken slot costs no compile: nothing is staged before the refusal."""
    dest_root = tmp_path / "worksheets"
    monkeypatch.setattr("forge.cli.WORKSHEETS", dest_root)
    dest = dest_root / "Testy_Math"
    dest.mkdir(parents=True)
    (dest / "2026-08-07_Testy.pdf").write_bytes(b"already delivered")

    stage = tmp_path / "stage"
    rc = main(["quick", "negatives/add_sub_integers:3", "--deliver-to", "Testy_Math",
               "--date", "2026-08-07", "--seed", "11", "--out", str(stage)])
    assert rc == 1
    assert (dest / "2026-08-07_Testy.pdf").read_bytes() == b"already delivered"
    assert not stage.exists(), "refused early, so nothing should have been staged"
