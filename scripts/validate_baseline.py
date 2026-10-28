"""Phase 3 baseline check: compare the base network with official 2024 figures, then calibrate (plan Task 10).

Two cases, each a dispatch-only year (capacities frozen, load = 2024 total demand minus flat imports):
- "pypsa_earth": the network as PyPSA-Earth built it.
- "calibrated":  thermal fleet rebuilt from ONEM 2024 types (tn2030.fleet), demand shape stretched to the official
                 load factor and minimum/peak ratio (tn2030.demand.reshape_profile), and one efficiency factor for
                 existing gas units fitted so fleet efficiency matches STEG's measured fuel use.
Writes results/validation.csv (case, metric, model, reference, diff_pct, source).

Run:  python scripts/validate_baseline.py
"""

from pathlib import Path

import pandas as pd
import pypsa
import yaml

from tn2030.demand import reshape_profile, scale_profile, subtract_imports
from tn2030.fleet import rebuild_thermal_fleet
from tn2030.register import load_register

ROOT = Path(__file__).resolve().parents[1]
ONEM = "ONEM Memento 2024"
MWH_PER_TOE = 11.63  # 1 toe = 41.868 GJ = 11.63 MWh (IEA unit definition)
HOURS_2024 = 8784  # 2024 was a leap year
VOLL = 100_000  # EUR/MWh for unserved load, PyPSA-Earth's default load_shedding (configs/solving.default.yaml)
GAS = ["CCGT", "OCGT"]
RENEWABLE = ["onwind", "solar", "ror"]


def row(case, metric, model, reference, source):
    diff = 100 * (model - reference) / reference if reference else float("nan")
    return {"case": case, "metric": metric, "model": round(model, 3), "reference": round(reference, 3),
            "diff_pct": round(diff, 1), "source": source}


def capacity_rows(case, n, reg):
    """Existing capacity by type. For PyPSA-Earth's merged units, existing = p_nom_min."""
    g = n.generators[n.generators.carrier != "load shedding"]
    existing = g.p_nom_min.where(g.p_nom_extendable, g.p_nom).groupby(g.carrier).sum()
    renewables = existing.reindex(RENEWABLE, fill_value=0).sum() + n.storage_units.p_nom.sum()
    thermal_ref = reg["cap_2024_ccgt_mw"] + reg["cap_2024_ocgt_mw"] + reg["cap_2024_steam_mw"]
    return [
        row(case, "cap_ccgt_mw", existing.get("CCGT", 0), reg["cap_2024_ccgt_mw"], ONEM),
        row(case, "cap_ocgt_and_steam_mw", existing.get("OCGT", 0), reg["cap_2024_ocgt_mw"] + reg["cap_2024_steam_mw"], ONEM),
        row(case, "cap_oil_mw", existing.get("oil", 0), 0.0, ONEM + " (no oil category)"),
        row(case, "cap_thermal_mw", existing.reindex(GAS + ["oil"], fill_value=0).sum(), thermal_ref, ONEM),
        row(case, "cap_renewable_mw", renewables, reg["cap_2024_re_mw"], ONEM + " (centralised only)"),
    ]


def dispatch_network(n, reg, reshape):
    """Freeze every capacity and set the load to 2024 domestic demand (total demand minus flat imports)."""
    m = n.copy()
    for comp, attr in (("generators", "p_nom"), ("links", "p_nom"), ("stores", "e_nom"), ("lines", "s_nom")):
        getattr(m, comp)[f"{attr}_extendable"] = False

    w = m.snapshot_weightings.generators
    pe_total = m.loads_t.p_set.sum(axis=1)
    total = pe_total
    if reshape:
        load_factor = reg["demand_2024_twh"] * 1e6 / HOURS_2024 / reg["peak_2024_mw"]
        total = reshape_profile(pe_total, w, load_factor, reg["min_to_peak_2030"])
    total = scale_profile(total, w, reg["demand_2024_twh"] * 1e6)
    domestic = subtract_imports(total, w, reg["imports_2024_twh"] * 1e6)
    m.loads_t.p_set = m.loads_t.p_set.div(pe_total, axis=0).mul(domestic, axis=0)  # keep each bus's hourly share

    # Unserved load at a very high price, so a shortage shows up as a number instead of an infeasible model.
    m.add("Carrier", "unserved")
    for bus in m.loads.bus:
        m.add("Generator", f"{bus} unserved", bus=bus, carrier="unserved", p_nom=1e5, marginal_cost=VOLL)
    status, condition = m.optimize(solver_name="highs")
    if status != "ok":
        raise RuntimeError(f"dispatch run failed: {status}, {condition}")
    return m, total


