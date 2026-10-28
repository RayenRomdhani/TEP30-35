import pytest

from tn2030.flexibility import add_shiftable_load


def test_shift_split_by_bus_load_share(two_bus_network):  # loads 3:1
    add_shiftable_load(two_bus_network, 300.0, 3.0)
    assert two_bus_network.storage_units.p_nom.tolist() == pytest.approx([225.0, 75.0])


def test_shift_is_free_lossless_and_fixed(two_bus_network):
    add_shiftable_load(two_bus_network, 300.0, 3.0)
    s = two_bus_network.storage_units
    assert (s.carrier == "demand_shift").all() and (s.max_hours == 3.0).all()
    assert (s.efficiency_store == 1).all() and (s.efficiency_dispatch == 1).all()
    assert (s.capital_cost == 0).all() and (s.marginal_cost == 0).all() and not s.p_nom_extendable.any()


def test_shift_soc_zero_at_each_day_end(toy_network):
    add_shiftable_load(toy_network, 300.0, 3.0)
    toy_network.optimize(solver_name="highs")
    soc = toy_network.storage_units_t.state_of_charge["demand_shift TN"]
    assert soc[soc.index.hour == 21].abs().max() < 1e-6  # last 3 h step of each day


def test_shift_soc_reset_on_partial_last_day(toy_network_partial_day):  # 52 h horizon
    add_shiftable_load(toy_network_partial_day, 300.0, 3.0)
    s = toy_network_partial_day.storage_units_t.state_of_charge_set["demand_shift TN"]
    assert s.iloc[-1] == 0.0


def test_shift_is_energy_neutral(toy_network):
    add_shiftable_load(toy_network, 300.0, 3.0)
    toy_network.optimize(solver_name="highs")
    p = toy_network.storage_units_t.p["demand_shift TN"]
    w = toy_network.snapshot_weightings.stores
    assert (p * w).sum() == pytest.approx(0.0, abs=1e-6)


def test_shift_is_used_when_it_saves_money(toy_network):  # sanity: a free shift should not make things worse
    toy_network.optimize(solver_name="highs")
    without = toy_network.objective
    add_shiftable_load(toy_network, 300.0, 3.0)
    toy_network.optimize(solver_name="highs")
    assert toy_network.objective <= without + 1e-6
