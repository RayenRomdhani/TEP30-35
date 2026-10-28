# Pitfalls: detection and fix

Each entry: what goes wrong, how to see it, how to fix it, and where the Tunisia example does it. Versions: PyPSA-Earth v0.10.0 with its own locked Windows environment (`envs/win-64.lock.yaml`), which pins PyPSA 0.30.3, linopy 0.5.5, HiGHS 1.11 and Snakemake 7.32.

Commands used (run in the PyPSA-Earth folder, env activated):

```bash
snakemake -j 1 solve_all_networks --configfile config.tutorial.yaml
```
```bash
snakemake -j 1 networks/<CC>/elec_s_2_ec_lcopt_1h.nc --configfile <repo>/config/<cc>_base.yaml
```

The second builds the prepared, unsolved network (`s` simplified, `2` clusters, `ec` batteries, `lcopt` line expansion, `1h` steps) that the scenario pipeline starts from.

## Country differences to settle first

The Tunisia example is a gas system with no modelled interconnector. Before reusing a step, check:
- **Fuel mix.** Coal, oil or nuclear fleets get the same treatment as gas: rebuild existing units by type from official statistics, calibrate their efficiency on measured fuel use per fuel, and decide which count as firm. The fuel-price sensitivity then scales the fuel you study.
- **Interconnectors.** Tunisia subtracts a flat import flow from load. A country with large exchanges (e.g. Morocco-Spain) needs either a modelled link with a sourced price profile or an explicit statement that imports are fixed; the "every MWh saved falls on domestic generation" reading only holds for fixed imports.
- **Territory and clustering.** Check which regions the country shapes include and where the cluster borders fall; document the choice.

## Inputs and environment

**Unsourced numbers.** Keep one register (`data/assumptions_register.xlsx`: id, parameter, value, unit, type, source_title, source_url, accessed, notes). Code reads values only through it and refuses a `sourced` row without a URL (`src/tn2030/register.py`). A number with no source is typed `assumption`, never left as a silent default.

**Downloads.** The country build pulls the data bundles and weather cutouts (Tunisia: ~16 GB zipped, ~41 GB on disk, ~6 h). Check the Zenodo sizes and ask before starting.

**Windows.** Antivirus can quarantine files inside the conda env (Bitdefender removed `mamba.exe` and several `.py` files). Symptom: `ModuleNotFoundError` for a package that is installed. Fix: reinstall the package with `--force-reinstall --no-deps`; use `conda` if `mamba` stays blocked. Snakemake cannot measure memory on Windows; sample the process tree yourself if you need peak RAM.

**Resolution.** Benchmark the real network at 3 h and 1 h before choosing (Tunisia, 2 nodes: 1 min vs 10 min; 3 h built ~3% more solar and wind). A shift window of a few hours cannot be represented at 3-hour steps.

## Base network

**Carrier names.** PyPSA-Earth uses `onwind`, `solar`, `ror` (Generator), `hydro` (StorageUnit), `battery` (Store) with `battery charger` / `battery discharger` (Links). A renewable constraint written for `wind` counts nothing and still solves. Fix: raise `ValueError` when no component matches (`constraints.add_min_res_share`).

**Fleet labels.** The open plant list may label every gas unit `CCGT` and add plants that no longer run (`oil`). Compare `n.generators.groupby("carrier").p_nom.sum()` with official statistics. Fix: remove them and add existing units by type at `capital_cost=0`, split across buses by the existing share (`fleet.rebuild_thermal_fleet`).

**No OCGT candidate.** PyPSA-Earth adds extendable OCGT only at buses that already have one. Fix: add an extendable `"<bus> OCGT new"` per AC bus with annualised cost from the register (`fleet.add_ocgt_candidates`).

**Existing capacity is costed.** Existing units are merged with their extendable twin; `n.statistics.capex()` includes their cost (PyPSA keeps it in `n.objective_constant`). Report scenario differences. New capacity = `p_nom_opt - p_nom_min`, with existing kept as `p_nom_min`.

