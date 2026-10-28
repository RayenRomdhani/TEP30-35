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
def solved_toy(toy_network):
    """The toy network solved with the 35% renewable target."""
    from tn2030.constraints import solve_network
    solve_network(toy_network, 0.35)
    return toy_network


@pytest.fixture
def toy_network_cheap_gas(toy_network):
    """Toy network where wind and solar cost 5x more, so without a target the optimizer picks mostly gas."""
    re = toy_network.generators.carrier.isin(["solar", "onwind"])
    toy_network.generators.loc[re, "capital_cost"] *= 5
    return toy_network


@pytest.fixture
def two_bus_network():
    """Two buses whose loads are in the ratio 3:1 over the day."""
    n = pypsa.Network()
    n.set_snapshots(pd.date_range("2030-07-01", periods=24, freq="h"))
    for bus, mw in (("north", 300.0), ("south", 100.0)):
        n.add("Bus", bus, carrier="AC")
        n.add("Load", f"{bus} load", bus=bus, p_set=mw)
    return n
