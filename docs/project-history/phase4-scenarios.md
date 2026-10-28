# Phase 4: Scenarios and runs

**What this phase does:** one Snakemake pipeline turns the calibrated Tunisia base network into the 11 scenarios of spec §4, solves each one as a 2030 least-cost investment and dispatch problem, checks it, and writes two tables:

- [`results/summary.csv`](../../results/summary.csv): one row per scenario (capacity, new capacity, generation, demand, gas, CO2, system cost, average price, renewable share, cooling share).
- [`results/avoided.csv`](../../results/avoided.csv): each scenario against its reference, per MWh of demand saved (the headline metric).

**To reproduce:** run `snakemake -j 1` from the repo root. The base network path is in `config/pipeline.yaml`. The rules depend on the `src/tn2030` code, so a code change re-runs them.

## How a scenario network is built

[`src/tn2030/scenario.py`](../../src/tn2030/scenario.py) `build_scenario`, in the order of spec §5.1:

1. **Calibrate the base network** (`calibrate_base`, Phase 3):
   - official 2024 thermal fleet with the fitted efficiency factor;
   - one new-build OCGT option per bus;
   - existing 2024 wind and solar kept.
2. **Demand shape:** stretch the hourly profile to the official load factor (0.524) and minimum/peak ratio (0.34).
3. **2030 demand:** scale the total to 22.507 TWh × 1.032⁶ = 27.19 TWh.
4. **Efficiency cut:** uniform, or cooling-weighted (below).
5. **Imports:** subtract the flat 2024 import flow (3.11 TWh, about 355 MW every hour). Because imports are equal in all scenarios, every MWh saved falls on domestic generation.
6. **Committed projects** (`data/committed_projects.csv`): their MW become a minimum the optimizer must build.
7. **Gas-price sensitivity:** only the fuel part of gas units' marginal cost changes (×0.5 or ×1.5).
8. **Shiftable load**, for S2-300 and S2-600 only.

### Efficiency in plain words (spec §5.2)

- **Uniform (S1-10/15/20):** every hour of the year is 10, 15 or 20% lower. This is the simplest reading of "15% more efficient": the same appliances, each using less.
- **Cooling-weighted (S1-15C):** the same 15% of annual energy is saved, but first from air-conditioning load.
  - The cooling load is the summer load above the average shoulder-month (April, May, October, November) load for the same hour of day.
  - On the 2030 profile it adds up to only 1.60 TWh, against a 4.08 TWh saving. So **39%** of the saving sits on cooling and 61% is cut uniformly (`cooling_share` in `summary.csv`).
  - Question it answers: is a MWh saved at a summer afternoon peak worth more than an average MWh?

### Flexibility in plain words (spec D5, §5.3)

[`src/tn2030/flexibility.py`](../../src/tn2030/flexibility.py)

- Shiftable load works like a free, lossless battery at each bus, split by each bus's share of demand. It starts every day **half full**.
  - **Above half full:** consumers used power *earlier* than planned (load went up), and they use less later.
  - **Below half full:** consumers *postponed* use (load went down), and the load comes back later.
- **Power cap:** 300 MW (S2-300) or 600 MW (S2-600).
- **Energy cap:** up to power × 3 h can be moved in each direction.
- **3-hour limit:** every MWh moved must come back within **3 hours**. The energy owed at any hour cannot exceed what was moved during the last 3 hours.
- **One direction at a time:** in each hour, load shifted up plus load shifted down is at most the cap. Without this, charging and discharging at once (free, lossless) would refresh the 3-hour window.
- **Back to half full at the end of every day:** no energy is saved, it only moves.
- Batteries can be built in every scenario, so S2 measures what shifting adds *on top of* batteries.
- **What the model does with it** (S2-300, average by hour): it cuts load in the early morning (05:00–08:00 UTC) and the evening (16:00–20:00 UTC) and moves it into the midday solar hours (09:00–14:00 UTC). About 1.07 TWh of load is moved per year.

### Constraints added to the least-cost problem

[`src/tn2030/constraints.py`](../../src/tn2030/constraints.py)

- **Renewable target (spec D12):**
  - Over the year, solar + onshore wind + hydro output ≥ 35% of all domestic generation.
  - Batteries and shifted load are on neither side, and imports are outside the model.
  - If no carrier name matches, the code raises an error rather than silently enforcing nothing.
