# Phase 3: Baseline validation and calibration

**Question:** does the PyPSA-Earth Tunisia network reproduce 2024 reality well enough to study 2030?

**Method:** compare it with the official 2024 statistics, explain every gap above 10%, and calibrate what matters. Calibrations go into code with tests (`src/tn2030/fleet.py`, `src/tn2030/demand.py`) and into the assumptions register, never as hand edits to the network.

**Script:** [`scripts/validate_baseline.py`](../scripts/validate_baseline.py) (about 40 s, three HiGHS solves).
**Output:** [`results/validation.csv`](../results/validation.csv).
**References:**
- ONEM *Memento du secteur de l'énergie, Chiffres de 2024* for 2024 capacity, generation, peak and fuel use.
- STEG's forecast in the JICA 2022 survey for the minimum/peak ratio.

All values, with page numbers, are in `data/assumptions_register.xlsx`.

## How the check works

1. **Capacity:** existing MW by type in the base network vs ONEM 2024.
2. **Dispatch-only year:**
   - Freeze every capacity (nothing can be built).
   - Set the load to 2024 total demand (22.51 TWh), minus a flat import flow (3.11 TWh).
   - Let HiGHS dispatch the fleet at least cost for the 8,760 hours of the weather year.
   - Unserved load is allowed at 100,000 EUR/MWh, so a shortage shows up as a number instead of an infeasible model. It stayed at zero in both cases.
3. **Compare:** generation by fuel, gas share, gas fleet efficiency and the demand shape against 2024 statistics.

## Results

| Metric | PyPSA-Earth as built | Calibrated | 2024 official | Source |
|---|---|---|---|---|
| Combined cycle (MW) | 5,580 | 2,527 | 2,527 | ONEM |
| Gas turbines + steam (MW) | 0 | 3,117 | 3,117 (2,457 + 660) | ONEM |
| Oil (MW) | 1,409 | 0 | none listed | ONEM |
| **Thermal total (MW)** | **6,989 (+24%)** | **5,644** | **5,644** | ONEM |
| Gas generation (TWh) | 18.15 | 18.15 | 18.16 | ONEM |
| Gas share of generation | 93.6% | 93.6% | 94.5% | ONEM |
| **Gas fleet efficiency (net CV)** | **58.0% (+18%)** | **49.0%** | **49.0%** | ONEM: 194.8 toe(gross)/GWh, net = 0.9 × gross |
| **Peak demand, 2024 (MW)** | **3,480 (−29%)** | **4,901** | **4,888** | ONEM |
| **Load factor** | **0.738** | **0.524** | **0.524** | ONEM: 22.507 TWh / 8,784 h / 4,888 MW |
| Minimum / peak | 0.525 | 0.340 | 0.34 (2030 forecast) | STEG via JICA |
| Wind generation (TWh) | 0.48 | 0.48 | 0.34 | ONEM |
| Solar generation (TWh) | 0.75 | 0.75 | 0.63 | ONEM |
| Hydro generation (TWh) | 0.009 | 0.009 | 0.016 | ONEM |
| Oil generation (TWh) | 0 | 0 | 0.072 | ONEM |
| Unserved load (TWh) | 0 | 0 | 0 | – |

Gas generation matches in both cases by construction: demand and imports are fixed, renewables take what the weather gives, and gas covers the rest. The useful tests are the ones it does not set directly: capacity, efficiency (that is, gas burnt) and the shape of demand.

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
  - Their capital cost is set to 0, because existing plant is a sunk cost. This also removes the "existing capacity is costed" issue found in Phase 2.
- **Oil** generators are removed.
- **New-build candidates:** PyPSA-Earth's old extendable CCGT generators stay, starting from 0 MW.
- **Bus split:** each bus gets the share of both types that it had of PyPSA-Earth's existing thermal MW (75% north, 25% south). No 2024 plant-by-plant list was found, so this is a simplification.

### 2. Gas fleet efficiency too high (calibrated)

**Gap:**
- The model's gas plants convert 58% of the fuel energy into electricity, the technology-data value for a *new* combined cycle.
- STEG's measured specific consumption in 2024 was 194.8 toe (gross calorific value) per GWh. That is 1,000 / (194.8 × 11.63) = 44.1% on gross calorific value, or **49.0% on net**. ONEM gives net = 0.9 × gross for natural gas.