def gas_efficiency(m):
    """Fleet efficiency = gas generation / gas fuel burnt (net calorific value, like technology-data)."""
    w = m.snapshot_weightings.generators
    gen = m.generators_t.p.mul(w, axis=0).sum()
    gas = m.generators.carrier.isin(GAS)
    return gen[gas].sum() / (gen[gas] / m.generators.efficiency[gas]).sum()


def dispatch_rows(case, m, total, reg):
    """Generation by carrier (TWh, weighted by snapshot hours), gas share, efficiency and demand shape vs ONEM 2024."""
    w = m.snapshot_weightings.generators
    gen = m.generators_t.p.mul(w, axis=0).sum().groupby(m.generators.carrier).sum() / 1e6
    hydro = m.storage_units_t.p.mul(w, axis=0).sum().sum() / 1e6 + gen.get("ror", 0)
    gas = gen.reindex(GAS, fill_value=0).sum()
    produced = gen.drop("unserved", errors="ignore").sum() + hydro - gen.get("ror", 0)
    steg_eff = 1000 / (reg["steg_specific_consumption_2024"] * MWH_PER_TOE) / reg["gas_ncv_per_gcv"]
    return [
        row(case, "gen_gas_twh", gas, reg["gen_2024_gas_twh"], ONEM),
        row(case, "gen_oil_twh", gen.get("oil", 0), reg["gen_2024_oil_twh"], ONEM),
        row(case, "gen_wind_twh", gen.get("onwind", 0), reg["gen_2024_wind_twh"], ONEM),
        row(case, "gen_solar_twh", gen.get("solar", 0), reg["gen_2024_solar_twh"], ONEM),
        row(case, "gen_hydro_twh", hydro, reg["gen_2024_hydro_twh"], ONEM),
        row(case, "gen_total_twh", produced, reg["gen_2024_total_twh"], ONEM + " (excl. 0.187 TWh third-party purchases)"),
        row(case, "gas_share", gas / produced, reg["gas_share_2024"], ONEM),
        row(case, "unserved_twh", gen.get("unserved", 0), 0.0, "should be zero"),
        row(case, "gas_fleet_efficiency_ncv", gas_efficiency(m), steg_eff, ONEM + " specific consumption x 1/0.9 (gross to net)"),
        row(case, "peak_mw", total.max(), reg["peak_2024_mw"], ONEM),
        row(case, "load_factor", total.mean() / total.max(), reg["demand_2024_twh"] * 1e6 / HOURS_2024 / reg["peak_2024_mw"],
            ONEM + " (2024 demand / 8,784 h / peak)"),
        row(case, "min_to_peak", total.min() / total.max(), reg["min_to_peak_2030"], "STEG 2030 forecast in JICA 2022"),
    ]


def calibrated_fleet(n, reg, factor):
    """ONEM 2024 thermal fleet: steam units are grouped with the gas turbines (both simple-cycle, low efficiency)."""
    return rebuild_thermal_fleet(
        n, ccgt_mw=reg["cap_2024_ccgt_mw"], ocgt_mw=reg["cap_2024_ocgt_mw"] + reg["cap_2024_steam_mw"],
        ccgt_eff=reg["ccgt_efficiency"], ocgt_eff=reg["ocgt_efficiency"], fuel_cost=reg["gas_price_eur_per_mwh_th"],
        ccgt_vom=reg["ccgt_vom"], ocgt_vom=reg["ocgt_vom"], efficiency_factor=factor)


def main():
    reg = load_register(ROOT / "data" / "assumptions_register.xlsx")
    base = yaml.safe_load((ROOT / "config" / "pipeline.yaml").read_text())["base_network"]
    n = pypsa.Network(base)
    target = 1000 / (reg["steg_specific_consumption_2024"] * MWH_PER_TOE) / reg["gas_ncv_per_gcv"]

    rows = capacity_rows("pypsa_earth", n, reg)
    m, total = dispatch_network(n, reg, reshape=False)
    rows += dispatch_rows("pypsa_earth", m, total, reg)

    # Fit: scaling every existing efficiency by the same factor leaves the merit order unchanged,
    # so one run at factor 1 gives the factor directly; a second run confirms it.
    m1, _ = dispatch_network(calibrated_fleet(n, reg, 1.0), reg, reshape=True)
    factor = target / gas_efficiency(m1)
    print(f"\nfitted efficiency factor for existing gas units: {factor:.4f}")

    cal = calibrated_fleet(n, reg, factor)
    rows += capacity_rows("calibrated", cal, reg)
    m2, total2 = dispatch_network(cal, reg, reshape=True)
    rows += dispatch_rows("calibrated", m2, total2, reg)

    out = ROOT / "results" / "validation.csv"
    table = pd.DataFrame(rows)
    table.to_csv(out, index=False)
    print(table.drop(columns="source").to_string(index=False))
    print(f"\nwritten: {out}")


if __name__ == "__main__":
    main()
