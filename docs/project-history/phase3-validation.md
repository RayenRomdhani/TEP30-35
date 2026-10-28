# Phase 3: Baseline validation and calibration

**Question:** does the PyPSA-Earth Tunisia network reproduce 2024 reality well enough to study 2030?

**Method:** compare it with the official 2024 statistics, explain every gap above 10%, and calibrate what matters. Calibrations go into code with tests (`src/tn2030/fleet.py`, `src/tn2030/demand.py`) and into the assumptions register, never as hand edits to the network.

**Script:** [`scripts/validate_baseline.py`](../../scripts/validate_baseline.py) (about 40 s, three HiGHS solves).
**Output:** [`results/validation.csv`](../../results/validation.csv).
**References:**
- ONEM *Memento du secteur de l'énergie, Chiffres de 2024* for 2024 capacity, generation, peak and fuel.
- STEG's forecast in the JICA 2022 survey for the minimum/peak ratio.

All values, with page numbers, are in `data/assumptions_register.xlsx`.

## How the check works

1. **Capacity:** 2024 MW by type in the base network vs ONEM 2024.
2. **Dispatch-only year:**
   - Freeze every capacity, so nothing can be built. Extendable units keep `p_nom`, PyPSA-Earth's 2024 estimate.
   - Set the load to 2024 total demand (22.51 TWh), minus a flat import flow (3.11 TWh).
   - Let HiGHS dispatch the fleet at least cost for the 8,760 hours of the weather year.
   - Unserved load is allowed at 100,000 EUR/MWh, so a shortage shows up as a number instead of an infeasible model. It stayed at zero in both cases.
3. **Compare:** generation by fuel, gas burnt, gas fleet efficiency and the demand shape against 2024 statistics.

## Results

| Metric | PyPSA-Earth as built | Calibrated | 2024 official | Source |
|---|---|---|---|---|
| Combined cycle (MW) | 5,580 | 2,527 | 2,527 | ONEM |
| Gas turbines + steam (MW) | 0 | 3,117 | 3,117 (2,457 + 660) | ONEM |
| Oil (MW) | 1,409 | 0 | none listed | ONEM |
| **Thermal total (MW)** | **6,989 (+24%)** | **5,644** | **5,644** | ONEM |
| Renewables, centralised (MW) | 846 | 846 | 368 | ONEM |
| Renewables incl. self-generation solar (MW) | 846 | 846 | 808 (368 + 315 + 125) | ONEM |
| Gas generation (TWh) | 18.15 | 18.15 | 18.16 | ONEM |
| Gas share of generation | 93.6% | 93.6% | 94.5% | ONEM |
| **Gas fleet efficiency (net CV)** | **58.0% (+18%)** | **49.0%** | **49.0%** | ONEM: 194.8 toe(gross)/GWh, net = 0.9 × gross |
| **Gas burnt for power (TWh_th, net)** | **31.3 (−15%)** | **37.0 (+0.4%)** | **36.8** | ONEM: 3,168 ktep (net) |
| Generation split: CCGT / OCGT + steam (TWh) | 18.15 / 0 | 17.23 / 0.92 | not published | – |
| **Peak demand, 2024 (MW)** | **3,480 (−29%)** | **4,901** | **4,888** | ONEM |
| **Load factor** | **0.738** | **0.524** | **0.524** | ONEM: 22.507 TWh / 8,784 h / 4,888 MW |
| Minimum / peak | 0.525 | 0.340 | 0.34 (2030 forecast) | STEG via JICA |
| Wind generation (TWh) | 0.48 | 0.48 | 0.34 | ONEM |
| Solar generation (TWh) | 0.75 | 0.75 | 0.63 | ONEM |
| Hydro generation (TWh) | 0.009 | 0.009 | 0.016 | ONEM |
| Oil generation (TWh) | 0 | 0 | 0.072 | ONEM |
| Unserved load (TWh) | 0 | 0 | 0 | – |

### Why gas generation matches

Gas is the residual in this run. Demand and imports are fixed, renewables take what the weather gives, and gas covers the rest. Its close match with ONEM (18.15 vs 18.16 TWh) is partly offsetting errors:

- The model's wind and solar are 0.27 TWh too high.
- That roughly cancels what it lacks: 0.07 TWh of oil generation and the 0.19 TWh ONEM books as third-party purchases.
- The 0.19 TWh is also why the model's gas share (93.6%) is below ONEM's (94.5%): the model counts it in total generation, ONEM does not.

So gas generation is not evidence by itself. The independent tests are capacity, gas burnt and the demand shape.

## Gaps and what was done

### 1. Thermal fleet: wrong types, phantom oil (calibrated)

