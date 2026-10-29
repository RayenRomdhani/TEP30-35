from pathlib import Path

import pandas as pd
import yaml

import pypsa
import pytest

from tn2030.pipeline import build_step, pathway_step, pathway_summarize_step, solve_step, summarize_step

REGISTER = Path(__file__).parents[1] / "data" / "assumptions_register.xlsx"


def test_pipeline_end_to_end_on_toy(tmp_path, toy_network):
    base = tmp_path / "base.nc"
    toy_network.export_to_netcdf(base)
    committed = tmp_path / "committed.csv"
    pd.DataFrame(columns=["name", "carrier", "p_nom_mw", "bus"]).to_csv(committed, index=False)

    solved, scenarios = [], []
    for name, share in (("S0", 0.0), ("S1-15", 0.15)):
        scen = tmp_path / f"{name}.yaml"
        scen.write_text(yaml.safe_dump({"name": name, "reference": "S0",
                                        "efficiency": {"share": share, "mode": "uniform"},
                                        "flexibility": {"p_max_mw": 0}, "gas_price_factor": 1.0}))
        built, done = tmp_path / f"{name}_built.nc", tmp_path / f"{name}_solved.nc"
        build_step(base, scen, REGISTER, committed, built, calibrate=False)  # the toy has no existing fleet
        solve_step(built, done, REGISTER, committed)
        solved.append(done)
        scenarios.append(scen)
    summarize_step(solved, scenarios, tmp_path / "summary.csv", tmp_path / "avoided.csv")

    summary = pd.read_csv(tmp_path / "summary.csv", index_col=0)
    avoided = pd.read_csv(tmp_path / "avoided.csv", index_col=0)
    assert list(summary.index) == ["S0", "S1-15"]
    assert summary.loc["S1-15", "demand_twh"] < summary.loc["S0", "demand_twh"]
    assert avoided.loc["S1-15", "cost_eur_per_mwh"] > 0
    assert list(avoided.index) == ["S1-15"]  # S0 is its own reference: skipped
    assert (summary["cooling_share"] == 0).all()  # uniform cuts put nothing specifically on cooling
    assert (tmp_path / "S0_solved.nc.warnings.txt").exists()


def test_pathway_end_to_end_on_toy(tmp_path, toy_network):
    """History 2025-2026, then S0 and S1-15 from 2027 to 2030, each year built on the one before."""
    base = tmp_path / "base.nc"
    toy_network.export_to_netcdf(base)
    committed = tmp_path / "committed.csv"
    pd.DataFrame({"name": ["plant due 2028"], "carrier": ["solar"], "p_nom_mw": [50.0], "bus": ["TN"],
                  "cod_expected": [2028]}).to_csv(committed, index=False)
    scen = {}
    for name, share, shift in (("S0", 0.0, 0), ("S1-15", 0.15, 20)):  # S1-15 also shifts load, ramped like the saving
        scen[name] = tmp_path / f"{name}.yaml"
        scen[name].write_text(yaml.safe_dump({"name": name, "reference": "S0",
                                              "efficiency": {"share": share, "mode": "uniform"},
                                              "flexibility": {"p_max_mw": shift}, "gas_price_factor": 1.0}))

    def step(name, year, prev):
        out = tmp_path / f"{name}_{year}.nc"
        pathway_step(base, scen["S0" if name == "history" else name], REGISTER, committed, year, prev, out,
                     calibrate=False)  # the toy has no existing fleet
        return out

    prev = None
    for year in (2025, 2026):
        prev = step("history", year, prev)
    solved = {}
    for name in scen:
        last = prev
        for year in (2027, 2028, 2029, 2030):
            last = solved[(name, year)] = step(name, year, last)
    pathway_summarize_step(solved, scen, 0.35, tmp_path / "summary.csv", tmp_path / "avoided.csv")

    summary = pd.read_csv(tmp_path / "summary.csv").set_index(["scenario", "year"])
    avoided = pd.read_csv(tmp_path / "avoided.csv", dtype={"year": str})
    assert (summary.loc["S0", "cap_solar_mw"].diff().dropna() >= -1e-6).all()  # plants are never taken down
    assert summary.loc[("S1-15", 2030), "demand_twh"] < summary.loc[("S0", 2030), "demand_twh"]
    assert summary.loc[("S0", 2030), "res_gap_to_target"] == pytest.approx(0.35 - summary.loc[("S0", 2030), "res_share"])
    assert list(avoided.year) == ["2027", "2028", "2029", "2030", "2027-2030"]  # S0 is its own reference: skipped
    assert (avoided.cost_eur_per_mwh > 0).all()
    # the plant due in 2028 is on top of everything built up to 2027
    built_2027 = pypsa.Network(str(solved[("S0", 2027)])).generators.at["solar", "p_nom_opt"]
    assert pypsa.Network(str(solved[("S0", 2028)])).generators.at["solar", "p_nom_min"] >= built_2027 + 50 - 1e-6
