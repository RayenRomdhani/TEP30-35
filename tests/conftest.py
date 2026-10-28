from pathlib import Path

import pandas as pd
import pypsa
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


@pytest.fixture
def toy_network_partial_day(reg):
    """52 hours at 3-hour steps: the last calendar day has only one snapshot (review focus 5)."""
    return build_toy_network(reg, hours=52, step_hours=3)


@pytest.fixture
def two_bus_network():
    """Two buses whose loads are in the ratio 3:1 over the day."""
    n = pypsa.Network()
    n.set_snapshots(pd.date_range("2030-07-01", periods=24, freq="h"))
    for bus, mw in (("north", 300.0), ("south", 100.0)):
        n.add("Bus", bus, carrier="AC")
        n.add("Load", f"{bus} load", bus=bus, p_set=mw)
    return n
