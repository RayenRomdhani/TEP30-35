"""The three pipeline steps, called from the Snakefile: build -> solve -> summarize."""

import time
from pathlib import Path

import pandas as pd
import pypsa

from tn2030.checks import sanity_check
from tn2030.constraints import res_share, solve_network
from tn2030.pathway import build_year, committed_in, limits_from_register, peak_reference
from tn2030.register import load_register
from tn2030.results import avoided_per_mwh, summarize
from tn2030.scenario import build_scenario, load_scenario


def build_step(base_path: Path, scenario_path: Path, register_path: Path, committed_path: Path, out_path: Path,
               calibrate: bool = True) -> None:
    """Base network + scenario file -> network ready to solve."""
    n = build_scenario(pypsa.Network(str(base_path)), load_scenario(scenario_path), load_register(register_path),
                       pd.read_csv(committed_path), calibrate=calibrate)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    n.export_to_netcdf(out_path)


def solve_step(in_path: Path, out_path: Path, register_path: Path, committed_path: Path) -> None:
    """Solve with the 35% renewable target and STEG's reserve margin, then run the sanity checks."""
    r = load_register(register_path)
    n = pypsa.Network(str(in_path))
    start = time.time()
    solve_network(n, r["re_target_2030"], reserve_margin=r["reserve_margin"])
    minutes = (time.time() - start) / 60

    # The model's load is domestic (imports removed as a flat flow), so compare its peak on the same basis.
    hours = n.snapshot_weightings.generators.sum()
    peak_ref = r["peak_ref_2030_mw"] - r["imports_2024_twh"] * 1e6 / hours
    warnings = sanity_check(n, r["re_target_2030"], pd.read_csv(committed_path), peak_ref,
                            reserve_margin=r["reserve_margin"])
    for w in warnings:
        print("WARNING:", w)
    Path(f"{out_path}.warnings.txt").write_text(
        f"solve time: {minutes:.1f} min\n" + "".join(f"WARNING: {w}\n" for w in warnings), encoding="utf-8")
    n.export_to_netcdf(out_path)


def pathway_step(base_path: Path, scenario_path: Path, register_path: Path, committed_path: Path, year: int,
                 prev_path: Path | None, out_path: Path) -> None:
    """One year of the 2027-2030 pathway: build from last year's solved network, solve without forcing the 35%
    target (it is reported instead), check, save."""
    r, committed = load_register(register_path), pd.read_csv(committed_path)
    prev = pypsa.Network(str(prev_path)) if prev_path else None
    n = build_year(pypsa.Network(str(base_path)), load_scenario(scenario_path), r, committed, year, prev, limits_from_register(r))
    start = time.time()
    solve_network(n, None, reserve_margin=r["reserve_margin"])
    minutes = (time.time() - start) / 60
    hours = n.snapshot_weightings.generators.sum()
    warnings = sanity_check(n, 0.0, committed_in(committed, year), peak_reference(r, year, hours),
                            reserve_margin=r["reserve_margin"])
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(f"{out_path}.warnings.txt").write_text(
        f"solve time: {minutes:.1f} min\n" + "".join(f"WARNING: {w}\n" for w in warnings), encoding="utf-8")
    n.export_to_netcdf(out_path)


def pathway_summarize_step(solved: dict[tuple[str, int], Path], scenario_paths: dict[str, Path], target: float,
                           summary_out: Path, avoided_out: Path) -> None:
    """One row per scenario and year; then each scenario against its reference, per year and over the whole plan
    (sum of avoided cost over sum of MWh saved)."""
    rows = []
    for (name, year), path in sorted(solved.items()):
        n = pypsa.Network(str(path))
        share = res_share(n)
        rows.append(pd.concat([pd.Series({"scenario": name, "year": year, "res_share": share, "res_gap_to_target": target - share,
                                          "cooling_share": n.meta.get("cooling_share", 0.0)}), summarize(n)]))
    summary = pd.DataFrame(rows).fillna(0.0)
    summary.to_csv(summary_out, index=False)

    refs = {name: load_scenario(p)["reference"] for name, p in scenario_paths.items()}
    s = summary.set_index(["scenario", "year"])
    out = []
    for name, ref in refs.items():
        if ref == name:
            continue
        years = sorted(s.loc[name].index)
        for year in years:
            out.append({"scenario": name, "reference": ref, "year": year, **avoided_per_mwh(s.loc[(ref, year)], s.loc[(name, year)])})
        # Over the whole plan: totals summed over the years. Each year's new capacity is that year's build only
        # (last year's fleet is its floor), so their sum is everything built 2027-2030; it is divided by the
        # yearly saving reached in 2030.
        saved = {k: s.loc[ref].loc[years, k].sum() - s.loc[name].loc[years, k].sum()
                 for k in ("system_cost_meur", "co2_mt", "gas_use_twh_th", "demand_twh", "new_cap_total_mw")}
        saved_2030 = s.loc[(ref, years[-1]), "demand_twh"] - s.loc[(name, years[-1]), "demand_twh"]
        out.append({"scenario": name, "reference": ref, "year": "2027-2030",
                    "cost_eur_per_mwh": saved["system_cost_meur"] / saved["demand_twh"],
                    "co2_t_per_mwh": saved["co2_mt"] / saved["demand_twh"],
                    "gas_mwh_th_per_mwh": saved["gas_use_twh_th"] / saved["demand_twh"],
                    "capacity_mw_per_twh": saved["new_cap_total_mw"] / saved_2030})
    pd.DataFrame(out).to_csv(avoided_out, index=False)


def summarize_step(solved_paths: list[Path], scenario_paths: list[Path], summary_out: Path, avoided_out: Path) -> None:
    """One row per scenario; then each scenario against its reference (self-references skipped)."""
    rows, refs = {}, {}
    for solved, scen_path in zip(solved_paths, scenario_paths):
        scen = load_scenario(scen_path)
        n = pypsa.Network(str(solved))
        extra = {"res_share": res_share(n), "cooling_share": n.meta.get("cooling_share", 0.0)}
        rows[scen["name"]] = pd.concat([summarize(n), pd.Series(extra)])
        refs[scen["name"]] = scen["reference"]
    summary = pd.DataFrame(rows).T.fillna(0.0)  # a technology not built in one scenario shows as 0
    summary.index.name = "scenario"
    summary.to_csv(summary_out)

    avoided = {name: avoided_per_mwh(summary.loc[ref], summary.loc[name])
               for name, ref in refs.items() if ref != name}
    table = pd.DataFrame(avoided).T
    table.index.name = "scenario"
    table.insert(0, "reference", [refs[name] for name in table.index])
    table.to_csv(avoided_out)
