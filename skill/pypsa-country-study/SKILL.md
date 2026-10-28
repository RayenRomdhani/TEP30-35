---
name: pypsa-country-study
description: Use when planning, building or reviewing a single-country power-system study on PyPSA-Earth (a few nodes, 2030-style capacity expansion, scenarios such as efficiency, demand flexibility or fuel-price sensitivity), especially when inputs must be sourced, results defended in an interview or report, or the run is on native Windows.
---

# PyPSA-Earth country study

## Overview

A country study is four stages, each ending with evidence before the next starts: **base network → 2024 validation → scenario pipeline → deliverables**. PyPSA-Earth stays unmodified; all changes live in your own package, applied to its prepared network. Most wrong results come from a short list of known traps (see `pitfalls.md`), not from the solver.

Worked example: the Tunisia study at https://github.com/RayenRomdhani/TEP30-35 (`src/tn2030/`, `docs/project-history/phase*.md`, and the learning path in `docs/learn/`). File references in `pitfalls.md` point there.

## When to use

- One country, 1-10 nodes, one target year, least-cost expansion with HiGHS
- Comparing scenarios against a reference ("what one MWh saved avoids")
- Not for multi-country or sector-coupled (PyPSA-Eur-Sec) studies

## Stages and gates

| Stage | Build | Gate (evidence) |
|---|---|---|
| 0. Rules | Assumptions register (id, value, unit, sourced/assumption, URL); ask before any download (Tunisia bundle: ~16 GB, ~41 GB on disk) | Every number has a row |
| 1. Base network | PyPSA-Earth tutorial run, then the country config; benchmark 1 h vs 3 h steps on the real network | Inspection table: buses, carriers, capacity by carrier, load total and peak |
| 2. Validation year | Rebuild the thermal fleet from official statistics, reshape demand, fit one efficiency factor to measured fuel use | Model vs official: capacity, generation, fuel burnt (independent of the fit), peak |
| 3. Scenarios | `build_scenario → solve → summarize` in Snakemake; custom constraints in `extra_functionality`; post-solve checks that stop the pipeline | All runs pass checks; summary and avoided tables |
| 4. Deliverables | Figures, README, report, deck, all numbers read from the result CSVs | Reproduce from a clean clone up to `pytest` |

## Quick reference: traps that change results

| Trap | Fix |
|---|---|
| Energy sums without `n.snapshot_weightings.generators` | Multiply every MWh, fuel, CO2 and share sum; test on a 3-hour-step fixture |
| Carrier names differ (`onwind`, `ror`, `hydro` storage) | Read them from the built network; raise if a constraint matches no carrier |
| Open plant list mislabels the fleet (all gas = CCGT, phantom oil) | Rebuild existing thermal units from official statistics |
| No OCGT is added unless the plant list has one | Add new-build OCGT candidates per bus yourself |
| Battery inverter cost sits on the charger only | Constrain charger `p_nom` = efficiency × discharger `p_nom` |
| No reserve rule | Without one, saving demand never shows capacity value |
| Shiftable load as free storage | Daily reset, rolling-window duration limit, one direction per hour |
| Comparing scenarios at different fuel prices | Each scenario names its own reference; zero saving raises |
| PyPSA omits all-zero output columns | `reindex(columns=..., fill_value=0)` before summing |

Detection and code for each, plus the rest: `pitfalls.md`.

## Common mistakes

- Reporting absolute system cost: it includes existing assets PyPSA-Earth costs as extendable. Report differences.
- Treating a non-binding renewable target as a finding about the target: say it does not bind and why (no build-rate limit).
- Fitting a calibration factor and then "validating" on the same number. Validate on an independent one.
