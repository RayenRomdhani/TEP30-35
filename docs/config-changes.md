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

| 2026-10-27 | Environment repair | reinstalled `currencyconverter==0.18.9`, `googledrivedownloader==1.1.0` (pip, `--force-reinstall --no-deps`) and `snakemake-minimal=7.32.4` (bioconda) | same env | Bitdefender had removed 5 `.py` files and kept their paths blocked until a reboot; an audit of conda/pip install records against the disk now shows no missing files that matter (only gurobipy licence/DLL, unused, and two debugpy `.gitignore` files) |

Key pinned versions: Python 3.11.13, PyPSA 0.30.3, linopy 0.5.5, HiGHS (highspy) 1.11.0, Snakemake 7.32.4.

## Tutorial run (Task 5)

Command (from `D:\pypsa-earth`, PyPSA-Earth unmodified):
`snakemake -j 1 solve_all_networks --configfile config.tutorial.yaml`

| Item | Value |
|---|---|
| Date | 2026-10-27, 16:10 → 17:08 |
| Result | 27 of 27 steps done, exit 0 |
| Runtime | 58.1 min on 1 core (i3-1215U, 24 GB RAM) |
| Downloads | tutorial bundles ≈ 0.75 GB zipped (data 144 MB, cutouts 10 MB, common data 259 MB, hydrobasins 337 MB) + OpenStreetMap data |
| Disk after unzip | `data/` 4.5 GB, other folders < 0.1 GB |
| Solved network | `results/networks/elec_s_6_ec_lcopt_Co2L-4H.nc` (Nigeria + Benin, 18 buses, 36 snapshots × 243 h) |
| Objective | 3,258.9 M EUR/yr |
| Energy balance | generators 42.95 TWh + hydro storage 8.39 TWh = load 51.33 TWh (gap 0.000 TWh) |

Lesson for the Tunisia run: on-disk size is several times the download size, so plan ≥ 30 GB for the ≈ 16 GB Tunisia download (D: had 78 GB free after the tutorial).

## PyPSA-Earth configuration changes

(None yet. Filled in Phase 2.)
