# results/

Everything the pipeline produces. The solved networks themselves (`networks/*.nc`, about 3 MB each) are not stored in the repository; rerun the pipeline to recreate them.

| File | What it is |
|---|---|
| [`summary.csv`](summary.csv) | One row per scenario: capacity and new capacity by technology (MW), generation (TWh), demand, gas burnt, CO2, renewable share, system cost, average price |
| [`avoided.csv`](avoided.csv) | Each scenario against its reference: avoided cost, CO2, gas and capacity per MWh saved (the headline metric) |
| [`validation.csv`](validation.csv) | The 2024 check: model against official statistics, before and after calibration |
| [`figures/`](figures/) | The charts, drawn by `scripts/make_figures.py` from the files above (`0_headline.png` is the README's opening picture; `phase1_toy_dispatch.png` is from the first toy model) |
| `networks/*_solved.nc.warnings.txt` | Per-scenario solve time and any check warnings (for example the 2030 peak against STEG's forecast) |

Units: MW for capacity, TWh for energy, TWh_th for gas (energy in the fuel), Mt for CO2, M EUR per year for cost.
