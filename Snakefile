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


rule all:
    input:
        "results/summary.csv",
        "results/avoided.csv",


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