- **Reserve margin (author's decision, 2026-10-28):**
  - Firm capacity (gas + hydro) ≥ 1.10 × the scenario's peak load. 10% is the lower end of STEG's planning target of 10–15% of peak (JICA 2022, p.5-33; register row `reserve_margin`).
  - Wind, solar, batteries and shifted load get no firm credit, and the peak is taken before any shifting. Flexibility therefore earns no capacity value here (conservative).
- **Battery sizing:** PyPSA-Earth puts the whole inverter cost on the battery charger, so the charger must equal efficiency × discharger, as in PyPSA-Earth's own `solve_network.py` (line 514). Without it, discharge power would be free.

### Checks after every solve

[`src/tn2030/checks.py`](../../src/tn2030/checks.py). The pipeline stops if any of these fails:
- the whole-system energy balance closes (relative gap ≤ 1e-4);
- the renewable share is ≥ 35%;
- no load is shed;
- every generator keeps its floor (existing + committed), and every committed project is built;
- the reserve margin is met.

The peak is compared with STEG's 6,000 MW 2030 forecast, on the same domestic basis (minus the flat imports, giving 5,645 MW). This is a warning only.

## Run

| Item | Value |
|---|---|
| Date | 2026-10-28, 16:43 → 17:39 (56 min for all 24 jobs, `snakemake -j 1`) |
| Solve time per scenario | 3.7–5.1 min, 7.5–8.3 min with shiftable load (HiGHS, 8,760 hourly steps, 2 buses) |
| Sanity checks | **all 11 passed** |
| Warnings | Peak more than 10% below 5,645 MW in the 8 scenarios with an efficiency cut. Expected: the forecast assumes no extra efficiency. S0 (5,566 MW) and the two G-…-S0 runs are within 10%. |

Checked by hand on the solved networks:
- S0 firm capacity is exactly 1.100 × peak, so the reserve binds.
- In S2-300 the 3-hour limit and the one-direction cap hold to within 1e-9, and every day ends back at neutral.
- In G-hi-S0 each battery charger is 0.98 × its discharger.

## Results

All figures are from `results/summary.csv` and `results/avoided.csv`. They describe a least-cost 2030 system: capacity built where it is the cheapest way to meet demand, the 35% target and the 10% reserve, with 2030 technology-data costs.

### Main scenarios

| | S0 | S1-10 | S1-15 | S1-20 | S1-15C | S2-300 | S2-600 |
|---|---|---|---|---|---|---|---|
| Domestic demand (TWh) | 24.08 | 21.36 | 20.00 | 18.64 | 20.00 | 20.00 | 20.00 |
| Peak (MW) | 5,566 | 4,974 | 4,678 | 4,381 | 3,881 | 4,678 | 4,678 |
| New gas turbines (MW) | 423 | 0 | 0 | 0 | 0 | 0 | 0 |
| New solar (MW) | 3,929 | 3,237 | 2,928 | 2,606 | 2,802 | 3,453 | 3,948 |
| New onshore wind (MW) | 2,121 | 1,857 | 1,714 | 1,574 | 1,853 | 1,629 | 1,485 |
| New batteries (MW) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Gas burnt (TWh_th) | 21.55 | 19.09 | 17.83 | 16.60 | 17.09 | 16.63 | 15.89 |
| CO2 (Mt) | 4.27 | 3.78 | 3.53 | 3.29 | 3.38 | 3.29 | 3.15 |
| Renewable share | 56% | 56% | 56% | 56% | 57% | 58% | 60% |
| System cost (M EUR/yr) | 1,327 | 1,157 | 1,084 | 1,012 | 1,073 | 1,062 | 1,045 |
| Average price (EUR/MWh) | 54.7 | 54.2 | 53.5 | 52.8 | 53.1 | 52.5 | 51.9 |

### Headline: what one MWh saved avoids (vs S0)

| | Cost (EUR/MWh) | CO2 (t/MWh) | Gas (MWh_th/MWh) | New capacity (MW per TWh/yr) |
|---|---|---|---|---|
| S1-10 | 62.6 | 0.18 | 0.90 | 507 |
| S1-15 | 59.6 | 0.18 | 0.91 | 449 |
| S1-20 | 58.0 | 0.18 | 0.91 | 422 |
| S1-15C (cooling) | 62.4 | 0.22 | 1.09 | 446 |
| S2-300 (efficiency + flexibility) | 65.0 | 0.24 | 1.21 | 341 |
| S2-600 (efficiency + flexibility) | 69.2 | 0.28 | 1.39 | 255 |

### Extra value of targeting and flexibility

These are differences against S1-15, which has the same annual saving. They are computed from `summary.csv`.

| vs S1-15 | System cost (M EUR/yr) | Gas (TWh_th) | CO2 (Mt) | New capacity (MW) |
|---|---|---|---|---|
| S1-15C: 39% of the saving on cooling | −11.5 | −0.74 | −0.15 | +13 |
| S2-300: + 300 MW shiftable load | −22.1 | −1.20 | −0.24 | +440 (525 more solar, 85 less wind) |
| S2-600: + 600 MW shiftable load | −39.2 | −1.94 | −0.38 | +791 (1,020 more solar, 229 less wind) |

300 MW of shifting is worth about 74,000 EUR per MW per year (22.1 M EUR / 300 MW). 600 MW gives about 65,000 EUR per MW, so each extra MW is worth a little less.

### Gas-price sensitivity (S1-15 against its own-price reference)

| | Gas ×0.5 | Base | Gas ×1.5 |
|---|---|---|---|
| Avoided cost (EUR/MWh) | 43.0 | 59.6 | 70.1 |
| Avoided CO2 (t/MWh) | 0.28 | 0.18 | 0.11 |
| Avoided gas (MWh_th/MWh) | 1.42 | 0.91 | 0.54 |
| Renewable share (reference run) | 35% (binding) | 56% | 70% |
| New gas in the reference run (MW) | 423 OCGT | 423 OCGT | 131 CCGT + 292 OCGT |
| Batteries in the reference run | 0 | 0 | 628 MW / 3,148 MWh (5 h) |

### What the results say

1. **The 35% target does not bind at the base gas price.** With 2030 technology-data costs and gas at 28.4 EUR/MWh_th, new solar and wind are cheaper than running the existing gas fleet. The least-cost system reaches 56% renewables on its own. Only with gas at half price does the 35% constraint bind.
2. **Efficiency avoids new gas plant, and quickly.**
   - With STEG's 10% reserve, S0 needs 423 MW of new gas turbines on top of the existing 5,644 MW.
   - A 10% saving already lowers the peak enough (4,974 MW) that no new gas plant is needed.
   - So the 423 MW is avoided by every efficiency scenario. Beyond that point, further savings avoid only solar and wind.
3. **One MWh saved avoids about 60 EUR of system cost** (S1-15). That is the average power price (55 EUR/MWh) plus the avoided gas turbines.
   - The value per MWh is highest for the first 10% saved (62.6 EUR), which carries all of the avoided gas capacity.
   - Each MWh saved also avoids about 0.9 MWh of gas and 0.18 t of CO2.
   - Of the generation that is no longer needed, **43% is gas and 57% is renewables** that would otherwise have been built (S1-15 vs S0).
4. **Where the saving happens matters, even when only part of it can be targeted.**
   - In S1-15C only 39% of the saving fits on the cooling load; the rest is uniform.
   - That is enough to avoid 20% more gas and CO2 per MWh than a fully uniform cut, and 11.5 M EUR/yr more.
   - The air-conditioning hours are when gas runs.
5. **Flexibility adds a lot on top of efficiency.** 300 MW of load moved by at most 3 hours saves another 22 M EUR/yr and 0.24 Mt CO2.
   - It moves morning and evening load into midday solar hours, so the model builds about 525 MW more solar (and 85 MW less wind) and burns less gas.
   - This value is all energy: under the reserve rule, flexibility gets no credit for lowering the peak. No batteries are built at the base gas price, so shifting is not competing with them here.
6. **The gas price changes the story more than any efficiency choice does.**
   - With cheap gas, efficiency mainly avoids gas: 0.28 t CO2 per MWh.
   - With expensive gas, the system is already 70% renewable with 5-hour batteries. Efficiency then mainly avoids renewables, batteries and some gas capacity: 0.11 t CO2 per MWh, but 70 EUR/MWh.

### Caveats before using these numbers

- **No limit on renewable build-out:** the model builds renewables at technology-data costs with no limits on yearly build rate, financing or grid integration beyond the 2-bus network. 6 GW of new wind and solar by 2030 is far above Tunisia's recent pace (about 1 GW of committed projects). The results read as "what least cost would do", not as a forecast.
- **The efficiency factor for existing gas units** also stands in for outages (Phase 3, gap 2). It lands mostly on combined-cycle plants. With outages modelled, peaking units would run more and avoided gas per MWh would probably be higher. Recorded as a limitation (author's decision, 2026-10-28); no sensitivity run.
- **Reserve:**
  - It is a single national constraint on capacity, not a reliability simulation.
  - Firm capacity counts the full hydro (49 MW), although its yearly inflow is small.
  - Using 15% instead of 10% would raise the gas capacity S0 needs and the value of efficiency.
- **System cost:** it includes the annualised cost of existing and committed wind and solar, the existing line, and the small fixed run-of-river plant. Differences between scenarios are correct; absolute values are not the cost of the real system. Line expansion is not in "new capacity".
- **Average price** is weighted by the planned load before shifting, which is slightly off for S2.
- **Peak hour:** the model's demand peaks about 2–3 hours later than in reality (Phase 3). This affects how much load can be shifted into solar hours.
