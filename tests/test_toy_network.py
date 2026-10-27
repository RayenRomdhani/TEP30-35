import pytest

from tn2030.toy import build_toy_network


def test_toy_solves_optimal(toy_network):
    status, _ = toy_network.optimize(solver_name="highs")
    assert status == "ok"


def test_toy_energy_balance_closes(toy_network):
    toy_network.optimize(solver_name="highs")
    w = toy_network.snapshot_weightings.generators
    # Storage p is positive when discharging, negative when charging.
    supply = (toy_network.generators_t.p.sum(axis=1) + toy_network.storage_units_t.p.sum(axis=1)) * w
    demand = toy_network.loads_t.p_set.sum(axis=1) * w
    assert supply.sum() == pytest.approx(demand.sum(), rel=1e-6)


def test_toy_battery_soc_within_bounds(toy_network):
    toy_network.optimize(solver_name="highs")
    su = toy_network.storage_units.loc["battery"]
    soc = toy_network.storage_units_t.state_of_charge["battery"]
    assert (soc <= su.p_nom_opt * su.max_hours + 1e-6).all()
    assert (soc >= -1e-6).all()


def test_toy_snapshots_start_at_midnight_with_step_weights(toy_network):
    # Later tests rely on day boundaries (e.g. last 3 h step of a day is 21:00).
    assert toy_network.snapshots[0].hour == 0
    assert (toy_network.snapshot_weightings.generators == 3.0).all()
    assert len(toy_network.snapshots) == 16


def test_toy_week_has_a_wind_lull(reg):
    # Real weather has multi-day low-wind periods; without one the toy needs no backup at all.
    n = build_toy_network(reg, hours=168, step_hours=1)
    daily_wind = n.generators_t.p_max_pu["onwind"].groupby(n.snapshots.date).mean()
    assert daily_wind.min() < 0.15
    assert daily_wind.max() > 0.30


def test_all_bus_carriers_are_defined(toy_network):
    assert set(toy_network.buses.carrier) <= set(toy_network.carriers.index)


def test_toy_capital_cost_scaled_to_horizon(reg, toy_network):
    # A 48 h model must carry 48/8760 of the yearly capital cost, or it would overvalue capex.
    from tn2030.toy import annualised_capex

    full_year = annualised_capex(reg["toy_solar_investment"] * 1000, reg["toy_solar_fom"],
                                 reg["toy_solar_lifetime"], reg["discount_rate"])
    assert toy_network.generators.at["solar", "capital_cost"] == pytest.approx(full_year * 48 / 8760)