**Calibration:**
- One factor multiplies the technology-data efficiency of every *existing* gas unit.
- Scaling all of them by the same factor keeps their order of dispatch, so one run at factor 1 gives the answer directly: factor = 0.490 / 0.568 = **0.863**. A second run confirms 49.0%.
- Result: existing combined cycle 0.58 × 0.863 = **50.1%**; existing gas turbines and steam 0.41 × 0.863 = **35.4%**.
- New builds keep the technology-data values (58% and 41%).
- Register row: `existing_gas_efficiency_factor`.

### 3. Demand shape too flat (calibrated, risk R5)

**Gap:**
- Scaled to 2024 demand, PyPSA-Earth's hourly profile peaks at only 3,480 MW, against the real 4,888 MW (14 Aug 2024).
  - Its load factor is 0.74 against 0.52.
  - Its summer days are a flat plateau from 10:00 to 18:00 UTC, and the summer peak is only about 10% above the winter one.
- PyPSA-Earth's other source, DemandCast, is just as flat for Tunisia: load factor 0.70 in 2024.
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
- Result: peak 4,901 MW against 4,888 (+0.3%). The small gap comes from the model year having 8,760 h instead of 8,784.

**What it does not fix:** the *hour* of the daily peak. PyPSA-Earth's summer peaks fall around 17:00 UTC (18:00 local). STEG's 2024 and 2025 peaks were at 15:41 local (14:41 UTC). This matters for the 3-hour load shift and its overlap with solar, so it is listed under limitations and checked again in Phase 4.

### 4. Wind and solar output higher than 2024 (explained, not calibrated)

**Wind:** the model gives 0.48 TWh against 0.34 TWh (+43%).
- The model has 283 MW of wind; IRENA lists 245 MW for 2024.
- STEG's short-term plan includes "restoring the full production capacity" of the Kchabta and Metline plants, about 190 MW (La Presse, 9 Oct 2026). So part of the wind fleet was out of service in 2024.
- The model also uses 2013 weather, not 2024.

**Solar:** the model gives 0.75 TWh against 0.63 TWh (+20%). Its 508 MW includes PyPSA-Earth's IRENA top-up, and the reference mixes centralised and rooftop output.

**Why not calibrated:** together these are about 1% of generation. In 2030 the optimizer builds several GW of new wind and solar, which dwarfs this gap. Recorded, not changed.

### 5. Small gaps (not calibrated)

- **Hydro:** 9 GWh against 16 GWh.
- **Oil:** 0 against 72 GWh.
- **Gas share:** 93.6% against 94.5%.

Each is below 0.5% of generation.

## What Phase 4 must apply

Every scenario network is built from the base network with the same three calibrations, in this order:

1. `rebuild_thermal_fleet(...)` with the ONEM capacities and `existing_gas_efficiency_factor`, as in `calibrated_fleet()` in the script.
2. `reshape_profile(...)` on the total demand profile, with load factor 0.524 and minimum/peak 0.34, **before** growing it to 2030 and before the efficiency cuts.
3. Committed projects from `data/committed_projects.csv` added as fixed capacity (spec D6).

The steam units stay in the 2030 fleet. STEG's 2022 plan to retire 660 MW is not a commitment, and ONEM still lists them in 2024 (author's decision, 2026-10-28). Their retirement can be a sensitivity case.

## Limitations

- **Plant locations:** the split of each plant type between the two buses follows PyPSA-Earth's thermal locations, not a plant list.
- **Steam modelling:** steam units are modelled with the gas-turbine efficiency curve. The fitted factor absorbs the difference at fleet level only.
- **Minimum/peak ratio:** taken from STEG's 2030 forecast, not from 2024.
- **Peak hour:** the timing comes from PyPSA-Earth's profile, about 2 to 3 hours later than the real peak.
- **One capacity chart was read by eye:** the 2024 capacity split by type comes from a chart in the ONEM Memento that has no text layer. Its combined-cycle share (42%) matches the text on the same page. The author will check the four values against printed p.17.
