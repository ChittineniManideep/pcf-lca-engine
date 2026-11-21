import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pcf.config import load_study  # noqa: E402


@pytest.fixture(scope="session")
def study():
    return load_study()


@pytest.fixture
def fresh_study(study):
    return study.copy()