**Gap:**
- PyPSA-Earth labels all 5,580 MW of gas plant as combined cycle.
- It adds 1,409 MW of "oil" that does not appear in the official figures. Fuel oil and gasoil produced only 72 GWh in 2024.
- Officially, Tunisia has 2,527 MW combined cycle, 2,457 MW gas turbines and 660 MW steam turbines.

**Why it matters:**
- Gas turbines and steam units burn much more gas per MWh than combined cycle.
- A fleet that is all combined cycle under-states gas use and CO2.
- The extra 1.3 GW would hide how much new capacity 2030 needs, which is exactly what efficiency is supposed to avoid.

**Calibration** (`tn2030.fleet.rebuild_thermal_fleet`, tested in `tests/test_fleet.py`):
- **Existing units** become fixed generators with the ONEM capacities.
  - Steam is grouped with the gas turbines as one `OCGT` group: both are simple-cycle plants with low efficiency, and technology-data has no gas steam-turbine row.
  - Their capital cost is 0, because existing plant is a sunk cost. This removes the "existing capacity is costed" issue from Phase 2 for thermal plants. Existing wind and solar (`p_nom_min`) and the existing line are still costed. That cancels in differences between scenarios but not in absolute system cost.
- **Oil** generators are removed.
- **New-build options:**
  - **CCGT:** PyPSA-Earth's old extendable CCGT generators stay, starting from 0 MW.
  - **OCGT:** PyPSA-Earth added no OCGT option, because none existed under that label (Phase 2 finding). `tn2030.fleet.add_ocgt_candidates` adds one per bus. Its costs are technology-data rows in the register (`ocgt_investment`, `ocgt_fom`, `ocgt_lifetime`), and Phase 4 applies it (spec D1).
- **Bus split:** each bus gets the share of both types that it had of PyPSA-Earth's existing gas MW: **73% north, 27% south** ("oil" ignored). No 2024 plant-by-plant list was found, so this is a simplification.

### 2. Gas fleet efficiency too high (calibrated)

**Gap:**
- The model's gas plants convert 58% of the fuel energy into electricity, the technology-data value for a *new* combined cycle.
- STEG's measured specific consumption in 2024 was 194.8 toe (gross calorific value) per GWh. That is 1,000 / (194.8 × 11.63) = 44.1% on gross calorific value, or **49.0% on net**. ONEM gives net = 0.9 × gross for natural gas.

**Cross-check:**
- ONEM also reports the gas burnt for electricity in 2024: 3,168 ktep on net calorific value = 36.8 TWh_th.
- 18.16 TWh / 36.8 TWh = **49.3%**, which agrees with the 49.0% above.
- PyPSA-Earth as built burns only 31.3 TWh_th (−15%).

**Calibration:**
- One factor multiplies the technology-data efficiency of every *existing* gas unit.
- Scaling all of them by the same factor keeps their order of dispatch: combined cycle stays cheaper on both fuel and variable O&M. So one run at factor 1 gives the answer directly: factor = 0.490 / 0.568 = **0.863**.
- A second run confirms 49.0%. Gas burnt then comes to 37.0 TWh_th, +0.4% against ONEM. That figure was not used in the fit.
- Result: existing combined cycle 0.58 × 0.863 = **50.1%**; existing gas turbines and steam 0.41 × 0.863 = **35.4%**.
- New builds keep the technology-data values (58% and 41%).
- Register row: `existing_gas_efficiency_factor`. It is typed as an assumption, because it is a calibration and not a published figure. The script warns if a new fit differs from the register value.

**Caveat (important for Phase 4):**
- The model has no outages or maintenance, so existing combined cycle runs almost as baseload: 17.2 of 18.15 TWh. The gas turbines and steam units run at capacity factors of only a few percent.
- The single factor therefore also absorbs unmodelled outages and part-load running. It lands mostly on the combined-cycle plants (50.1%).
- In reality, the plant at the margin is probably a gas turbine or steam unit more often than the model says. The marginal unit sets the avoided gas and CO2 per MWh saved.
- Phase 4 adds a sensitivity, for example the factor applied to the gas-turbine/steam group only, decided with the author.

### 3. Demand shape too flat (calibrated, risk R5)

**Gap:**
- Scaled to 2024 demand, PyPSA-Earth's hourly profile peaks at only 3,480 MW, against the real 4,888 MW (14 Aug 2024).
  - Its load factor is 0.74 against 0.52.
  - Its summer days are a flat plateau from 10:00 to 18:00 UTC, and the summer peak is only about 10% above the winter one.
