# Environment and configuration log

Every install step and every change to PyPSA-Earth's configuration, with the reason.

## Software

| Date | Item | Version / value | Where | Why |
|---|---|---|---|---|
| 2026-10-27 | Miniforge | 26.9.4-1 (SHA-256 `8cb96eed…70585bb`, matches GitHub asset digest) | `D:\miniforge3` | conda/mamba; C: has only ~14 GB free |
| 2026-10-27 | PyPSA-Earth | `v0.10.0` (commit `37b42f4`), shallow clone, unmodified | `D:\pypsa-earth` | Latest release at project start |
| 2026-10-27 | Conda env `pypsa-earth` | from `envs/win-64.lock.yaml` (460 conda + 2 pip packages, 783 MB download) | `D:\miniforge3\envs\pypsa-earth` | Official locked Windows environment |
| 2026-10-27 | `openjdk` (conda-forge) | added to the env | same env | PyPSA-Earth needs Java; docs suggest Oracle JDK on Windows, conda-forge openjdk is open source and reproducible from `environment.yml` |
| 2026-10-27 | `pytest`, `openpyxl` | already in the lock file; conda updated pytest 8.4.1 → 9.1.1 and rebuilt openpyxl 3.1.5 | same env | Tests; reading the assumptions register |
| 2026-10-27 | Side effects of the extras install | openssl 3.5.2 → 3.6.5, certifi/ca-certificates → 2026.10.23, docutils 0.22.4 → 0.22 | same env | Pulled in by conda's solver; no modelling package (pypsa, linopy, highspy, snakemake, pandas, numpy) changed |
| 2026-10-27 | Installer tool | extras installed with `conda`, not `mamba` | base | Bitdefender quarantined `mamba.exe` and blocks the reinstalled copy; PyPSA-Earth docs give conda as the fallback |
| 2026-10-28 | `python-docx` 1.2.0, `python-pptx` 1.0.2, `pytest-cov` 7.1.0 (+ `coverage` 7.17.0, `xlsxwriter` 3.2.9) | conda-forge, 1.2 MB, approved by the author | same env | Phase 5 report, deck and coverage figure; dry run showed new packages only, nothing updated |
| 2026-10-27 | Environment repair | reinstalled `currencyconverter==0.18.9`, `googledrivedownloader==1.1.0` (pip, `--force-reinstall --no-deps`) and `snakemake-minimal=7.32.4` (bioconda) | same env | Bitdefender had removed 5 `.py` files and kept their paths blocked until a reboot; an audit of conda/pip install records against the disk now shows no missing files that matter (only gurobipy licence/DLL, unused, and two debugpy `.gitignore` files) |

Key pinned versions: Python 3.11.13, PyPSA 0.30.3, linopy 0.5.5, HiGHS (highspy) 1.11.0, Snakemake 7.32.4.

## Tutorial run (Task 5)

Command (from `D:\pypsa-earth`, PyPSA-Earth unmodified):
`snakemake -j 1 solve_all_networks --configfile config.tutorial.yaml`

| Item | Value |
|---|---|
| Date | 2026-10-27, 16:10 → 17:08 |
| Result | 27 of 27 steps done, exit 0 |
| Runtime | 58.1 min, one Snakemake job at a time (i3-1215U, 24 GB RAM) |
| Peak RAM | Not measured. Snakemake cannot collect memory on Windows (its benchmark files show `NA`); a sampler (`scripts/peak_ram.py`) was only written later, for Task 7 |
| Downloads | tutorial bundles ≈ 0.75 GB zipped (data 144 MB, cutouts 10 MB, common data 259 MB, hydrobasins 337 MB) + OpenStreetMap data |
| Disk after unzip | `data/` 4.5 GB, other folders < 0.1 GB |
| Solved network | `results/networks/elec_s_6_ec_lcopt_Co2L-4H.nc` (Nigeria + Benin, 18 buses, 36 snapshots × 243 h) |
| Objective | 3,258.9 M EUR/yr |
| Energy balance | generators 42.95 TWh + hydro storage 8.39 TWh = load 51.33 TWh (gap 0.000 TWh) |

Lesson for the Tunisia run: on-disk size is several times the download size, so plan ≥ 30 GB for the ≈ 16 GB Tunisia download (D: had 78 GB free after the tutorial). The 16 GB is from the Zenodo file sizes checked before downloading: Africa cutouts 10.0 GB, `bundle_data_earth` 6.2 GB.

## PyPSA-Earth configuration changes

