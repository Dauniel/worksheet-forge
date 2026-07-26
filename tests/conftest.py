import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from forge.core.registry import all_generators  # noqa: E402


@pytest.fixture(scope="session")
def generators():
    return all_generators()


@pytest.fixture(scope="session")
def spec_path():
    return ROOT / "specs" / "placement_algebra1.yaml"


@pytest.fixture(scope="session")
def root():
    return ROOT
