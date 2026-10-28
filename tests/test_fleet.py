import pandas as pd
import pypsa
import pytest

from tn2030.fleet import rebuild_thermal_fleet


@pytest.fixture
def pe_like():
    """Two buses shaped like PyPSA-Earth's output: merged existing+new CCGT, fixed oil, solar."""
    n = pypsa.Network()
    n.set_snapshots(pd.date_range("2030-01-01", periods=2, freq="h"))
    for b in ("north", "south"):
        n.add("Bus", b)
    n.add("Generator", "north CCGT", bus="north", carrier="CCGT", p_nom=300, p_nom_min=300, p_nom_extendable=True,
          efficiency=0.58, capital_cost=100.0, marginal_cost=50.0)
    n.add("Generator", "south CCGT", bus="south", carrier="CCGT", p_nom=100, p_nom_min=100, p_nom_extendable=True,
          efficiency=0.58, capital_cost=100.0, marginal_cost=50.0)
    n.add("Generator", "north oil", bus="north", carrier="oil", p_nom=100, efficiency=0.35, marginal_cost=130.0)
    n.add("Generator", "north solar", bus="north", carrier="solar", p_nom=50)
    return n


def _rebuild(n, factor=1.0):
    return rebuild_thermal_fleet(n, ccgt_mw=1000, ocgt_mw=500, ccgt_eff=0.58, ocgt_eff=0.41, fuel_cost=30.0,
                                 ccgt_vom=5.0, ocgt_vom=6.0, efficiency_factor=factor)


def test_existing_totals_match_inputs_and_oil_is_dropped(pe_like):
    n = _rebuild(pe_like)
    existing = n.generators[~n.generators.p_nom_extendable]
    assert existing.groupby("carrier").p_nom.sum()[["CCGT", "OCGT"]].tolist() == pytest.approx([1000, 500])
    assert "oil" not in n.generators.carrier.values
    assert "north solar" in n.generators.index  # renewables untouched


def test_split_follows_existing_thermal_share_per_bus(pe_like):  # north had 300 + 100 of 500 MW thermal = 80%
    n = _rebuild(pe_like)
    g = n.generators
    assert g.at["north CCGT existing", "p_nom"] == pytest.approx(800)
    assert g.at["south OCGT existing", "p_nom"] == pytest.approx(100)


def test_existing_units_are_fixed_and_sunk(pe_like):  # sunk cost: no capital cost on existing plant
    n = _rebuild(pe_like)
    existing = n.generators[n.generators.index.str.endswith("existing")]
    assert not existing.p_nom_extendable.any()
    assert (existing.capital_cost == 0).all()


def test_new_build_candidate_starts_from_zero(pe_like):  # the old merged generator becomes the new-build option
    n = _rebuild(pe_like)
    g = n.generators.loc["north CCGT"]
    assert g.p_nom_extendable and g.p_nom == 0 and g.p_nom_min == 0
    assert g.efficiency == pytest.approx(0.58)


def test_efficiency_factor_scales_existing_units_and_their_fuel_cost(pe_like):
    n = _rebuild(pe_like, factor=0.8)
    g = n.generators.loc["north OCGT existing"]
    assert g.efficiency == pytest.approx(0.41 * 0.8)
    assert g.marginal_cost == pytest.approx(30.0 / (0.41 * 0.8) + 6.0)