**Load shedding.** PyPSA-Earth's solve adds `load shedding` generators (100 EUR/kWh). Exclude them from generation totals and fail the run if any dispatch.

## Demand and validation

**Demand shape.** The default profile can be far from official statistics (Tunisia: load factor 0.74 vs 0.52). Fix: a rank-preserving reshape `m + (1-m)·x^k`, with `k` found by bisection to hit the official load factor and minimum-to-peak ratio, then rescale the energy (`demand.reshape_profile`).

**Imports.** Subtracting a flat import flow can push night load below zero. Fix: raise, never clip (`demand.subtract_imports`).

**Calibration.** Fit one efficiency factor on existing gas units so the validation year burns the measured fuel (from specific consumption), then check against an independent figure (gas burnt for power from a separate table). Scaling all units by one factor keeps the merit order, so the fit is analytic. The factor also absorbs outages: say so.

## Scenarios

**Cooling-weighted saving without extra data.** Cooling load = summer load above the average shoulder-month load (spring and autumn months) for the same hour of day, clipped at zero. Take the saving from that component first and spread the rest uniformly; report the share that fitted on cooling (`efficiency.cooling_weighted_cut`). Compare it only with a uniform cut of the same annual energy.

**Fuel-price sensitivity.** Scale only the fuel part of marginal cost: `mc += (factor - 1) · fuel_price / efficiency`. VOM and the calibrated efficiency stay as they are; the validation year is not re-fitted, because the fit is on fuel quantity, not cost (`scenario.scale_gas_cost`).

## Constraints

**Renewable share.** In `extra_functionality`: `sum(res · w) - share · sum(all generation · w) >= 0`, with dam hydro from `StorageUnit-p_dispatch` on both sides and storage, imports and load shedding on neither. Test that hydro is counted (switch it off and the test must fail).

**Battery.** PyPSA-Earth puts the whole inverter cost on the charger, so the discharger is free. Add `Link-p_nom[charger] - efficiency · Link-p_nom[discharger] == 0` (as PyPSA-Earth's own `solve_network.py` does).

**Reserve margin.** Without a firm-capacity rule the model never builds peaking plant and efficiency shows no capacity value. Add `sum(new firm p_nom) >= (1 + margin) · peak - existing firm`, with a sourced margin; wind, solar, batteries and flexibility get no credit unless you justify one.

**Shiftable load as a StorageUnit** (`p_nom` = shift cap, `max_hours` = 2 × window, efficiency 1, zero cost):
- start every day half full and force it back to half full at each day's last snapshot (`state_of_charge_set`), including a partial last day;
- limit the duration with a rolling window: state of charge above neutral ≤ what was stored in the last `window` snapshots (and the mirror for below);
- add `p_store + p_dispatch <= p_nom`, or charging and discharging at once (free, lossless) refreshes the window.
A year-cyclic store with a few hours of `max_hours` still moves energy across days.

## Results

**Snapshot weightings.** Every MWh, fuel, CO2 and share sum multiplies by `n.snapshot_weightings.generators`. At 1-hour steps the bug is invisible, so keep a 3-hour-step test fixture.

**Missing output columns.** PyPSA does not store all-zero time series (a battery never built has no `links_t.p1` column). Use `reindex(columns=index, fill_value=0)`.

**Avoided per MWh.** `(reference metric - scenario metric) / (reference demand - scenario demand)`. Each scenario names its reference in its YAML, so fuel-price variants compare at the same price; equal demand raises.

**Post-solve checks** that stop the pipeline: energy balance closes, renewable share met, no load shed, floors kept, committed projects built, reserve met (`checks.sanity_check`).

**Non-binding target.** At current technology costs the least-cost system may exceed the target. Report the realised share, which sensitivity makes it bind, and that the model has no build-rate limit.
