# Phase 4: Scenarios and runs

**What this phase does:** one Snakemake pipeline turns the calibrated Tunisia base network into the 11 scenarios of spec §4, solves each one as a 2030 least-cost investment and dispatch problem, checks it, and writes two tables:

- [`results/summary.csv`](../results/summary.csv): one row per scenario (capacity, new capacity, generation, demand, gas, CO2, system cost, average price, renewable share).
- [`results/avoided.csv`](../results/avoided.csv): each scenario against its reference, per MWh of demand saved (the headline metric).

**To reproduce:** run `snakemake -j 1` from the repo root (the base network path is in `config/pipeline.yaml`).

## How a scenario network is built

[`src/tn2030/scenario.py`](../src/tn2030/scenario.py) `build_scenario`, in the order of spec §5.1:

1. **Calibrate the base network** (`calibrate_base`, Phase 3):
   - official 2024 thermal fleet with the fitted efficiency factor;
   - one new-build OCGT option per bus;
   - existing 2024 wind and solar kept.
2. **Demand shape:** stretch the hourly profile to the official load factor (0.524) and minimum/peak ratio (0.34).
3. **2030 demand:** scale the total to 22.507 TWh × 1.032⁶ = 27.19 TWh.
4. **Efficiency cut:** uniform, or cooling-weighted (below).
5. **Imports:** subtract the flat 2024 import flow (3.11 TWh, about 355 MW every hour). Because imports are equal in all scenarios, every MWh saved falls on domestic generation.
6. **Committed projects** (`data/committed_projects.csv`): their MW become a minimum the optimizer must build.
7. **Gas price sensitivity:** only the fuel part of gas units' marginal cost changes (×0.5 or ×1.5).
8. **Shiftable load**, for S2-300 and S2-600 only.

### Efficiency in plain words (spec §5.2)

- **Uniform (S1-10/15/20):** every hour of the year is 10, 15 or 20% lower. This is the simplest reading of "15% more efficient": the same appliances, each using less.
- **Cooling-weighted (S1-15C):** the same 15% of annual energy is saved, but first from air-conditioning load.
  - The cooling load is the summer load above the average shoulder-month (April, May, October, November) load for the same hour of day.
  - If the cooling load is smaller than the saving, the rest is cut uniformly. The share that fits on cooling is reported.
  - Question it answers: is a MWh saved at a summer afternoon peak worth more than an average MWh?

### Flexibility in plain words (spec §5.3)

- Shiftable load works like a free battery at each bus, split by each bus's share of demand.
  - "Charging" means consumers postpone use (load falls now).
  - "Discharging" means they use it later.
- **Power cap:** 300 MW (S2-300) or 600 MW (S2-600).
- **Energy cap:** power × 3 h, so load moves by at most 3 hours at full power.
- **No cost, no losses.**
- **Empty at the end of every day:** no energy is saved, it only moves within the day.
- Batteries can be built in every scenario, so S2 measures what shifting adds *on top of* batteries.

### The renewable target (spec D12)

[`src/tn2030/constraints.py`](../src/tn2030/constraints.py):
- Over the year, solar + onshore wind + hydro output ≥ 35% of all domestic generation.
- Batteries and shifted load are on neither side, and imports are outside the model.
- If no carrier name matches, the code raises an error rather than silently enforcing nothing.

### Checks after every solve

[`src/tn2030/checks.py`](../src/tn2030/checks.py). The pipeline stops if any of these fails:
- the whole-system energy balance closes (relative gap ≤ 1e-4);
- the renewable share is ≥ 35%;
- no load is shed;
- every committed project is built.

The 2030 peak is compared with STEG's 6,000 MW forecast, on the same domestic basis (minus the flat imports). This is a warning only.

## Run