All overrides live in [`config/tn_base.yaml`](../config/tn_base.yaml), passed with `--configfile`. PyPSA-Earth itself is unmodified.

| Key | Default | Ours | Why |
|---|---|---|---|
| `tutorial` | `false` (`true` only in `config.tutorial.yaml`) | `false` | Not a change: stated so the run clearly uses the full data bundles |
| `countries` | `["NG", "BJ"]` | `["TN"]` | Tunisia only (spec D11) |
| `run.name` | `""` | `"TN"` | Keeps Tunisia files apart from the tutorial run |
| `scenario.clusters` | `[10]` | `[2]` | Small, fast network (spec D11) |
| `scenario.opts` | `[Co2L-3h]` | `[1h]` | 1-hour steps (Task 7 decision, see below); no CO2 cap because Tunisia has none (spec D9) |
| `electricity.extendable_carriers.Generator` | `[solar, onwind, offwind-ac, offwind-dc, OCGT]` | `[solar, onwind, OCGT, CCGT]` | Candidate technologies of spec D1 |
| `electricity.extendable_carriers.Store` | `[battery, H2]` | `[battery]` | Li-ion only; no hydrogen (spec D1) |
| `electricity.renewable_carriers` | `[solar, onwind, offwind-ac, offwind-dc, hydro]` | `[solar, onwind, hydro]` | Offshore wind is not a candidate, so its profiles are skipped |
| `solving.solver` | `gurobi`, `gurobi-default` | `highs`, `highs-default` | Open-source solver |

Left at their defaults (checked in `config.default.yaml`): cost year 2030 with technology-data v0.15.0, discount rate 0.071, weather year 2013, load source GEGIS with prediction year 2030.

### Built-in minimum renewable share (plan Task 6, Step 2)

PyPSA-Earth v0.10.0 has an `RES` option in `opts` (`scripts/solve_network.py`, `add_RES_constraints`, lines 537–616). It is not usable here:
- It forces the renewable share to **equal** the target (`lhs == rhs`, line 616).
- It measures the share against load (line 583), not domestic generation.
- It adds battery discharge and subtracts battery charging on the renewable side (line 614), whatever charged the battery.
- The code warns it is work in progress (line 550).

Our spec needs **at least** 35% of domestic generation (D12).
**Answer: none suitable; custom constraint in Task 13.**

### Missing OCGT candidate

PyPSA-Earth adds extendable OCGT only at buses that already have a plant labelled OCGT (`scripts/add_electricity.py`, line 772). The Tunisian plant list has none, so listing OCGT in `extendable_carriers` adds the carrier but no generator. Our own code will add OCGT candidates (see `docs/phase2-base-network.md`).

## Tunisia base network run (Task 6)

Command (from `D:\pypsa-earth`):
`snakemake -j 1 networks/TN/elec_s_2_ec_lcopt_3h.nc --configfile <repo>/config/tn_base.yaml`

| Item | Value |
|---|---|
| Date | 2026-10-27, 17:12 → 23:00 |
| Result | 21 of 21 steps done, exit 0 |
| Runtime | 347.6 min, of which about 5.3 h downloads and 14 min modelling (breakdown in `docs/phase2-base-network.md`) |
| Disk after the run | `data/` 21.4 GB, `cutouts/` 19.5 GB (includes the tutorial data); 41.2 GB free on D: |
| Output | `networks/TN/elec_s_2_ec_lcopt_3h.nc` (2 buses, 2,920 snapshots × 3 h, 29.88 TWh load) |

## Time resolution decision (Task 7, risk R1)

**Decision (author, 2026-10-28): 1-hour steps for all scenarios.** It replaces the 3 h first planned in spec D11.

| | 3 h | 1 h |
|---|---|---|
| HiGHS run time (two runs) | 50.7–59.5 s | 546.7–591.8 s |
| Peak memory | 0.72 GiB | 1.26 GiB |
| Objective (M EUR/yr) | 1,369.3 | 1,374.0 |

Reasons:
- Affordable: about 10 min per base-network solve. That makes roughly 2 h for all 11 scenarios, an estimate: the renewable-share and load-shift constraints may slow the solves.
- At 3 h, a "shift up to 3 h" is a single step.
- 3 h averaging smooths peaks: compared with 1 h, it built 2.7% more solar and 3.9% more wind, and burned 2.7% less gas.

Base network from now on: `networks/TN/elec_s_2_ec_lcopt_1h.nc` (8,760 snapshots × 1 h, 29.88 TWh, peak 4,620 MW), recorded in `config/pipeline.yaml`.
Full table: `docs/phase2-base-network.md`.
