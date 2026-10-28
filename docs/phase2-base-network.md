# Phase 2: Tunisia base network

PyPSA-Earth v0.10.0 (unmodified) built a prepared, unsolved network for Tunisia using [`config/tn_base.yaml`](../config/tn_base.yaml).
It was first built at 3-hour steps. After the benchmark below, the author chose **1-hour steps** for all scenarios (spec D11). Our scenario pipeline starts from the 1-hour file, whose path is in [`config/pipeline.yaml`](../config/pipeline.yaml).

Command, run from `D:\pypsa-earth`:

```
snakemake -j 1 networks/TN/elec_s_2_ec_lcopt_1h.nc --configfile <repo>/config/tn_base.yaml
```

The file name reads as: `s` simplified, `2` clusters, `ec` extra components (batteries), `lcopt` line expansion left to the optimizer, `1h` one-hour steps.

## Network summary

The 1-hour base network (`elec_s_2_ec_lcopt_1h.nc`) has the same buses, plants and annual load as the 3-hour one below. It has 8,760 snapshots × 1 h, and its peak load is 4,620 MW at 2013-08-07 17:00 (3-hour averaging lowers the peak to 4,604 MW).

Output of `python scripts/inspect_base.py D:\pypsa-earth\networks\TN\elec_s_2_ec_lcopt_3h.nc`:

```
countries: ['TN'] | buses: 4 | lines: 1 | links: 4
snapshots: 2920 x 3 h = 8,760 h (2013-01-01 to 2013-12-31)

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

Annual load: 29.88 TWh | peak: 4,604 MW at 2013-08-07 15:00
```

Checks from the plan: all buses are in Tunisia; there is at least one gas generator (CCGT); annual load is above zero.

## What the network contains

| Item | Value | Note |
|---|---|---|
| Electricity buses | 2: `TN0 0` (north, 36.47° N) and `TN0 1` (south, 34.39° N) | The other 2 buses are the battery buses at the same sites |
| Lines | 1 AC line, 292 km, 2,178 MW | Line capacity can be expanded (`lcopt`) |
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

## Findings to resolve in Phase 3

1. **No OCGT candidate.** PyPSA-Earth adds extendable OCGT only at buses that already have a plant labelled OCGT (`scripts/add_electricity.py`, line 772). The Tunisian plant list has none, so every existing gas unit is labelled CCGT. Spec D1 needs OCGT as a candidate, so our code must add it (Task 13 or the scenario builder).
2. **Fleet labels and sizes.** The 5,580 MW of "CCGT" and 1,409 MW of "oil" are PyPSA-Earth's reading of its plant database. They will be checked against a cited source before use (spec D6).
3. **Existing capacity is costed.** Existing CCGT, onwind and solar are merged with their extendable twins, so `capital_cost × p_nom_opt` also charges for capacity that already exists. This is a constant: differences between scenarios (avoided cost) are unaffected, but absolute system cost is overstated. Phase 4 will either report differences only or subtract this constant.
4. **Gas price.** CCGT marginal cost is 54.6 EUR/MWh from the technology-data default fuel price. It will be replaced by our sourced gas price (register row `gas_price_eur_per_mwh_th`, still pending).

## Build run

| Item | Value |
|---|---|
| Date | 2026-10-27, 17:12 → 23:00 |
| Result | 21 of 21 steps done, exit 0 |
| Runtime | 347.6 min. Downloads took about 5.3 h (data bundle 4 h 51 min, cutout 29 min); modelling steps took about 17 min |
| Disk on D: after the run | `data/` 21.4 GB, `cutouts/` 19.5 GB, `resources/` 0.1 GB; 41.2 GB free |

## Resolution benchmark (Task 7, risk R1)

The base network solved as-is (PyPSA-Earth `solve_network`, HiGHS, same config) at 3-hour and 1-hour steps. Both solves are optimal. This is a plain least-cost expansion with no renewable-share constraint and default costs, so the results are a timing check, not study results.

Command: `snakemake -j 1 results/TN/networks/elec_s_2_ec_lcopt_{3h,1h}.nc --configfile <repo>/config/tn_base.yaml`

| | 3 h | 1 h | 1 h vs 3 h |
|---|---|---|---|
| Snapshots | 2,920 | 8,760 | ×3 |
| LP size (rows × columns) | 154,779 × 75,934 | 464,299 × 227,774 | ×3 |
| HiGHS solve time | 49.9 s | 535.8 s | ×10.7 |
| Whole `solve_network` step | 69.6 s | 582.3 s | ×8.4 |
| Peak memory (process tree) | 0.72 GiB | 1.26 GiB | ×1.8 |
| Objective (M EUR/yr, excl. constant 842.5) | 1,369.3 | 1,374.0 | +0.3% |
| Solar built (MW) | 6,633 | 6,459 | −2.6% |
| Onshore wind built (MW) | 2,023 | 1,948 | −3.7% |
| CCGT generation (TWh) | 15.4 | 15.9 | +3.2% |
| Batteries built | 0 | 0 | |
| Peak load (MW) | 4,604 | 4,620 | 3-hour averaging smooths the peak |

Solve times are from the HiGHS and Snakemake logs. Snakemake cannot measure memory on Windows ("unable to collect cpu and memory benchmark statistics"), so peak memory comes from a second run of each solve, sampling the memory of the whole process tree every 0.5 s. That second run reproduced both objectives exactly; its HiGHS times were 58.5 s (3 h) and 578.2 s (1 h), so solve times vary by about ±10% between runs. Machine: i3-1215U, 24 GB RAM, 1 Snakemake core.

During solving, PyPSA-Earth adds `load shedding` generators priced at 100 EUR/kWh, i.e. 100,000 EUR/MWh (`configs/solving.default.yaml`). It also adds tiny random "noisy costs" so the solver has a unique optimum. Both runs shed 0 TWh. Our Phase 4 pipeline must decide whether to keep both settings.

## Notes

The `GUROBI error: Unknown parameter '_test'` line at the top of the log is a harmless check by the `pulp` library for an installed commercial solver. Gurobi is not used.
