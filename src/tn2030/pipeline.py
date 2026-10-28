"""The three pipeline steps, called from the Snakefile: build -> solve -> summarize."""

import time
from pathlib import Path

import pandas as pd
import pypsa

from tn2030.checks import sanity_check
from tn2030.constraints import res_share, solve_network
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
    """Solve with the 35% renewable target, then run the sanity checks (an error stops the pipeline)."""
    r = load_register(register_path)
    n = pypsa.Network(str(in_path))
    start = time.time()
    solve_network(n, r["re_target_2030"])
    minutes = (time.time() - start) / 60

    # The model's load is domestic (imports removed as a flat flow), so compare its peak on the same basis.
    hours = n.snapshot_weightings.generators.sum()
    peak_ref = r["peak_ref_2030_mw"] - r["imports_2024_twh"] * 1e6 / hours
    warnings = sanity_check(n, r["re_target_2030"], pd.read_csv(committed_path), peak_ref)
    for w in warnings:
        print("WARNING:", w)
    Path(f"{out_path}.warnings.txt").write_text(
        f"solve time: {minutes:.1f} min\n" + "".join(f"WARNING: {w}\n" for w in warnings), encoding="utf-8")
    n.export_to_netcdf(out_path)


def summarize_step(solved_paths: list[Path], scenario_paths: list[Path], summary_out: Path, avoided_out: Path) -> None:
    """One row per scenario; then each scenario against its reference (self-references skipped)."""
    rows, refs = {}, {}
    for solved, scen_path in zip(solved_paths, scenario_paths):
        scen = load_scenario(scen_path)
        n = pypsa.Network(str(solved))
        rows[scen["name"]] = pd.concat([summarize(n), pd.Series({"res_share": res_share(n)})])
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
