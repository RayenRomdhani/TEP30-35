import pandas as pd
import pypsa
import pytest

from tn2030.constraints import solve_network
from tn2030.flexibility import add_shiftable_load


def _half(n):
    """Energy each shift unit can move = p_nom x shift hours = half of its storage room."""
    s = n.storage_units
    return s.p_nom * s.max_hours / 2


@pytest.fixture
def late_cheap_day():
    """One day at 1 h steps; power is cheap only in the last 2 hours, so postponing load pays."""
    n = pypsa.Network()
    n.set_snapshots(pd.date_range("2030-07-01", periods=24, freq="h"))
    for c in ("AC", "solar", "gas"):
        n.add("Carrier", c)
    n.add("Bus", "TN", carrier="AC")
    n.add("Load", "TN load", bus="TN", p_set=100.0)
    cheap = pd.Series(0.0, index=n.snapshots)
    cheap.iloc[-2:] = 1.0
    n.add("Generator", "cheap", bus="TN", carrier="solar", p_nom=1000.0, p_max_pu=cheap, marginal_cost=0.0)
    n.add("Generator", "gas", bus="TN", carrier="gas", p_nom=1000.0, marginal_cost=100.0)
    return n


def test_shift_split_by_bus_load_share(two_bus_network):  # loads 3:1
    add_shiftable_load(two_bus_network, 300.0, 3.0)
    assert two_bus_network.storage_units.p_nom.tolist() == pytest.approx([225.0, 75.0])


def test_shift_is_free_lossless_and_fixed(two_bus_network):  # room for 3 h earlier and 3 h later
    add_shiftable_load(two_bus_network, 300.0, 3.0)
    s = two_bus_network.storage_units
    assert (s.carrier == "demand_shift").all() and (s.max_hours == 6.0).all()
    assert (s.efficiency_store == 1).all() and (s.efficiency_dispatch == 1).all()
    assert (s.capital_cost == 0).all() and (s.marginal_cost == 0).all() and not s.p_nom_extendable.any()


def test_shift_back_to_neutral_at_each_day_end(toy_network):  # neutral = half full
    add_shiftable_load(toy_network, 300.0, 3.0)
    solve_network(toy_network, 0.0)
    soc = toy_network.storage_units_t.state_of_charge["demand_shift TN"]
    neutral = _half(toy_network)["demand_shift TN"]
    assert (soc[soc.index.hour == 21] - neutral).abs().max() < 1e-6  # last 3 h step of each day


def test_shift_neutral_on_partial_last_day(toy_network_partial_day):  # 52 h horizon
    add_shiftable_load(toy_network_partial_day, 300.0, 3.0)
    s = toy_network_partial_day.storage_units_t.state_of_charge_set["demand_shift TN"]
    assert s.iloc[-1] == pytest.approx(_half(toy_network_partial_day)["demand_shift TN"])


def test_shift_is_energy_neutral(toy_network):
    add_shiftable_load(toy_network, 300.0, 3.0)
    solve_network(toy_network, 0.0)
    p = toy_network.storage_units_t.p["demand_shift TN"]
    w = toy_network.snapshot_weightings.stores
    assert (p * w).sum() == pytest.approx(0.0, abs=1e-6)


def test_shift_can_postpone_load(late_cheap_day):  # two-way: load can move later, not only earlier
    add_shiftable_load(late_cheap_day, 50.0, 3.0)
    solve_network(late_cheap_day, 0.0)
    soc = late_cheap_day.storage_units_t.state_of_charge["demand_shift TN"]
    assert soc.min() < _half(late_cheap_day)["demand_shift TN"] - 1.0


def test_shift_moves_load_at_most_3_hours(late_cheap_day):
    """Energy owed at any hour must have been moved within the last 3 hours, in both directions."""
    add_shiftable_load(late_cheap_day, 50.0, 3.0)
    solve_network(late_cheap_day, 0.0)
    t = late_cheap_day.storage_units_t
    soc, store, dispatch = (t[a]["demand_shift TN"] for a in ("state_of_charge", "p_store", "p_dispatch"))
    neutral = _half(late_cheap_day)["demand_shift TN"]
    recent_store = store.rolling(3, min_periods=1).sum()
    recent_dispatch = dispatch.rolling(3, min_periods=1).sum()
    assert ((soc - neutral) <= recent_store + 1e-6).all()
    assert ((neutral - soc) <= recent_dispatch + 1e-6).all()
    assert ((store + dispatch) <= 50.0 + 1e-6).all()  # no charging and discharging at once beyond the 50 MW


def test_shift_moves_load_into_cheap_hours(late_cheap_day):
    """The 2 cheap hours take 50 MW extra each, so gas falls by exactly 100 MWh; daily energy is unchanged.

    (Moving load between two equally expensive hours costs nothing, so the solver may do it; it has no effect.)
    """
    add_shiftable_load(late_cheap_day, 50.0, 3.0)
    solve_network(late_cheap_day, 0.0)
    p = late_cheap_day.storage_units_t.p["demand_shift TN"]  # + = load reduced, - = load increased
    assert -p.iloc[-2:].sum() == pytest.approx(100.0)
    assert late_cheap_day.generators_t.p["gas"].sum() == pytest.approx(22 * 100.0 - 100.0)