| Item | Value |
|---|---|
| Date | 2026-10-28, 15:58 → 16:27 (29.5 min for all 24 jobs, `snakemake -j 1`) |
| Solve time per scenario | 1.7–3.9 min (HiGHS, 8,760 hourly steps, 2 buses) |
| Sanity checks | **all 11 passed**: energy balance, renewable share ≥ 35%, no load shed, committed projects built |
| Warnings | peak more than 10% below 5,645 MW (STEG's 6,000 MW 2030 forecast minus the flat imports) in the 8 scenarios with an efficiency cut. Expected: the forecast assumes no extra efficiency. S0 and the two G-…-S0 runs are within 10%. |

The solve time per scenario is listed in `results/networks/<scenario>_solved.nc.warnings.txt`.

## Results

All figures are from `results/summary.csv` and `results/avoided.csv`. They describe a least-cost 2030 system: capacity built where it is the cheapest way to meet demand and the 35% target, with 2030 technology-data costs.

### Main scenarios

| | S0 | S1-10 | S1-15 | S1-20 | S1-15C | S2-300 | S2-600 |
|---|---|---|---|---|---|---|---|
| Domestic demand (TWh) | 24.08 | 21.36 | 20.00 | 18.64 | 20.00 | 20.00 | 20.00 |
| New solar (MW) | 3,932 | 3,237 | 2,928 | 2,606 | 2,802 | 3,194 | 3,476 |
| New onshore wind (MW) | 2,147 | 1,857 | 1,714 | 1,574 | 1,853 | 1,695 | 1,674 |
| New gas or batteries (MW) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Gas burnt (TWh_th) | 21.57 | 19.09 | 17.83 | 16.60 | 17.09 | 17.00 | 16.24 |
| CO2 (Mt) | 4.27 | 3.78 | 3.53 | 3.29 | 3.38 | 3.37 | 3.22 |
| Renewable share | 56% | 56% | 56% | 56% | 57% | 58% | 59% |
| System cost (M EUR/yr) | 1,306 | 1,157 | 1,084 | 1,012 | 1,073 | 1,069 | 1,057 |
| Average price (EUR/MWh) | 55.2 | 54.2 | 53.5 | 52.8 | 53.1 | 52.7 | 52.0 |

### Headline: what one MWh saved avoids (vs S0)

| | Cost (EUR/MWh) | CO2 (t/MWh) | Gas (MWh_th/MWh) | New capacity (MW per TWh/yr) |
|---|---|---|---|---|
| S1-10 | 54.6 | 0.18 | 0.91 | 362 |
| S1-15 | 54.3 | 0.18 | 0.92 | 352 |
| S1-20 | 54.0 | 0.18 | 0.91 | 349 |
| S1-15C (cooling) | 57.1 | 0.22 | 1.10 | 349 |
| S2-300 (eff. + flex) | 58.0 | 0.22 | 1.12 | 292 |
| S2-600 (eff. + flex) | 61.0 | 0.26 | 1.31 | 228 |

### Extra value of targeting and flexibility

These are differences against S1-15, which has the same annual saving. They are computed from `summary.csv`.

| vs S1-15 | System cost (M EUR/yr) | Gas (TWh_th) | CO2 (Mt) | New capacity (MW) |
|---|---|---|---|---|
| S1-15C: saving placed on cooling | −11.5 | −0.74 | −0.15 | +13 |
| S2-300: + 300 MW shiftable load | −15.0 | −0.83 | −0.16 | +247 |
| S2-600: + 600 MW shiftable load | −27.3 | −1.59 | −0.31 | +508 |

The 300 MW of shifting is worth about 50,000 EUR per MW per year (15.0 M EUR / 300 MW). The 600 MW case gives about 45,000 EUR per MW, so each extra MW is worth a little less.

### Gas-price sensitivity (S1-15 against its own-price reference)

| | Gas ×0.5 | Base | Gas ×1.5 |
|---|---|---|---|
| Avoided cost (EUR/MWh) | 37.7 | 54.3 | 63.8 |
| Avoided CO2 (t/MWh) | 0.29 | 0.18 | 0.09 |
| Avoided gas (MWh_th/MWh) | 1.49 | 0.92 | 0.47 |
| Renewable share (reference run) | 35% (binding) | 56% | 71% |
| Batteries built (reference run) | 0 | 0 | 3,446 MW |

### What the results say

1. **The 35% target does not bind at the base gas price.** With 2030 technology-data costs and gas at 28.4 EUR/MWh_th, new solar and wind are cheaper than running the existing gas fleet. The least-cost system reaches 56% renewables on its own. Only with gas at half price does the 35% constraint bind.
2. **No new gas plant is needed in any scenario.** The existing 5,644 MW of thermal capacity covers the 2030 peak in every case. So the "avoided capacity" is avoided **solar and wind**, about 350 MW per TWh saved, not avoided gas plants.
3. **One MWh saved avoids about 54 EUR of system cost.** That is close to the average power price, as theory predicts for a least-cost system.
   - It also avoids about 0.9 MWh of gas and 0.18 t of CO2.
   - Only about half of each saved MWh displaces gas generation (0.92 × 0.50 efficiency ≈ 0.46). The rest displaces renewables that would otherwise have been built.
4. **Where the saving happens matters.** Placing the same saving on summer cooling (S1-15C) avoids 20% more gas and CO2 per MWh than a uniform cut. The air-conditioning hours are when gas runs.
5. **Flexibility adds value on top of efficiency.** 300 MW of shiftable load saves another 15 M EUR/yr and 0.16 Mt CO2.
   - It mostly shifts load into sunny hours: the model builds more solar.
   - No batteries are built at the base gas price, so shifting is not competing with batteries here.
6. **The gas price changes the story more than any efficiency choice does.**
   - With cheap gas, efficiency mainly avoids gas: CO2 savings rise to 0.29 t/MWh.
   - With expensive gas, the system is already 71% renewable plus batteries. Efficiency then mainly avoids renewables and batteries: 815 MW per TWh, with CO2 savings of only 0.09 t/MWh.

### Caveats before using these numbers

- **The model builds renewables at technology-data costs with no limits** on yearly build rate, financing or grid integration beyond the 2-bus network. 6 GW of new wind and solar by 2030 is far above Tunisia's recent pace (about 1 GW of committed projects). The result reads as "what least cost would do", not as a forecast.
- **The efficiency factor for existing gas units** also stands in for outages (Phase 3, gap 2). With more realistic availability, peaking units would run more and avoided gas per MWh would be higher.
- **System cost includes the annualised cost of existing wind, solar and lines.** Differences between scenarios are correct; absolute values are not the cost of the real system.
- **Peak hour:** the model's demand peaks about 2–3 hours later than in reality (Phase 3). This affects the value of shifting load into solar hours.
