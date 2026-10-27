from pathlib import Path

import pytest

from tn2030.register import load_register
from tn2030.toy import build_toy_network

REGISTER = Path(__file__).parents[1] / "data" / "assumptions_register.xlsx"


@pytest.fixture(scope="session")
def reg():
    """The real assumptions register (toy costs come from technology-data via the register)."""
    return load_register(REGISTER)


@pytest.fixture
def toy_network(reg):
    """Two days at 3-hour steps: small enough to solve in about a second."""
    return build_toy_network(reg, hours=48, step_hours=3)
