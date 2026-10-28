# 7. Try it yourself: run the model, add a scenario

> **Learning path:** [1. The problem](01-the-problem.md) · [2. Key ideas](02-key-ideas.md) · [3. How the model works](03-how-the-model-works.md) · [4. The experiment](04-the-experiment.md) · [5. Results](05-results.md) · [6. How far to trust it](06-how-far-to-trust-it.md) · **7. Try it yourself** · [Glossary](glossary.md)

Reading about a model is fine. Breaking it yourself is better. This chapter gets you from a clean computer to your own scenario.

## What you need

- Windows 10 or 11 (the environment file pins Windows packages; on Linux or macOS, create the environment from PyPSA-Earth's own files instead).
- About 45 GB of free disk and a few hours for the first build (mostly downloads: about 16 GB of PyPSA-Earth data).
- [Miniforge](https://github.com/conda-forge/miniforge) (a free Python/conda installer).

## Step 1: set up (once)

1. Clone PyPSA-Earth at the version this study used, and this repository:
   ```bash
   git clone --branch v0.10.0 https://github.com/pypsa-meets-earth/pypsa-earth.git
   ```
   ```bash
   git clone https://github.com/RayenRomdhani/TEP30-35.git
   ```
2. In this repository, create and activate the environment, and install the study's package:
   ```bash
   conda env create -f environment.yml
   ```
   ```bash
   conda activate pypsa-earth
   ```
   ```bash
   pip install -e .
   ```
3. Build the Tunisia network. Run this in the **PyPSA-Earth** folder (it asks nothing, but takes hours the first time):
   ```bash
   snakemake -j 1 networks/TN/elec_s_2_ec_lcopt_1h.nc --configfile <path-to-this-repo>/config/tn_base.yaml
   ```
4. Open `config/pipeline.yaml` in this repository and set `base_network` to the full path of the file you just built.
5. Check everything works:
   ```bash
   pytest
   ```

## Step 2: reproduce the study

```bash
snakemake -j 1
```

This builds, solves and checks all 11 scenarios and writes `results/summary.csv` and `results/avoided.csv`. On my laptop (i3, 24 GB RAM) it took about an hour, 4 to 8 minutes per scenario. Then draw the figures:

```bash
python scripts/make_figures.py
```

## Step 3: your own scenario

Let's ask a question the study did not: **what if Tunisia saves 12%?**

1. Copy `config/scenarios/S1-15.yaml` to `config/scenarios/S1-12.yaml` and edit it so it reads:
   ```yaml
   # Exercise: every hour 12% lower.
   name: S1-12
   reference: S0
   efficiency: {share: 0.12, mode: uniform}
   flexibility: {p_max_mw: 0}
   gas_price_factor: 1.0
   ```
2. Solve only this scenario:
   ```bash
   snakemake -j 1 results/networks/S1-12_solved.nc
   ```
   It takes about 6 minutes. At the end you will see a warning that the peak (4,855 MW) is more than 10% from the reference 5,645 MW. That reference is STEG's 2030 forecast (6,000 MW) minus the flat import flow, and the warning is expected: STEG's forecast assumes no extra savings.
3. Compare it with the base case. Save this as `my_scenario.py` in the repository folder and run `python my_scenario.py`:
   ```python
   import pypsa

   from tn2030.results import avoided_per_mwh, summarize

   base = summarize(pypsa.Network("results/networks/S0_solved.nc"))
   mine = summarize(pypsa.Network("results/networks/S1-12_solved.nc"))
   print(avoided_per_mwh(base, mine).round(2))
   print("new gas turbines (MW):", round(mine["new_cap_OCGT_mw"]))
   ```

When I ran exactly this, I got:

```
cost_eur_per_mwh        61.12
co2_t_per_mwh            0.18
gas_mwh_th_per_mwh       0.91
capacity_mw_per_twh    477.82
dtype: float64
new gas turbines (MW): 0
```

**What does it tell you?** 61.1 EUR per MWh sits neatly between the 10% case (62.6) and the 15% case (59.6): each extra percent saved is worth a little less, because the gas turbines were already avoided at 10%. And no new gas turbines are built, as expected.

## More things to try

- **Gas price:** make copies of S0 and S1-15 with `gas_price_factor: 1.2` and new names (say `G12-S0` and `G12-S1-15`). Set the `reference` of **both** copies to `G12-S0`, as in `G-hi-S0.yaml`; a copy of S0 that still points at S0 has nothing to compare and stops the pipeline. Does dearer gas make saving worth more?
- **Timing:** copy S1-15C and change the share to 0.10. Is the cooling-first bonus bigger or smaller for a smaller saving?
- **Flexibility:** copy S2-300 and set `p_max_mw: 150`. Is the value per MW higher for a smaller amount of shifting?

Two rules keep comparisons fair: compare scenarios that differ in one thing only, and give every scenario a `reference` at the same gas price.

When you are done, delete your extra scenario files, or `snakemake -j 1` will include them in `results/summary.csv` next time.

---

That is the end of the path. Questions, mistakes, ideas: open an issue on the repository. For the full method in one document, see the [report](../../report/report.docx); for how it was built, the [project history](../project-history/README.md).
