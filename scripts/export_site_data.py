"""Write the website's data files (site/data/*.json) from the results, the register and the solved networks.

Run from the repo root after the pipeline:  python scripts/export_site_data.py
The site never types a number itself: every figure it shows comes from these files.
"""

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))  # this checkout's tn2030
import pandas as pd
import pypsa

from tn2030.constraints import res_share
from tn2030.plotting import STACK_ORDER, dispatch_by_carrier
from tn2030.register import load_register
from tn2030.results import summarize
from tn2030.site_data import grid_lines, hour_grid

OUT = ROOT / "site" / "data"
RESULTS = ROOT / "results"
OSM_LINES = Path(r"D:\pypsa-earth\resources\TN\osm\clean\all_clean_lines.geojson")  # OpenStreetMap, ODbL
ORDER = ["S0", "S1-10", "S1-15", "S1-20", "S1-15C", "S2-300", "S2-600",
         "G-lo-S0", "G-lo-S1-15", "G-hi-S0", "G-hi-S1-15"]
NAMES = {"S0": "Base case", "S1-10": "Save 10%", "S1-15": "Save 15%", "S1-20": "Save 20%",
         "S1-15C": "Save 15%, cooling first", "S2-300": "Save 15% + 300 MW shift",
         "S2-600": "Save 15% + 600 MW shift", "G-lo-S0": "Cheap gas", "G-lo-S1-15": "Cheap gas, save 15%",
         "G-hi-S0": "Expensive gas", "G-hi-S1-15": "Expensive gas, save 15%"}
CONTEXT_IDS = ["re_target_2030", "tsp_re_target_2030", "indc_co2_intensity_cut_2030", "demand_2024_twh",
               "imports_2024_twh", "demand_growth", "gas_share_2024", "peak_2024_mw", "peak_ref_2030_mw",
               "cap_2024_ccgt_mw", "cap_2024_ocgt_mw", "cap_2024_steam_mw", "cap_2024_total_mw",
               "gen_2024_total_twh", "gas_supply_domestic_2023_ktep", "gas_supply_domestic_2024_ktep",
               "gas_supply_royalty_2024_ktep", "gas_supply_purchases_2024_ktep", "gas_for_power_2024_ktep_ncv",
               "energy_independence_2024", "steg_established_year", "steg_generation_share",
               "gas_price_eur_per_mwh_th", "reserve_margin", "flex_cap_mw", "flex_cap_hi_mw", "flex_max_hours",
               "gas_price_factor_lo", "gas_price_factor_hi"]


def clean(obj):
    """Empty cells (NaN) become null: browsers reject NaN in JSON."""
    if isinstance(obj, dict):
        return {k: clean(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean(v) for v in obj]
    return None if isinstance(obj, float) and obj != obj else obj


def write(name: str, data) -> None:
    path = OUT / name
    path.write_text(json.dumps(clean(data), separators=(",", ":"), allow_nan=False), encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)} ({path.stat().st_size / 1e3:.0f} kB)")


def study(reg: dict) -> dict:
    """Scenario results, avoided-per-MWh, the 2024 check and the context facts, with their register sources."""
    summary = pd.read_csv(RESULTS / "summary.csv", index_col="scenario").loc[ORDER]
    avoided = pd.read_csv(RESULTS / "avoided.csv", index_col="scenario")
    validation = pd.read_csv(RESULTS / "validation.csv").query("case == 'calibrated'")
    register = pd.read_excel(ROOT / "data" / "assumptions_register.xlsx", sheet_name="register").set_index("id")
    scenarios = [{"code": s, "name": NAMES[s], **summary.loc[s].round(4).to_dict(),
                  **({"avoided": avoided.loc[s].to_dict()} if s in avoided.index else {})} for s in ORDER]
    context = {i: {"value": reg[i], "unit": register.at[i, "unit"], "source": register.at[i, "source_title"],
                   "url": register.at[i, "source_url"] if pd.notna(register.at[i, "source_url"]) else None}
               for i in CONTEXT_IDS}
    return {"scenarios": scenarios, "context": context, "merit": merit(reg),
            "validation": validation.drop(columns="case").to_dict(orient="records")}


def merit(reg: dict) -> list[dict]:
    """Running cost (fuel / efficiency + variable upkeep) and CO2 per MWh of electricity for each gas plant type.
    Existing plants use the technology-data efficiency times the factor fitted to 2024 fuel use (Phase 3)."""
    gas, co2, f = reg["gas_price_eur_per_mwh_th"], reg["gas_co2_intensity"], reg["existing_gas_efficiency_factor"]
    rows = [("Combined cycle, new", reg["ccgt_efficiency"], reg["ccgt_vom"]),
            ("Combined cycle, existing", reg["ccgt_efficiency"] * f, reg["ccgt_vom"]),
            ("Gas turbine, new", reg["ocgt_efficiency"], reg["ocgt_vom"]),
            ("Gas turbine / steam, existing", reg["ocgt_efficiency"] * f, reg["ocgt_vom"])]
    return [{"name": name, "efficiency": round(eff, 3), "run_cost": round(gas / eff + vom, 1),
             "co2": round(co2 / eff, 3)} for name, eff, vom in rows]


