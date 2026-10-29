# Scenario pipeline: for each config/scenarios/*.yaml, build -> solve -> summarize (plan Task 16).
# Run from the repo root:  snakemake -j 1        (dry run: snakemake -n)

import sys
from pathlib import Path

sys.path.insert(0, "src")  # use this checkout's tn2030, not another pip-installed copy
from tn2030 import pipeline

configfile: "config/pipeline.yaml"

SCENARIOS = sorted(p.stem for p in Path("config/scenarios").glob("*.yaml"))
REGISTER = "data/assumptions_register.xlsx"
COMMITTED = "data/committed_projects.csv"
CODE = sorted(str(p) for p in Path("src/tn2030").glob("*.py"))  # a code change re-runs builds and solves


PLAN_YEARS = [2027, 2028, 2029, 2030]

wildcard_constraints:
    year=r"\d{4}",


rule all:
    input:
        "results/summary.csv",
        "results/avoided.csv",
        "results/pathway_summary.csv",
        "results/pathway_avoided.csv",


# ---------- the 2027-2030 pathway: each year starts from the year before ----------
# 2025 and 2026 are solved once ("history", base case); every scenario then branches off from 2026.

def previous_year(w):
    year = int(w.year)
    if w.s == "history":
        return [] if year == 2025 else [f"results/pathway/history_{year - 1}_solved.nc"]
    return [f"results/pathway/history_2026_solved.nc" if year == 2027 else f"results/pathway/{w.s}_{year - 1}_solved.nc"]


rule pathway_year:
    input:
        base=config["base_network"],
        scenario=lambda w: "config/scenarios/S0.yaml" if w.s == "history" else f"config/scenarios/{w.s}.yaml",
        register=REGISTER,
        committed=COMMITTED,
        code=CODE,
        prev=previous_year,
    output:
        "results/pathway/{s}_{year}_solved.nc",
    run:
        pipeline.pathway_step(Path(input.base), Path(input.scenario), Path(input.register), Path(input.committed),
                              int(wildcards.year), Path(input.prev[0]) if input.prev else None, Path(output[0]))


rule pathway_summarize:
    input:
        solved=expand("results/pathway/{s}_{year}_solved.nc", s=SCENARIOS, year=PLAN_YEARS),
        register=REGISTER,
    output:
        summary="results/pathway_summary.csv",
        avoided="results/pathway_avoided.csv",
    run:
        from tn2030.register import load_register
        solved = {(s, y): Path(f"results/pathway/{s}_{y}_solved.nc") for s in SCENARIOS for y in PLAN_YEARS}
        pipeline.pathway_summarize_step(solved, {s: Path(f"config/scenarios/{s}.yaml") for s in SCENARIOS},
                                        load_register(input.register)["re_target_2030"],
                                        Path(output.summary), Path(output.avoided))


rule build_scenario:
    input:
        base=config["base_network"],
        scenario="config/scenarios/{s}.yaml",
        register=REGISTER,
        committed=COMMITTED,
        code=CODE,
    output:
        "results/networks/{s}_built.nc",
    run:
        pipeline.build_step(Path(input.base), Path(input.scenario), Path(input.register), Path(input.committed),
                            Path(output[0]))


rule solve:
    input:
        network="results/networks/{s}_built.nc",
        register=REGISTER,
        committed=COMMITTED,
        code=CODE,
    output:
        "results/networks/{s}_solved.nc",
    run:
        pipeline.solve_step(Path(input.network), Path(output[0]), Path(input.register), Path(input.committed))


rule summarize:
    input:
        solved=expand("results/networks/{s}_solved.nc", s=SCENARIOS),
        scenarios=expand("config/scenarios/{s}.yaml", s=SCENARIOS),
    output:
        summary="results/summary.csv",
        avoided="results/avoided.csv",
    run:
        pipeline.summarize_step([Path(p) for p in input.solved], [Path(p) for p in input.scenarios],
                                Path(output.summary), Path(output.avoided))
