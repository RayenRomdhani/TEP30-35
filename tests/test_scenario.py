from pathlib import Path

import pandas as pd
import pypsa
import pytest
import yaml

from tn2030.demand import annual_demand_2030
from tn2030.scenario import apply_committed, build_scenario, calibrate_base, load_scenario, scale_gas_cost

ROOT = Path(__file__).parents[1]
NO_COMMITTED = pd.DataFrame(columns=["carrier", "bus", "p_nom_mw"])
S1_15 = {"name": "S1-15", "reference": "S0", "efficiency": {"share": 0.15, "mode": "uniform"},
         "flexibility": {"p_max_mw": 0}, "gas_price_factor": 1.0}


def weighted_load_twh(n):
    w = n.snapshot_weightings.generators
    return n.loads_t.p_set.mul(w, axis=0).sum().sum() / 1e6


def mc(n, carrier):
    return n.generators.marginal_cost[n.generators.carrier == carrier].iloc[0]


def test_build_scenario_hits_2030_demand_minus_saving_minus_imports(toy_network, reg):
    out = build_scenario(toy_network, S1_15, reg, NO_COMMITTED, calibrate=False)
    expected = annual_demand_2030(reg["demand_2024_twh"], reg["demand_growth"]) * 0.85 - reg["imports_2024_twh"]
    assert weighted_load_twh(out) == pytest.approx(expected)


def test_build_scenario_does_not_modify_base(toy_network, reg):
    before = toy_network.loads_t.p_set.copy()
    build_scenario(toy_network, S1_15, reg, NO_COMMITTED, calibrate=False)
    pd.testing.assert_frame_equal(toy_network.loads_t.p_set, before)


def test_build_scenario_adds_shift_from_register_id(toy_network, reg):
    scen = {**S1_15, "flexibility": {"p_max_mw": "flex_cap_mw"}}
    out = build_scenario(toy_network, scen, reg, NO_COMMITTED, calibrate=False)
    assert out.storage_units.p_nom[out.storage_units.carrier == "demand_shift"].sum() == pytest.approx(reg["flex_cap_mw"])


def test_scale_gas_cost_adds_fuel_part_only(toy_network):
    before = mc(toy_network, "CCGT")
    scale_gas_cost(toy_network, 1.5, 30.0)
    eff = toy_network.generators.efficiency[toy_network.generators.carrier == "CCGT"].iloc[0]
    assert mc(toy_network, "CCGT") - before == pytest.approx(0.5 * 30.0 / eff)


def test_apply_committed_raises_p_nom_min(toy_network):
    apply_committed(toy_network, pd.DataFrame({"carrier": ["solar"], "bus": ["TN"], "p_nom_mw": [250.0]}))
    g = toy_network.generators.loc["solar"]
    assert g.p_nom_min == pytest.approx(250.0) and g.p_nom >= 250.0


def test_apply_committed_unknown_carrier_raises(toy_network):
    with pytest.raises(ValueError, match="no extendable"):
        apply_committed(toy_network, pd.DataFrame({"carrier": ["nuclear"], "bus": ["TN"], "p_nom_mw": [1.0]}))


def test_load_scenario_rejects_bad_mode(tmp_path):
    bad = {**S1_15, "efficiency": {"share": 0.15, "mode": "magic"}}
    path = tmp_path / "bad.yaml"
    path.write_text(yaml.safe_dump(bad))
    with pytest.raises(ValueError, match="efficiency.mode"):
        load_scenario(path)


def test_all_scenario_files_load():
    assert len([load_scenario(p) for p in (ROOT / "config" / "scenarios").glob("*.yaml")]) == 11


BASE = Path(yaml.safe_load((ROOT / "config" / "pipeline.yaml").read_text())["base_network"])


@pytest.mark.skipif(not BASE.exists(), reason="needs the PyPSA-Earth base network on D:")
def test_calibrate_base_on_real_network(reg):  # integration: the Phase 3 calibrations on the real base network
    n = calibrate_base(pypsa.Network(str(BASE)), reg)
    g = n.generators
    assert "oil" not in g.carrier.values
    assert g.p_nom[g.index.str.endswith("existing")].sum() == pytest.approx(
        reg["cap_2024_ccgt_mw"] + reg["cap_2024_ocgt_mw"] + reg["cap_2024_steam_mw"])
    assert (g.carrier[g.index.str.endswith("OCGT new")] == "OCGT").sum() == 2  # one new-build OCGT per bus
    solar = g[(g.carrier == "solar") & g.p_nom_extendable]
    assert (solar.p_nom_min == solar.p_nom).all()  # existing 2024 solar is kept
