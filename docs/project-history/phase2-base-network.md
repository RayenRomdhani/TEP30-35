# Phase 2: Tunisia base network

PyPSA-Earth v0.10.0 (unmodified) built a prepared, unsolved network for Tunisia using [`config/tn_base.yaml`](../../config/tn_base.yaml).
It was first built at 3-hour steps. After the benchmark below, the author chose **1-hour steps** for all scenarios (spec D11). Our scenario pipeline starts from the 1-hour file, whose path is in [`config/pipeline.yaml`](../../config/pipeline.yaml).

Command to rebuild it, run from `D:\pypsa-earth`:

```
snakemake -j 1 networks/TN/elec_s_2_ec_lcopt_1h.nc --configfile <repo>/config/tn_base.yaml
```

The file name reads as: `s` simplified, `2` clusters, `ec` extra components (batteries), `lcopt` line expansion left to the optimizer, `1h` one-hour steps.
The long build (see "Build run" below) produced the 3-hour file. The 1-hour file was then made from the same clustered network in 11 s (`prepare_network`, 2026-10-27 23:03, inside the benchmark run).

## Network summary

Output of `python scripts/dev/inspect_base.py D:\pypsa-earth\networks\TN\elec_s_2_ec_lcopt_1h.nc`:

```
network:   D:\pypsa-earth\networks\TN\elec_s_2_ec_lcopt_1h.nc
countries: ['TN'] | buses: 4 | lines: 1 | links: 4
snapshots: 8760 x 1 h = 8,760 h (2013-01-01 to 2013-12-31)

Generators by carrier (existing p_nom, MW / extendable?):
  CCGT               5,580 MW   extendable
  oil                1,409 MW   fixed
  onwind               283 MW   extendable
  ror                    6 MW   fixed
  solar                508 MW   extendable

StorageUnits by carrier:
  hydro                 49 MW   fixed

Stores by carrier:
  battery                0 MWh   extendable

Annual load: 29.88 TWh | peak: 4,620 MW at 2013-08-07 17:00
```

Checks from the plan: all buses are in Tunisia; there is at least one gas generator (CCGT); annual load is above zero.
The 3-hour file has identical output except the snapshot line (`2920 x 3 h`) and the peak (4,604 MW at 15:00): averaging over 3 hours lowers the peak.

## What the network contains

| Item | Value | Note |
|---|---|---|
| Electricity buses | 2: `TN0 0` (north, 36.47° N) and `TN0 1` (south, 34.39° N) | The other 2 buses are the battery buses at the same sites |
| Lines | 1 AC line, 292 km, 2,178 MW | Usable limit is 70% of that, about 1,525 MW (`s_max_pu` = 0.7, the N-1 security margin in the build log). Capacity can be expanded (`lcopt`) |
| Links | 4: battery charger and discharger at each bus | Extendable |
| Weather year | 2013 (PyPSA-Earth default for wind, solar and the load shape) | Spec D10 |
| Load | GEGIS projection for 2030 (PyPSA-Earth default `load_options`) | Rescaled to our sourced 2030 demand in Phase 3 (spec D2) |
| Cost data | technology-data v0.15.0, year 2030, discount rate 7.1% (defaults) | Same source as the assumptions register |

Existing fleet as PyPSA-Earth sees it, by bus. `p_nom_min` is the existing capacity the model must keep. Extendable units can add capacity above it.

| Generator | p_nom (MW) | p_nom_min (MW) | Extendable |
|---|---|---|---|
| TN0 0 CCGT | 4,075 | 4,075 | yes |
| TN0 1 CCGT | 1,505 | 1,505 | yes |
| TN0 0 oil | 1,183 | 1,183 | no |
| TN0 1 oil | 226 | 226 | no |
| TN0 0 onwind | 283 | 283 | yes |
| TN0 1 onwind | 0 | 0 | yes |
| TN0 0 solar | 164 | 1 | yes |
| TN0 1 solar | 344 | 245 | yes |
| TN0 0 ror | 6 | 0 | no |
| TN0 0 hydro (storage) | 49 | – | no |

The build log reports that solar capacity was topped up from IRENA statistics: 0.25 GW from the plant database, an IRENA figure of 0.51 GW, and 0.26 GW added to close the gap. The added 0.26 GW is in `p_nom` but not in `p_nom_min`, so the optimizer may drop it.

## Carriers actually used

These feed the constants in Task 13 (renewable share constraint):

- Generators: `CCGT`, `oil`, `onwind`, `solar`, `ror`
- StorageUnits: `hydro`
- Stores and Links: `battery`, `battery charger`, `battery discharger`

`OCGT` is defined as a carrier but has **no generator**.

## Findings to resolve in Phases 3 and 4

1. **No OCGT candidate.** PyPSA-Earth adds extendable OCGT only at buses that already have a plant labelled OCGT (`scripts/add_electricity.py`, line 772). The Tunisian plant list has none, so every existing gas unit is labelled CCGT. Spec D1 needs OCGT as a candidate, so our code must add it (Task 13 or the scenario builder).
2. **Fleet labels and sizes.** The 5,580 MW of "CCGT" and 1,409 MW of "oil" are PyPSA-Earth's reading of its plant database. They will be checked against a cited source before use (spec D6).
3. **Existing capacity is costed.** Existing CCGT, onwind and solar are merged with their extendable twins, so `capital_cost × p_nom_opt` includes capacity that already exists.
   - PyPSA separates this fixed part: it is `n.objective_constant` (842.45 M EUR/yr here), and `n.objective` excludes it.
   - Statistics such as `n.statistics.capex()` do include it. That is what plan Task 14's `system_cost_meur` uses, so absolute system cost there would be overstated.
   - Differences between scenarios (avoided cost) are unaffected, as long as the constant is the same in every scenario.
   - Caveat: the constant includes the 262 MW IRENA solar top-up, which the optimizer is free to drop.
   - Phase 4 decides whether to report differences only or subtract the constant.
