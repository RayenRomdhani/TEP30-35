# Design spec: The value of energy efficiency in Tunisia's power system (2030)

- **Date:** 2026-10-27
- **Author:** Rayen Romdhani (ENIM, Energy Engineering)
- **Status:** Approved 2026-10-27
- **Tooling:** PyPSA-Earth (pinned version) + own Python package and Snakemake pipeline, HiGHS solver

---

## 1. Research question

> How much generation capacity, gas consumption, system cost and CO2 can Tunisia avoid in 2030 through energy efficiency and demand flexibility, while meeting its 35% renewable electricity target?

**Headline metric:** avoided system cost (EUR), CO2 (t), gas (MWh_th) and new capacity (MW) **per MWh of electricity demand saved**.

**What the result means (stated up front):** efficiency programme costs are *not* modelled. The headline number is the
**system value** of efficiency: the most an efficiency measure could cost per MWh saved and still pay off for the power
system. If a sourced ANME programme cost is found, it is compared against this value in the report.

## 2. Policy anchor

| Item | Value | Source | Note |
|---|---|---|---|
| Renewable target | **35% of electricity generation by 2030** | Head of Government, reaffirmed 9 Oct 2026 ([TAP](https://www.tap.info.tn/fr/Portail-%C3%A0-la-Une-FR-top/20672933-%C3%A9nergie-la)) | Earlier documents (ANME, AICS) say 30%; raised to 35% in 2022 ([REGlobal](https://reglobal.org/greening-energy-mix-investments-focus-on-increasing-renewables-in-tunisia/)). Both recorded in the register. |
| Peak-demand reduction plan | 300 MW | Same TAP article (Oct 2026 action plan) | Anchors the flexibility size. |

## 3. Modelling approach (decisions)

| # | Decision | Choice |
|---|---|---|
| D1 | Capacity | **Brownfield capacity expansion.** Existing plants + committed projects are fixed; the optimizer builds new gas (CCGT, OCGT), solar PV, onshore wind and Li-ion batteries at least cost. Avoided capacity = difference in what gets built. |
| D2 | 2030 demand | **2024 actual demand × (1 + g)^6.** 2024 demand from ONEM (22.51 TWh; Ember kept as a cross-check). Growth rate g = 3.2%/yr, STEG's base-case forecast (JICA 2022), chosen 2026-10-28 over REGlobal's unsourced 3.7%. Hourly shape from PyPSA-Earth, **reshaped** to the official load factor and minimum/peak ratio (Phase 3, `docs/phase3-validation.md`), then scaled to the annual total. Resulting peak checked against STEG's 6,000 MW 2030 forecast (warning, not a hard fail). |
| D3 | Imports | **Fixed at the cited 2024 import volume**, flat hourly profile, subtracted from demand. Identical in all scenarios, so efficiency only reduces domestic generation. |
| D4 | Efficiency | **Main runs: uniform cut** of every hour by 10 / 15 / 20%. **Sensitivity at -15%: cooling-weighted** (same annual MWh saved, concentrated on the cooling component, see §5.2). |
| D5 | Flexibility | **Shiftable load** capped at 300 MW, shift up to 3 h, energy-neutral each day. Sensitivity at 600 MW. Batteries are extendable in **all** scenarios, so scenario 3 isolates the extra value of demand shifting. |
| D6 | Existing fleet | **ONEM 2024 thermal fleet by type** (2,527 MW combined cycle; 2,457 MW gas turbines + 660 MW steam), replacing PyPSA-Earth's labels after the Phase 3 validation, with one fitted efficiency factor for existing gas units; PyPSA-Earth's renewables and hydro **+ committed projects** (under construction or signed contract, each with a cited source). Announced-only projects are excluded. Steam units are kept in 2030 (author, 2026-10-28). |
| D7 | Technology costs | PyPSA `technology-data`, 2030 values, version shipped with the pinned PyPSA-Earth. Every value copied into the register. |
| D8 | Gas price | **Economic (opportunity) cost**, not STEG's subsidised tariff. Base value from technology-data; **±50% sensitivity** (labelled assumption). |
| D9 | CO2 | **Reported, not priced** (no carbon price in Tunisia). Emission factor from technology-data. |
| D10 | Weather | PyPSA-Earth default weather year from its data bundle (no ERA5 account). Ask before any download > 2 GB. |
| D11 | Resolution | Tunisia only; **2 clusters** (4 if runtime allows); **1-hour** time steps (decided 2026-10-28 after the risk R1 benchmark; first planned at 3 h); HiGHS. |
| D12 | RE constraint | One annual constraint: (solar + wind + hydro generation) ≥ 35% × total **domestic** generation. Storage discharge and imports excluded from both sides. Use a built-in PyPSA-Earth option if one exists (checked in Phase 2), else a custom `extra_functionality`. |
| D13 | ELMED (Italy link) | **Optional scenario 4**, decided after Phase 4 depending on time. |

## 4. Scenario matrix

| ID | Name | Efficiency | Flexibility | Gas price | Purpose |
|---|---|---|---|---|---|
| S0 | BASE | 0% | none | base | Reference |
| S1-10 / S1-15 / S1-20 | EFF | -10 / -15 / -20% uniform | none | base | Core efficiency effect |
| S1-15C | EFF-COOL | -15% cooling-weighted | none | base | Does targeting cooling avoid more per MWh? |
| S2-300 | EFF+FLEX | -15% uniform | 300 MW, ±3 h | base | Extra value of shifting |
| S2-600 | EFF+FLEX-HI | -15% uniform | 600 MW, ±3 h | base | Flexibility sensitivity |
| G-lo / G-hi | Gas sensitivity | S0 and S1-15 | none | -50% / +50% | Robustness of headline metric (4 runs) |
| S3 | ELMED (optional) | -15% | none | base | Interconnection value |

Core: 11 solves. Each scenario is one small YAML file in `config/scenarios/`.

## 5. Methods

### 5.1 Demand calibration
1. `D2024` = annual demand 2024 (TWh), source in register.
2. `D2030 = D2024 × (1 + g)^6`.
3. Reshape PyPSA-Earth's hourly profile to the 2024 load factor (ONEM) and STEG's minimum/peak ratio, keeping each hour's rank (Phase 3 calibration), then scale it so its annual sum equals `D2030`.
4. Apply the scenario's efficiency cut (§5.2 or uniform) to this **total** demand profile.
5. Subtract the flat import profile `I2024 / 8760` from every hour. The result is the domestic load the model must
   serve. Because imports are the same in every scenario, all savings fall on domestic generation.
6. Report the 2030 peak; warn if it differs from 6,000 MW by more than 10%.

### 5.2 Cooling-weighted efficiency
1. Baseline by hour of day = average load in shoulder months (April, May, October, November).
2. Cooling component(t) = max(0, load(t) − baseline(hour of t)) for June–September, else 0.
3. Spread the required annual saving (15% of annual demand) in proportion to the cooling component.
4. If the cooling component is smaller than the required saving, the rest is cut uniformly. The share that could be placed on cooling is reported.
5. Load never goes below zero (tested).

### 5.3 Shiftable load
Modelled as virtual storage at the demand bus: power ≤ cap (300 or 600 MW), energy ≤ cap × 3 h, round-trip efficiency 1, no investment cost, state of charge forced to zero at the start of each day (energy-neutral daily).

### 5.4 Output metrics
| Output | Definition |
|---|---|
| Capacity mix | Installed MW by technology (existing + committed + new) |
| Generation mix | TWh by technology |
| Gas use | Σ gas generation / plant efficiency (TWh_th) |
| CO2 | Gas use × emission factor (Mt) |
| System cost | Annualised capex of new builds + fixed O&M + fuel (M EUR/yr), from the objective |
| Marginal price | Load-weighted average of the bus energy-balance dual (EUR/MWh) + price duration curve |
| Summer week dispatch | The 7 days centred on the annual peak load hour |
| **Avoided X per MWh saved** | (X_S0 − X_s) / (D_S0 − D_s), D = annual total electricity demand after efficiency (imports are equal in all scenarios, so they cancel) |

All figures use one palette, labelled axes with units, and a source line.

## 6. Architecture

**Hybrid.** PyPSA-Earth (pinned tag, unmodified) builds the base Tunisia network: grid, existing plants, renewable
profiles and costs. Our own Snakemake pipeline takes that network and, per scenario, runs
`build_scenario → solve → summarize`.

```
TEP30-35/
├── README.md, environment.yml, Snakefile
├── config/      tn_base.yaml (PyPSA-Earth overrides) + scenarios/*.yaml
├── src/tn2030/  demand.py · efficiency.py · flexibility.py · constraints.py · results.py · plotting.py
├── scripts/     phase1_toy_model.py, make_figures.py
├── tests/       pytest unit + integration tests
├── data/        assumptions_register.xlsx (+ raw/ gitignored, with a list of sources)
├── results/     CSV tables, figures (small, committed)
├── report/      report.docx, deck.pptx
└── docs/        this spec, plan.md, config-change log, skills-inventory.md
```

**Locations:** project repo on C: (small). Miniforge, PyPSA-Earth and its data on **D:** (C: has 14 GB free).

**Environment:** one conda environment, built from PyPSA-Earth's pinned environment file plus our extras (pytest,
openpyxl), exported to `environment.yml`. Created at the start of Phase 1 (software only, no data download).

## 7. Testing

- **Unit tests (TDD, pytest):** demand scaling hits the target annual total; imports subtracted correctly; uniform cut
  reduces every hour by exactly x%; cooling-weighted cut keeps the same annual saving and never goes negative;
  shiftable load is energy-neutral daily; avoided-per-MWh formula.
- **Integration test:** the Phase 1 toy network runs through `build_scenario → solve → summarize` in seconds.
- **Sanity checks after every real solve (run fails if broken):** energy balance closes; RE share ≥ 35%; no unmet
  load; built capacity ≥ committed projects. Peak vs ~6 GW is a warning.

## 8. Phases and evidence gates

| Phase | Output | Evidence before "done" |
|---|---|---|
| 0 | Skill inventory, this spec, `docs/plan.md` | Files committed |
| 1 | Environment + single-node toy model (gas, solar, wind, battery, hourly load) + explanation of objective and constraints | Solve log, dispatch plot, passing tests |
| 2 | PyPSA-Earth installed; tutorial run; TN base network built | Run logs, network summary, config-change log |
| 3 | Baseline validated against STEG / IRENA / Ember; committed-projects list | Comparison table, explained gaps, justified calibration |
| 4 | All scenarios run through our Snakemake pipeline | Results table, sanity checks passing |
| 5 | Charts, report, deck, README, reusable skill | Rendered files, clean repo |

Each phase: own git branch, code review, then a 5-line summary + evidence, then wait for "go".

## 9. Risks and open points

| ID | Risk | Mitigation |
|---|---|---|
| R1 | **Time resolution vs shift window.** At 3-hour steps, a "shift up to 3 h" can only move load by exactly one step, a coarse approximation. | Benchmark in Phase 2. If a 1-hour run for 2 clusters solves in reasonable time, use 1 h for **all** scenarios (needs your approval). Otherwise keep 3 h and state the limitation. **Outcome (2026-10-28):** 1 h solved in about 10 min with 1.3 GiB peak memory (3 h: about 1 min, 0.7 GiB), and 3 h built 2.7% more solar and 3.9% more wind than 1 h. The author chose 1 h for all scenarios. See `docs/phase2-base-network.md`. |
| R2 | PyPSA-Earth install problems on native Windows | systematic-debugging; WSL fallback only with your approval |
| R3 | Data bundle larger than 2 GB | Check size first; ask before downloading |
| R4 | Open plant databases inaccurate for Tunisia | Phase 3 calibration against STEG, documented |
| R5 | PyPSA-Earth's hourly demand shape poor for Tunisia | Compare with any public STEG load curve; document |
| R6 | Growth rate g only from a secondary source | Labelled as such; replaced if the STEG master plan is found |
| R7 | Ember gas share figures disagree (~85% vs ~95%) | Use Ember directly in Phase 3; document the denominator |

## 10. Rules

- No invented data. Every input number goes in `data/assumptions_register.xlsx` with a source link, or is labelled as an assumption.
- Simple, commented code the author can defend in an interview.
- Deliverables in English.
- Nothing pushed or published without explicit approval.