def load_after_shift(n: pypsa.Network) -> pd.Series:
    """Hourly domestic load (MW) after any demand shifting (shift dispatch = load moved away)."""
    load = n.get_switchable_as_dense("Load", "p_set").sum(axis=1)
    shift = n.storage_units.index[n.storage_units.carrier == "demand_shift"]
    return load - n.storage_units_t.p[shift].sum(axis=1) if len(shift) else load


def hourly(networks: dict) -> dict:
    """365 x 24 grids of gas, solar and wind output and load, for the 3D landscape."""
    out = {}
    for s, n in networks.items():
        d = dispatch_by_carrier(n)
        gas = d.get("CCGT", 0) + d.get("OCGT", 0)
        out[s] = {"gas": hour_grid(gas), "solar": hour_grid(d["solar"]), "wind": hour_grid(d["onwind"]),
                  "load": hour_grid(load_after_shift(n))}
    return out


def peak_week(networks: dict) -> dict:
    """The week around the S0 peak hour: hourly output by technology and load, S0 and S2-300."""
    s0 = networks["S0"]
    peak = s0.get_switchable_as_dense("Load", "p_set").sum(axis=1).idxmax()
    window = slice(peak - pd.Timedelta(hours=84), peak + pd.Timedelta(hours=83))
    out = {"start": str(window.start), "peak": str(peak), "order": STACK_ORDER}
    for s in ("S0", "S2-300"):
        n = networks[s]
        d = dispatch_by_carrier(n).loc[window].round()
        out[s] = {"dispatch": {c: d[c].astype(int).tolist() for c in d.columns if d[c].max() > 1},
                  "load_planned": n.get_switchable_as_dense("Load", "p_set").sum(axis=1).loc[window].round()
                  .astype(int).tolist(),
                  "load_served": load_after_shift(n).loc[window].round().astype(int).tolist()}
    return out


def grid(s0: pypsa.Network) -> dict:
    """OpenStreetMap transmission lines of Tunisia and the model's two nodes."""
    ac = s0.buses[s0.buses.carrier == "AC"]
    return {"lines": grid_lines(json.loads(OSM_LINES.read_text(encoding="utf-8")), "TN"),
            "nodes": [{"name": b, "lon": round(r.x, 3), "lat": round(r.y, 3)} for b, r in ac.iterrows()],
            "attribution": "Grid: © OpenStreetMap contributors (ODbL), via PyPSA-Earth"}


PATHWAY_KEYS = ["res_share", "demand_twh", "gas_use_twh_th", "co2_mt", "system_cost_meur", "new_cap_total_mw"] + \
    [f"cap_{c}_mw" for c in STACK_ORDER] + ["cap_ror_mw"]
LIMIT_IDS = ["pathway_solar_extra_mw_per_year", "pathway_wind_first_year", "pathway_wind_extra_mw_per_year",
             "pathway_battery_first_year", "pathway_battery_mw", "pathway_battery_mwh", "solar_capacity_2024_mw"]


def pathway(reg: dict) -> dict:
    """The 2027-2030 pathway: 2025-2026 history, each scenario year by year, what a saved MWh avoids each year,
    and the build limits with their sources."""
    summary = pd.read_csv(RESULTS / "pathway_summary.csv")
    avoided = pd.read_csv(RESULTS / "pathway_avoided.csv")
    history = []
    for year in (2025, 2026):
        n = pypsa.Network(str(RESULTS / "pathway" / f"history_{year}_solved.nc"))
        history.append({"year": year, "res_share": res_share(n), **summarize(n).to_dict()})
    keep = lambda row: {k: round(float(row.get(k, 0.0) or 0.0), 4) for k in PATHWAY_KEYS} | {"year": int(row["year"])}
    register = pd.read_excel(ROOT / "data" / "assumptions_register.xlsx", sheet_name="register").set_index("id")
    committed = pd.read_csv(ROOT / "data" / "committed_projects.csv")
    committed["cod_expected"] = pd.to_numeric(committed.cod_expected, errors="coerce")
    by_year = committed[committed.carrier.isin(["solar", "onwind"])].groupby("cod_expected").p_nom_mw.sum()
    return {"target": reg["re_target_2030"],
            "committed": {int(y): float(mw) for y, mw in by_year.items()},
            "history": [keep(h) for h in history],
            "scenarios": {s: [keep(r) for _, r in summary[summary.scenario == s].sort_values("year").iterrows()]
                          for s in ORDER},
            "avoided": {s: d.drop(columns=["scenario", "reference"]).to_dict(orient="records")
                        for s, d in avoided.groupby("scenario")},
            "limits": {i: {"value": reg[i], "note": register.at[i, "notes"],
                           "url": register.at[i, "source_url"] if pd.notna(register.at[i, "source_url"]) else None}
                       for i in LIMIT_IDS}}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    reg = load_register(ROOT / "data" / "assumptions_register.xlsx")
    write("study.json", study(reg))
    if (RESULTS / "pathway_summary.csv").exists():
        write("pathway.json", pathway(reg))
    networks = {s: pypsa.Network(str(RESULTS / "networks" / f"{s}_solved.nc")) for s in ("S0", "S1-15", "S2-300")}
    write("hourly.json", hourly(networks))
    write("peakweek.json", peak_week(networks))
    write("grid.json", grid(networks["S0"]))
    (ROOT / "site" / "assets").mkdir(exist_ok=True)  # social-preview image
    shutil.copyfile(RESULTS / "figures" / "0_headline.png", ROOT / "site" / "assets" / "headline.png")


if __name__ == "__main__":
    main()