4. **Gas price.** CCGT marginal cost is 54.6 EUR/MWh from the technology-data default fuel price. It will be replaced by our sourced gas price (register row `gas_price_eur_per_mwh_th`, still pending).
5. **Existing CCGT efficiency.** The merged existing CCGT carries the new-build efficiency (0.58) and annuity from technology-data. Phase 3 calibration should check the existing fleet's efficiency.
6. **Hydro is tiny.** In the solved networks, run-of-river produces 2.5 GWh/yr and the hydro dam's total inflow is 7.2 GWh/yr, so hydro adds almost nothing toward the 35% target. Check against sourced hydro generation in Task 10.
7. **What counts as new capacity.** Plan Task 14 defines new capacity as `p_nom_opt − p_nom_min`. That counts the 262 MW IRENA solar top-up as new. Decide how to treat it.

## Build run

| Item | Value |
|---|---|
| Date | 2026-10-27, 17:12 → 23:00 |
| Result | 21 of 21 steps done, exit 0 |
| Runtime | 347.6 min in total. Data bundles 4 h 51 min, weather cutout 29 min, OpenStreetMap download 3 min, modelling steps 14 min (22:37 → 22:51). The last ~9 min between the final step (22:51:34) and the timer's end (23:00:10) were not spent in any Snakemake step (probably `conda run` passing on its buffered output; the log is 2.7 million lines). |
| Download size | About 16 GB zipped: Africa weather cutouts 10.0 GB and the global `bundle_data_earth` 6.2 GB (Zenodo file sizes checked before the download; `configs/bundle_config.yaml` line 304 also gives "about 10GB (zipped)" for the cutouts), plus small bundles |
| Disk on D: after the run | `data/` 21.4 GB (largest: `landcover` 7.4, `gebco` 7.0, `hydrobasins_hydroshare` 2.7, `copernicus` 1.6 GB), `cutouts/` 19.5 GB (`cutout-2013-era5.nc`), `resources/` 0.1 GB; 41.2 GB free |

## Resolution benchmark (Task 7, risk R1)

The base network solved as-is (PyPSA-Earth `solve_network`, HiGHS, same config) at 3-hour and 1-hour steps. HiGHS reports both solves "Optimal". In the 1 h solve, the interior-point crossover first ended imprecise ("Unwelcome IPX status"); HiGHS then cleaned up with simplex and reported Optimal. Watch for it in the scenario runs. This is a plain least-cost expansion with no renewable-share constraint and default costs, so the results are a timing check, not study results.

Command: `snakemake -j 1 results/TN/networks/elec_s_2_ec_lcopt_{3h,1h}.nc --configfile <repo>/config/tn_base.yaml`

| | 3 h | 1 h | 1 h vs 3 h |
|---|---|---|---|
| Snapshots | 2,920 | 8,760 | ×3 |
| LP size (rows × columns) | 154,779 × 75,934 | 464,299 × 227,774 | ×3 |
| HiGHS run time | 50.7 s | 546.7 s | ×10.8 |
| Whole `solve_network` step | 69.6 s | 582.3 s | ×8.4 |
| Peak memory (process tree) | 0.72 GiB | 1.26 GiB | ×1.8 |
| Objective (M EUR/yr, excl. constant 842.5) | 1,369.3 | 1,374.0 | +0.3% |
| Solar built (MW) | 6,633 | 6,459 | −2.6% |
| Onshore wind built (MW) | 2,023 | 1,948 | −3.7% |
| CCGT generation (TWh) | 15.44 | 15.86 | +2.7% |
| Batteries built | 0 | 0 | |
| Peak load (MW) | 4,604 | 4,620 | 3-hour averaging smooths the peak |

Sources (verbatim log lines in [`docs/project-history/evidence/phase2-run-logs.txt`](evidence/phase2-run-logs.txt)):
- **HiGHS run time:** the "HiGHS run time" line of the first run.
- **Step time:** the Snakemake rule timestamps of the first run.
- **Peak memory:** [`scripts/dev/peak_ram.py`](../../scripts/dev/peak_ram.py). Snakemake cannot measure memory on Windows ("unable to collect cpu and memory benchmark statistics"), so a second run of each solve sampled the whole process tree's memory every 0.5 s.

The second run reproduced both objectives exactly. Its HiGHS run times were 59.5 s (3 h) and 591.8 s (1 h), so times vary by about 10% between runs. The second run overwrote `D:\pypsa-earth\benchmarks\TN\solve_network\`, so those files hold its times, not the first run's.

Machine: i3-1215U, 24 GB RAM. Snakemake ran one job at a time; HiGHS used 4 threads (`highs-default` preset).

During solving, PyPSA-Earth adds `load shedding` generators at every bus, including the two battery buses, priced at 100 EUR/kWh, i.e. 100,000 EUR/MWh (`configs/solving.default.yaml`). It also adds tiny random "noisy costs" so the solver has a unique optimum. Both runs shed 0 TWh. Our Phase 4 pipeline must decide whether to keep both settings.

## Notes

The `GUROBI error: Unknown parameter '_test'` line at the top of the log is a harmless check by the `pulp` library for an installed commercial solver. Gurobi is not used.
