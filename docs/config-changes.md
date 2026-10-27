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

## PyPSA-Earth configuration changes

(None yet. Filled in Phase 2.)
