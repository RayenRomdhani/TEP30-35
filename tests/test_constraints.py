import pytest

from tn2030.constraints import add_min_res_share, res_share, solve_network
from tn2030.results import summarize


def solve_network_with(n, res_carriers):
    """Test helper: solve with the constraint built from a chosen list of carrier names."""
    return n.optimize(solver_name="highs",
                      extra_functionality=lambda n, s: add_min_res_share(n, 0.35, res_carriers))


def test_res_share_binding_when_gas_is_cheap(toy_network_cheap_gas):
    toy_network_cheap_gas.optimize(solver_name="highs")
    assert res_share(toy_network_cheap_gas) < 0.35  # unconstrained


def test_solve_network_enforces_35pct(toy_network_cheap_gas):
    solve_network(toy_network_cheap_gas, 0.35)
    assert res_share(toy_network_cheap_gas) >= 0.35 - 1e-6


def test_res_constraint_raises_when_no_carrier_matches(toy_network):  # e.g. "wind" instead of "onwind"
    with pytest.raises(ValueError, match="carrier"):
        solve_network_with(toy_network, res_carriers=("wind",))


def test_battery_charger_matches_discharger(pe_battery_network):  # else discharge power is free (review, Phase 4)
    solve_network(pe_battery_network, 0.35)
    links = pe_battery_network.links
    charger = links.at["TN battery charger", "p_nom_opt"]
    discharger = links.at["TN battery discharger", "p_nom_opt"]
    assert charger == pytest.approx(discharger * links.at["TN battery discharger", "efficiency"], abs=1e-3)


def test_summary_reports_store_and_link_battery(pe_battery_network):
    solve_network(pe_battery_network, 0.35)
    s = summarize(pe_battery_network)
    assert s["cap_battery_mw"] == pytest.approx(pe_battery_network.links.at["TN battery discharger", "p_nom_opt"])
    assert s["cap_battery_mwh"] == pytest.approx(pe_battery_network.stores.at["TN battery", "e_nom_opt"])


def test_reserve_margin_forces_firm_capacity(toy_network):
    peak = toy_network.loads_t.p_set.sum(axis=1).max()
    solve_network(toy_network, 0.0, reserve_margin=0.10)
    assert toy_network.generators.at["CCGT", "p_nom_opt"] >= 1.10 * peak - 1e-3  # gas is the only firm option


def test_res_share_ignores_battery_discharge(toy_network):  # spec D12: storage excluded from both sides
    solve_network(toy_network, 0.35)
    w = toy_network.snapshot_weightings.generators
    gen = toy_network.generators_t.p.mul(w, axis=0).sum()
    carrier = toy_network.generators.carrier
    expected = gen[carrier.isin(["solar", "onwind"])].sum() / gen.sum()
    assert res_share(toy_network) == pytest.approx(expected)