- PyPSA-Earth's other source, DemandCast, is just as flat for Tunisia: load factor 0.70 in 2024. This was computed from the DemandCast file in PyPSA-Earth's data bundle, `data/demand/forecasts_on_historical_period.parquet`.
- Tunisia's real peak is driven by summer air conditioning.

**Why it matters:**
- A 29% low peak would hide most of the capacity that efficiency can avoid.
- A weak summer peak would make the cooling-weighted scenario (S1-15C) meaningless.

**Calibration** (`tn2030.demand.reshape_profile`, tested in `tests/test_demand.py`):
- Each hour keeps its rank from the PyPSA-Earth profile, so the weather-driven timing of hot and cold days is kept.
- The values are stretched with one exponent `k` so that three things match:
  - annual energy (unchanged);
  - minimum/peak = 0.34 (STEG's 2030 forecast; no 2024 value was found);
  - load factor = 0.524 (2024 demand ÷ 8,784 h ÷ the 2024 peak).
- The function refuses a constant profile and checks that the target was reached.
- Result: peak 4,901 MW against 4,888 (+0.3%). The small gap comes from the model year having 8,760 h instead of 8,784.

**What it does not fix:** the *hour* of the daily peak. PyPSA-Earth's summer peaks fall around 17:00 UTC (18:00 local). STEG's 2024 and 2025 peaks were at 15:41 local (14:41 UTC; STEG "Produire" page). This matters for the 3-hour load shift and its overlap with solar, so it is listed under limitations and checked again in Phase 4.

### 4. Renewable capacity and output (explained, not calibrated)

**Capacity:** the model has 846 MW of renewables against ONEM's 368 MW (+130%). The two count different things:
- ONEM's 368 MW covers the centralised fleet only.
- PyPSA-Earth's solar (508 MW) is topped up to IRENA's 2024 total, which includes rooftop and other self-generation.
- ONEM lists 315 MW of low-voltage self-generation solar and 125 MW authorised at medium/high voltage. Adding these gives 808 MW, and the gap shrinks to **+4.7%**.
- Rule for Phase 4: existing solar and wind are kept at this 2024 level (`p_nom`), the same level the validation run used.

**Wind output:** the model gives 0.48 TWh against 0.34 TWh (+43%).
- The model has 283 MW of wind. IRENA's Tunisia statistical profile lists 245 MW for 2024.
- STEG's short-term plan includes restoring the full production capacity of its Kchabta and Metline plants, about 190 MW (La Presse, 9 Oct 2026). That suggests part of the wind fleet was not producing at full capacity in 2024; the article does not say how much.
- The model also uses 2013 weather, not 2024.

**Solar output:** the model gives 0.75 TWh against 0.63 TWh (+20%), for the capacity reasons above.

**Why not calibrated:** together these are about 1% of generation. In 2030 the optimizer builds several GW of new wind and solar, which dwarfs this gap.

### 5. Small gaps (not calibrated)

- **Hydro:** 9 GWh against 16 GWh.
- **Oil:** 0 against 72 GWh.

Each is below 0.5% of generation.

## What Phase 4 must apply

Every scenario network is built from the base network with these calibrations. The order and interfaces are in plan Task 15 (`calibrate_base`, then `build_scenario`):

1. `rebuild_thermal_fleet(...)` with the ONEM capacities and `existing_gas_efficiency_factor`, as in `calibrated_fleet()` in the script.
2. `add_ocgt_candidates(...)`, with the OCGT new-build costs from the register.
3. Existing solar and wind floor `p_nom_min = p_nom`.
4. `reshape_profile(...)` on the total demand profile, with load factor 0.524 and minimum/peak 0.34, **before** growing it to 2030 and before the efficiency cuts.
5. Committed projects from `data/committed_projects.csv` added as fixed capacity (spec D6).

The steam units stay in the 2030 fleet. STEG's 2022 plan to retire 660 MW is not a commitment, and ONEM still lists them in 2024 (author's decision, 2026-10-28). Their retirement can be a sensitivity case.

## Limitations

- **Plant locations:** the split of each plant type between the two buses follows PyPSA-Earth's gas locations, not a plant list.
- **Steam modelling:** steam units are modelled with the gas-turbine efficiency. The fitted factor matches the fleet as a whole, not each type.
- **The efficiency factor also stands in for outages and part-load running:** see gap 2. It lands mostly on combined cycle.
- **Minimum/peak ratio:** taken from STEG's 2030 forecast, not from 2024.
- **Peak hour:** the timing comes from PyPSA-Earth's profile, about 2 to 3 hours later than the real peak.
- **One capacity chart was read by eye:** the 2024 capacity split by type comes from a chart in the ONEM Memento that has no text layer. Its combined-cycle share (42%) matches the text on the same page. The author will check the four values against printed p.17.
