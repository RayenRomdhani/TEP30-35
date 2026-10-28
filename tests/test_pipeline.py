from pathlib import Path

import pandas as pd
import yaml

from tn2030.pipeline import build_step, solve_step, summarize_step

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
    assert (tmp_path / "S0_solved.nc.warnings.txt").exists()
