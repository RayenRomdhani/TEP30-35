# The value of energy efficiency in Tunisia's power system (2030)

How much gas, CO2, system cost and new capacity does Tunisia avoid in 2030 for each MWh of electricity it does not use? This study answers that question with an open capacity-expansion model built on [PyPSA-Earth](https://github.com/pypsa-meets-earth/pypsa-earth). It keeps the government's 35% renewable target in place throughout.

Author: Rayen Romdhani, Energy Engineering student, ENIM (Monastir, Tunisia).

## Headline result

Saving 15% of 2030 electricity demand in every hour (scenario S1-15, against the base case S0) avoids, per MWh saved:

| System cost | Gas burnt | CO2 | New capacity |
|---|---|---|---|
| 60 EUR | 0.91 MWh of gas | 0.18 t | 449 MW per TWh saved per year |

![What each MWh saved avoids](results/figures/8_avoided_per_mwh.png)

What the scenarios show:

- With STEG's 10% reserve margin, the base case needs 423 MW of new gas turbines. A 10% saving already avoids all of them.
- Timing matters. If the same 15% comes first out of summer air conditioning (S1-15C), each MWh saved avoids 20% more gas and CO2, although only 39% of the saving fits on the cooling load.
- Flexibility adds to efficiency. Letting 300 MW of load move by up to 3 hours (S2-300) saves another 22 M EUR per year and 0.24 Mt of CO2. The model moves morning and evening load into the midday solar hours.
- The gas price changes the result more than any efficiency choice. At half the gas price, each MWh saved avoids 0.28 t of CO2. At 1.5 times the price it avoids only 0.11 t, because the system is already 70% renewable.
- At the base gas price the 35% target does not bind: the least-cost 2030 system reaches 56% renewables on its own. That is the least-cost outcome and should not be read as a forecast (see Limitations).

The full tables are in [`results/summary.csv`](results/summary.csv) and [`results/avoided.csv`](results/avoided.csv). The method and every result are explained in [`docs/phase4-scenarios.md`](docs/phase4-scenarios.md).

## Question and scope

The study asks what each MWh of electricity saved through efficiency, or moved in time through demand flexibility, avoids in 2030 in capacity, gas, system cost and CO2. It is anchored on Tunisia's target of 35% renewable electricity by 2030 (register row `re_target_2030`).

The model covers Tunisia only, with 2 network nodes (north and south), 8,760 hourly steps and one weather year (2013). It is solved with the open-source solver HiGHS. It leaves out the cost of efficiency programmes (the study values the saving only), the electricity link to Italy (ELMED) and other countries.

## Method

1. PyPSA-Earth v0.10.0, unmodified, builds the base network: Tunisia's grid, power plants, renewable potentials and hourly demand, from open data. The settings are in [`config/tn_base.yaml`](config/tn_base.yaml) and are logged in [`docs/config-changes.md`](docs/config-changes.md).
2. The network is calibrated to 2024 ([`docs/phase3-validation.md`](docs/phase3-validation.md)). The thermal fleet is rebuilt from the official 2024 statistics (ONEM Memento 2024). One efficiency factor for existing gas units is then fitted so that the model burns as much gas as STEG did. After calibration the 2024 model matches the official gas burnt within 0.4% and the peak within 0.3%.
3. 2024 demand (22.5 TWh) grows to 2030 at 3.2% per year, STEG's base-case forecast as quoted by JICA (2022). The hourly shape is stretched to STEG's load factor and minimum-to-peak ratio. Imports stay at their 2024 level.
4. Each scenario changes the 2030 demand or the gas price (table below). The model then builds new solar, wind, batteries and gas turbines at least cost. In every scenario it must:
   - produce at least 35% of domestic generation from renewables;
   - keep firm capacity at least 10% above peak demand (STEG's planning margin);
   - build the committed projects listed in [`data/committed_projects.csv`](data/committed_projects.csv).
5. After each solve the pipeline checks the energy balance, the renewable share, the reserve margin, that no load is shed, and that committed and existing capacity is kept. It stops if any check fails. All 11 scenarios pass.

| Scenario | What changes against S0 |
|---|---|
| S0 | Base case: 2030 demand, base gas price |
| S1-10, S1-15, S1-20 | Demand 10, 15 or 20% lower in every hour |
| S1-15C | Same 15% of annual energy, taken first from summer cooling load |
| S2-300, S2-600 | S1-15 plus 300 or 600 MW of load that can move by up to 3 hours |
| G-lo-S0, G-lo-S1-15 | S0 and S1-15 with the gas price halved |
| G-hi-S0, G-hi-S1-15 | S0 and S1-15 with the gas price 1.5 times higher |

Each scenario is compared with the reference at its own gas price, so "per MWh saved" always compares like with like.

## Assumptions and data

Every input number is a row in [`data/assumptions_register.xlsx`](data/assumptions_register.xlsx) with its unit, source and source link. A number with no published source is labelled `assumption` and explained in the notes. The main sources are:

| Input | Value | Source |
|---|---|---|
| Renewable target 2030 | 35% | TAP news agency, 9 Oct 2026 |
| Electricity demand 2024 | 22.5 TWh | ONEM, *Memento du secteur de l'énergie, chiffres de 2024* |
| Demand growth | 3.2% per year | STEG forecast, quoted by JICA (2022) |
| Gas fleet 2024 | 2,527 MW combined cycle, 3,117 MW gas turbines and steam | ONEM Memento 2024 |
| Reserve margin | 10% of peak | STEG planning target, quoted by JICA (2022) |
| Gas price | 28.4 EUR/MWh (thermal) | PyPSA technology-data v0.15.0 (World Bank, ENTSO-E/ENTSOG) |
| Technology costs and efficiencies | 2030 values | PyPSA technology-data v0.15.0 (Danish Energy Agency) |
| Shiftable load | 300 MW | Peak-demand reduction target of the government action plan (TAP, 9 Oct 2026) |
| Shiftable load, high case; shift window; gas price ±50% | 600 MW; 3 h; ×0.5 and ×1.5 | Assumptions |

Downloaded source documents are listed in `data/raw/SOURCES.md`. They are not stored in the repository.

## Figures

All figures are in [`results/figures/`](results/figures/) and are made by [`scripts/make_figures.py`](scripts/make_figures.py) from the result files.

| | |
|---|---|
| Installed capacity by scenario | [`1_capacity_mix.png`](results/figures/1_capacity_mix.png) |
| Domestic generation by scenario | [`2_generation_mix.png`](results/figures/2_generation_mix.png) |
| Gas burnt, system cost, CO2 | [`3_gas_use.png`](results/figures/3_gas_use.png), [`4_system_cost.png`](results/figures/4_system_cost.png), [`5_co2.png`](results/figures/5_co2.png) |
| Hourly price, sorted | [`6_price_duration.png`](results/figures/6_price_duration.png) |
| Dispatch in the peak week, S0 and S2-300 | [`7_dispatch_peak_week.png`](results/figures/7_dispatch_peak_week.png) |
| What each MWh saved avoids | [`8_avoided_per_mwh.png`](results/figures/8_avoided_per_mwh.png) |
| Saving evenly or from cooling first | [`9_uniform_vs_cooling.png`](results/figures/9_uniform_vs_cooling.png) |

## Limitations

- Nothing limits how fast renewables are built. The model adds about 6 GW of solar and wind by 2030, far above Tunisia's recent pace (about 1 GW of committed projects), with no build-rate, financing or grid-integration limits beyond its 2-node grid.
- Programme costs are not modelled. The avoided cost per MWh is the most an efficiency programme could cost and still pay off for the power system.
- All runs use 1-hour steps and one weather year (2013). A 3-hour test run built 2.7% more solar and 3.9% more wind (risk R1 in the design spec).
- Demand growth and the 2030 peak come from STEG's forecast as quoted by JICA (2022), a secondary source (risk R6). Ember's figures for the gas share of generation disagree (about 85% and 95%); this study uses the official ONEM figure of 94.5% (risk R7).
- Imports are held at their 2024 level in every hour, so every MWh saved falls on domestic generation.
- The fitted efficiency factor for existing gas units also stands in for plant outages, which the model does not represent.
- The reserve margin is one national capacity rule, not a reliability study. Wind, solar, batteries and flexibility get no firm credit, so flexibility earns no capacity value here.
- System cost includes the annualised cost of plants that already exist. Differences between scenarios are meaningful, but the absolute level is not the cost of the real system.

## Repository layout

| Path | Contents |
|---|---|
| `src/tn2030/` | The study code: demand, efficiency, flexibility, constraints, scenario builder, results, checks, figures |
| `tests/` | pytest tests, mostly on a small 2-day test network |
| `Snakefile`, `config/` | Scenario pipeline and settings (`config/scenarios/*.yaml`, one file per scenario) |
| `data/` | Assumptions register and committed projects |
| `scripts/` | Base-network inspection, 2024 validation, figures |
| `results/` | Result tables, figures and solve logs (solved networks are not stored) |
| `docs/` | Design spec, plan, and one write-up per phase |

## How to reproduce

The study ran on Windows 11 (i3-1215U, 24 GB RAM). `environment.yml` pins Windows builds. Building the base network downloads about 16 GB of data, which takes about 41 GB of disk once unpacked.

1. Install [Miniforge](https://github.com/conda-forge/miniforge), then clone PyPSA-Earth at the version used here:
   ```bash
   git clone --branch v0.10.0 https://github.com/pypsa-meets-earth/pypsa-earth.git
   ```
2. Create the environment from this repository and activate it:
   ```bash
   conda env create -f environment.yml
   ```
   ```bash
   conda activate pypsa-earth
   ```
3. Install this package (from the root of this repository):
   ```bash
   pip install -e .
   ```
4. Build the Tunisia base network (from the PyPSA-Earth folder, about 6 hours the first time, mostly downloads):
   ```bash
   snakemake -j 1 networks/TN/elec_s_2_ec_lcopt_1h.nc --configfile <path-to-this-repo>/config/tn_base.yaml
   ```
   Then set `base_network` in `config/pipeline.yaml` to the path of the new file.
5. Run the tests (from this repository; tests that need the base network are skipped if it is missing):
   ```bash
   pytest
   ```
6. Run the 11 scenarios (about 1 hour), then draw the figures and write the report and slides (`report/`):
   ```bash
   snakemake -j 1
   ```
   ```bash
   python scripts/make_figures.py
   ```
   ```bash
   python scripts/make_report.py
   ```
   ```bash
   python scripts/make_deck.py
   ```

## Tests

93 tests check the study code. Most run on a 2-day network at 3-hour steps, which also catches energy sums that forget the snapshot weighting. Two integration tests run on the real Tunisia network.

Test coverage of `src/tn2030` is 98% (lines and branches together, measured with pytest-cov on 2026-10-28):

```bash
pytest --cov=tn2030 --cov-branch --cov-report=term-missing
```

The 5 lines not covered are error branches that need a failing solver or an unreachable target, and the figure-size helper used only by `scripts/make_figures.py`.
