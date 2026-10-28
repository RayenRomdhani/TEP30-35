# Tunisia 2030 Energy-Efficiency Study: Implementation Plan

> Work through the tasks in order. Each step is a checkbox (`- [ ]`) to tick when done.

**Goal:** Quantify the capacity, gas, system cost and CO2 Tunisia avoids in 2030 per MWh of electricity saved through efficiency and demand flexibility, under the 35% renewable target.

**Architecture:** PyPSA-Earth (pinned release, unmodified, on `D:`) builds the base Tunisia network. Our package `tn2030` and a small Snakemake pipeline in this repo turn that network into 11 scenarios (`build_scenario → solve → summarize`). All input numbers come from `data/assumptions_register.xlsx`.

**Tech Stack:** Python (version from the PyPSA-Earth env), PyPSA, linopy, HiGHS, Snakemake, pandas, pytest, openpyxl, matplotlib.

**Spec:** `docs/superpowers/specs/2026-10-27-tn-efficiency-2030-design.md` (read it with this plan).

## Global Constraints

- No invented data: every input number is a row in `data/assumptions_register.xlsx` with a source URL, or is typed `assumption`.
- Renewable target: renewables (solar + wind + hydro) ≥ **35%** of **domestic** generation; imports and battery discharge excluded from both sides.
- Scope: countries `["TN"]`, **2 clusters** (4 if runtime allows), **1-hour** steps (chosen by the author after the R1 benchmark in Task 7; first planned at 3 h), solver **HiGHS**.
- Platform: native Windows 11. Miniforge, PyPSA-Earth and its data on **`D:`**; this repo on `C:`.
- Ask the author before any download > 2 GB, and before any download at all (filename, source, size).
- All commands run from the repo root in the activated `pypsa-earth` conda env.
- Deliverables in English. Comments and docstrings short and plain.
- Git: one branch per phase (`phase-1-toy`, `phase-2-pypsa-earth`, `phase-3-validation`, `phase-4-scenarios`, `phase-5-deliverables`), commit after each task. **Commit messages have no co-author or tool-attribution lines. Nothing is pushed without approval.**
- Every phase ends with: `superpowers:requesting-code-review` → `superpowers:verification-before-completion` → 5-line summary + evidence → wait for "go" → `superpowers:finishing-a-development-branch`.

## Review Focus

1. **3-hour snapshot weightings.** Any energy sum (MWh, TWh, gas use, CO2, RES share) must multiply power by `n.snapshot_weightings.generators`; a sum of raw `p` under-counts by 3×. The real runs use 1 h steps (weight 1), where this bug would be invisible, so the 3 h toy fixture is what catches it. Pinned by `test_scale_profile_hits_annual_total_with_3h_weights` (Task 9) and `test_summary_uses_snapshot_weightings` (Task 14).
2. **Imports larger than load in some hour.** Flat imports can exceed night-time load and produce negative demand; this must fail loudly, not silently clip. Pinned by `test_subtract_imports_raises_when_load_goes_negative` (Task 9).
3. **Carrier names differ from our constants** (e.g. `onwind` vs `wind`). The RES constraint would then count nothing and still "solve". Pinned by `test_res_constraint_raises_when_no_carrier_matches` (Task 13).
4. **Avoided metric with zero demand saved.** Gas-price variants of S0 have no saving vs S0; each scenario is compared to its own `reference`, and division by zero raises. Pinned by `test_avoided_per_mwh_raises_on_zero_saving` (Task 14) and the `reference` field (Task 15).
5. **Partial last day for the daily shift reset.** The final day may have fewer snapshots; its last snapshot must still reset the shift state of charge to 0. Pinned by `test_shift_soc_reset_on_partial_last_day` (Task 12).

## File Map

| File | Responsibility |
|---|---|
| `pyproject.toml` | Installs `src/tn2030` as an editable package |
| `src/tn2030/register.py` | Read the assumptions register |
| `src/tn2030/toy.py` | Phase 1 single-node network + annuity |
| `src/tn2030/demand.py` | 2030 demand, profile scaling, imports, peak check |
| `src/tn2030/efficiency.py` | Uniform and cooling-weighted cuts |
| `src/tn2030/flexibility.py` | Shiftable load as virtual storage |
| `src/tn2030/constraints.py` | 35% RES constraint + solve wrapper |
| `src/tn2030/results.py` | Summary metrics, avoided-per-MWh |
| `src/tn2030/checks.py` | Post-solve sanity checks |
| `src/tn2030/scenario.py` | Scenario YAML → modified network |
| `src/tn2030/pipeline.py` | Step functions called by Snakemake |
| `src/tn2030/plotting.py` | Palette, figure style, source footer |
| `Snakefile`, `config/pipeline.yaml`, `config/scenarios/*.yaml` | Scenario pipeline |
| `config/tn_base.yaml` | PyPSA-Earth overrides for Tunisia |
| `data/assumptions_register.xlsx`, `data/committed_projects.csv` | Inputs with sources |
| `tests/conftest.py` | Shared fixture `toy_network` (48 h, 3 h steps) |

---

# Phase 1: Environment and toy model (branch `phase-1-toy`)

### Task 1: Environment and package skeleton

**Files:** Create `pyproject.toml`, `src/tn2030/__init__.py`, `tests/test_smoke.py`, `docs/config-changes.md`

**Interfaces:** Produces the importable package `tn2030` and the `pypsa-earth` conda env used by every later task.

- [x] **Step 1:** Ask the author for permission to download the Miniforge Windows installer (state the URL from github.com/conda-forge/miniforge and its size). Install to `D:\miniforge3` (just me, no PATH change).
- [x] **Step 2:** Find the latest PyPSA-Earth release tag on GitHub; `git clone --branch <tag> --depth 1 https://github.com/pypsa-meets-earth/pypsa-earth D:\pypsa-earth`. Record the tag in `docs/config-changes.md`.
- [x] **Step 3:** Create the env from PyPSA-Earth's Windows instructions (pinned env file if the release ships one, else `envs/environment.yaml`) with `mamba env create`. Then `mamba install -n pypsa-earth pytest openpyxl`.
Verify: `python -c "import pypsa, linopy, highspy, snakemake; print(pypsa.__version__)"` prints a version.
- [x] **Step 4: Write the failing test** `tests/test_smoke.py`:
```python
def test_package_imports():
    import tn2030
    assert tn2030.__version__ == "0.1.0"
```
- [x] **Step 5:** Run `pytest tests/test_smoke.py -v`. Expected: FAIL (`ModuleNotFoundError`).
- [x] **Step 6:** Write `pyproject.toml` (setuptools, `src` layout, name `tn2030`, version `0.1.0`), `src/tn2030/__init__.py` with `__version__ = "0.1.0"`; `pip install -e . --no-deps`.
- [x] **Step 7:** Run `pytest -v`. Expected: 1 passed.
- [x] **Step 8:** Commit: `git add pyproject.toml src tests docs/config-changes.md && git commit -m "build: add tn2030 package skeleton and environment notes"`

### Task 2: Assumptions register and loader

**Files:** Create `src/tn2030/register.py`, `tests/test_register.py`, `data/assumptions_register.xlsx` (use the `anthropic-skills:xlsx` skill)

**Interfaces:**
- Produces: `REGISTER_COLUMNS: tuple[str, ...] = ("id", "parameter", "value", "unit", "type", "source_title", "source_url", "accessed", "notes")`; `load_register(path: Path) -> dict[str, float]` returning `id → value` for rows with `type` in `{"sourced", "assumption"}`; rows typed `pending` are left out, so code asking for them fails with `KeyError`.

- [x] **Step 1: Write the failing tests** (build a tiny xlsx in `tmp_path` with pandas):
```python
def test_load_register_returns_sourced_and_assumption_rows(tmp_path): ...
    assert reg == {"re_target_2030": 0.35, "flex_max_hours": 3.0}
def test_load_register_skips_pending_rows(tmp_path): ...
    assert "demand_2024_twh" not in reg
def test_load_register_rejects_sourced_row_without_url(tmp_path):
    with pytest.raises(ValueError, match="source_url"): load_register(path)
def test_load_register_rejects_duplicate_ids(tmp_path):
    with pytest.raises(ValueError, match="duplicate"): load_register(path)
```
- [x] **Step 2:** Run `pytest tests/test_register.py -v`. Expected: 4 FAIL.
- [x] **Step 3:** Implement `load_register` with `pd.read_excel(path, sheet_name="register")`.
- [x] **Step 4:** Run the tests. Expected: 4 passed.
- [x] **Step 5:** Create the real register (sheet `register`) with these rows:

| id | value | type | source |
|---|---|---|---|
| `re_target_2030` | 0.35 | sourced | TAP, 9 Oct 2026 (spec §2) |
| `flex_cap_mw` | 300 | sourced | TAP, 9 Oct 2026 |
| `flex_cap_hi_mw` | 600 | assumption | 2 × official figure |
| `flex_max_hours` | 3 | assumption | spec D5 |
| `gas_price_factor_lo` / `_hi` | 0.5 / 1.5 | assumption | spec D8 |
| `demand_growth` | 0.037 | sourced | REGlobal (secondary, note R6) |
| `peak_ref_2030_mw` | 6000 | sourced | REGlobal (secondary) |
| `demand_2024_twh`, `imports_2024_twh`, `gas_price_eur_per_mwh_th` | (blank) | pending | Phase 3 |

- [x] **Step 6:** Commit: `git commit -m "feat: add assumptions register and loader"`

### Task 3: Annuity and toy costs

**Files:** Create `src/tn2030/toy.py`, `tests/test_toy.py`

**Interfaces:**
- Produces: `annuity(rate: float, lifetime_years: float) -> float`; `annualised_capex(investment: float, fom_pct: float, lifetime_years: float, rate: float) -> float` (EUR/MW/yr = investment × (annuity + fom_pct/100)).

Toy costs come from PyPSA `technology-data` `outputs/costs_2030.csv` (ask before download; small file into `data/raw/`). Add every value used to the register (`toy_*` ids, `sourced`, with the CSV URL and commit hash).

- [x] **Step 1: Write the failing tests:**
```python
def test_annuity_known_value():
    assert annuity(0.07, 25) == pytest.approx(0.08581, abs=1e-5)
def test_annuity_zero_rate_is_straight_line():
    assert annuity(0.0, 20) == pytest.approx(0.05)
def test_annualised_capex_adds_fom():
    assert annualised_capex(1000.0, 2.0, 25, 0.07) == pytest.approx(1000 * (0.08581 + 0.02), rel=1e-4)
```
- [x] **Step 2:** Run `pytest tests/test_toy.py -v`. Expected: 3 FAIL.
- [x] **Step 3:** Implement both functions (annuity = r / (1 − (1+r)^−n), 1/n when r = 0).
- [x] **Step 4:** Run the tests. Expected: 3 passed.
- [x] **Step 5:** Commit: `git commit -m "feat: add annuity and annualised capex"`

### Task 4: Toy network, solve, explanation

**Files:** Modify `src/tn2030/toy.py`; create `tests/conftest.py`, `scripts/phase1_toy_model.py`, `docs/phase1-toy-model.md`; test in `tests/test_toy.py`

**Interfaces:**
- Consumes: `load_register`, `annualised_capex`.
- Produces: `build_toy_network(register: dict[str, float], hours: int = 168, step_hours: int = 1) -> pypsa.Network` with one bus `"TN"`, carriers `"CCGT"`, `"solar"`, `"onwind"` (extendable `Generator`s), `"battery"` (extendable `StorageUnit`, `max_hours` from register), load `"TN load"`. Carriers carry `co2_emissions` (t/MWh_th). `snapshot_weightings` = `step_hours`. Load, solar and wind profiles are **illustrative synthetic shapes** (sine-based), stated in the docstring and figure footer. Fixture `toy_network` in `conftest.py` = `build_toy_network(reg, hours=48, step_hours=3)`, with `reg` from a fixture register dict (no file I/O).

- [x] **Step 1: Write the failing tests:**
```python
def test_toy_solves_optimal(toy_network):
    status, _ = toy_network.optimize(solver_name="highs")
    assert status == "ok"
def test_toy_energy_balance_closes(toy_network):
    toy_network.optimize(solver_name="highs")
    w = toy_network.snapshot_weightings.generators
    supply = (toy_network.generators_t.p.sum(axis=1) + toy_network.storage_units_t.p.sum(axis=1)) * w
    demand = toy_network.loads_t.p_set.sum(axis=1) * w
    assert supply.sum() == pytest.approx(demand.sum(), rel=1e-6)
def test_toy_battery_soc_within_bounds(toy_network): ...
    assert (soc <= su.p_nom_opt * su.max_hours + 1e-6).all() and (soc >= -1e-6).all()
```
- [x] **Step 2:** Run. Expected: FAIL (`build_toy_network` not defined).
- [x] **Step 3:** Implement `build_toy_network`.
- [x] **Step 4:** Run `pytest -v`. Expected: all pass.
- [x] **Step 5:** `scripts/phase1_toy_model.py`: build a 168 h network, solve, print capacities and cost, and save `results/figures/phase1_toy_dispatch.png` (stacked dispatch + load line, footer "Illustrative inputs; costs: PyPSA technology-data 2030"). Use the `dataviz` skill for the style.
Verify: `python scripts/phase1_toy_model.py` prints `status ok` and the PNG exists.
- [x] **Step 6:** `docs/phase1-toy-model.md` (use `concept-explainer`): objective (min Σ annualised capex × capacity + Σ marginal cost × dispatch × weighting), constraints (nodal energy balance, capacity limits with availability profiles, storage state-of-charge continuity, energy ≤ p_nom × max_hours), each mapped to the PyPSA component that creates it, plus what the results show.
- [x] **Step 7:** Commit: `git commit -m "feat: add Phase 1 single-node toy model and explanation"`
- [x] **Step 8: Phase gate** (see Global Constraints). Evidence: pytest output, solve log, dispatch PNG.

---

# Phase 2: PyPSA-Earth (branch `phase-2-pypsa-earth`)

Failures here go through `superpowers:systematic-debugging` and the `operations-planning-mitigation` skill. Fix root causes only; log every change in `docs/config-changes.md` (what, why, file:key).

### Task 5: Tutorial run

**Files:** Modify `docs/config-changes.md`

- [x] **Step 1:** In `D:\pypsa-earth`, follow the release's tutorial instructions (copy the tutorial config as instructed by its docs).
- [x] **Step 2:** Dry run: `snakemake -j 1 solve_all_networks -n`. Expected: a job list, no errors.
- [x] **Step 3:** Before the real run, find the size of each data bundle it will retrieve. If the total is > 2 GB, stop and ask.
- [x] **Step 4:** Run `snakemake -j 1 solve_all_networks`. Expected: a solved network in `results/networks/`.
- [x] **Step 5:** Record runtime, peak RAM and bundle sizes in `docs/config-changes.md`; commit in this repo: `git commit -m "docs: record PyPSA-Earth tutorial run"`

### Task 6: Tunisia base network

**Files:** Create `config/tn_base.yaml`, `scripts/inspect_base.py`, `docs/phase2-base-network.md`

**Interfaces:**
- Produces: a prepared (not solved) base network `.nc` path, written into `config/pipeline.yaml` as `base_network:`; the list of carrier names actually used (feeds the constants in Task 13).

- [x] **Step 1:** Write `config/tn_base.yaml` with only the keys we change, checked against the pinned `config.default.yaml`: `countries: ["TN"]`, clusters `[2]`, time resolution `3H` (changed to 1 h after Task 7), cost year 2030, extendable carriers CCGT, OCGT, solar, onwind, battery, solver `highs`. Each key gets a one-line comment saying why.
- [x] **Step 2:** Check whether the pinned release has a built-in minimum-renewable-share option. Record the answer (key name, or "none, custom constraint in Task 13") in `docs/config-changes.md`.
- [x] **Step 3:** Dry run with `--configfile <repo>/config/tn_base.yaml` up to the prepared network. Check bundle sizes (> 2 GB → ask). Then run.
- [x] **Step 4:** `scripts/inspect_base.py <network.nc>` prints buses, carriers, `p_nom` by carrier, annual load (TWh, using weightings), peak load. Save the output in `docs/phase2-base-network.md`.
Verify: TN-only buses; ≥ 1 gas generator; annual load > 0.
- [x] **Step 5:** Commit: `git commit -m "feat: add Tunisia PyPSA-Earth base configuration"`

### Task 7: Resolution benchmark (risk R1)

**Files:** Modify `docs/phase2-base-network.md`

- [x] **Step 1:** Solve the base network as-is at 3 H and at 1 H (same config otherwise). Record solve time and peak RAM.
- [x] **Step 2:** Present both numbers to the author with a recommendation. **Their decision** sets the resolution for all scenarios; record it in the spec's D11 and in `docs/config-changes.md`.
- [x] **Step 3:** Commit, then **Phase gate**. Evidence: run logs, network summary, config-change log, benchmark table.

---

# Phase 3: Data and baseline validation (branch `phase-3-validation`)

### Task 8: Collect sourced inputs

**Files:** Modify `data/assumptions_register.xlsx`; create `data/committed_projects.csv`, `data/raw/SOURCES.md`

Use the `anthropic-skills:pdf` skill for STEG / ANME / IRENA reports, and `superpowers:dispatching-parallel-agents` to search independent sources in parallel. Read Ember's own Tunisia data directly (risk R7).

- [x] **Step 1:** Fill the pending register rows: `demand_2024_twh`, `imports_2024_twh`, `gas_price_eur_per_mwh_th` (from the technology-data version used by PyPSA-Earth). Add validation rows: `cap_2024_<carrier>_mw` (STEG), `gen_2024_<carrier>_twh` and `gas_share_2024` (Ember). Each has a URL and access date; disagreements get a `notes` line. If a sourced ANME efficiency programme cost exists, add `ee_programme_cost_eur_per_mwh` (compared with the headline value in the report, spec §1); if none is found, say so in the README limitations.
- [x] **Step 2:** `data/committed_projects.csv` with columns `name, carrier, p_nom_mw, e_nom_mwh, bus, status, source_url`. `status` ∈ {`under_construction`, `signed_contract`}; announced-only projects are not included (spec D6). `bus` = nearest base-network bus to the site. *As built:* extra columns `governorate, cod_expected, notes`; a third status `operating_since_2025/2026` for plants that came online after the 2024 fleet; `bus` = the bus region holding most of the governorate's area (method in `data/raw/SOURCES.md`), since no source gives site coordinates.
- [x] **Step 3:** `python -c "from tn2030.register import load_register; r = load_register('data/assumptions_register.xlsx'); print(r['demand_2024_twh'], r['imports_2024_twh'])"` prints two numbers.
- [x] **Step 4:** Commit: `git commit -m "data: add sourced 2024 inputs and committed projects"`

### Task 9: Demand module

**Files:** Create `src/tn2030/demand.py`, `tests/test_demand.py`

**Interfaces:**
- Produces:
  - `annual_demand_2030(d2024_twh: float, growth: float, years: int = 6) -> float` (TWh)
  - `scale_profile(profile: pd.Series, weights: pd.Series, annual_total_mwh: float) -> pd.Series` (MW; keeps shape)
  - `subtract_imports(profile: pd.Series, weights: pd.Series, annual_imports_mwh: float) -> pd.Series` (flat MW = imports / weights.sum(); `ValueError` "negative" if any value < 0)
  - `peak_check(profile: pd.Series, reference_mw: float, tolerance: float = 0.10) -> tuple[float, bool]`

- [x] **Step 1: Write the failing tests:**
```python
def test_annual_demand_2030_compounds_growth():
    assert annual_demand_2030(20.0, 0.037) == pytest.approx(20.0 * 1.037**6)
def test_scale_profile_hits_annual_total_with_3h_weights():
    idx = pd.date_range("2030-01-01", periods=8, freq="3h")
    w = pd.Series(3.0, index=idx); p = pd.Series([1, 2, 3, 4, 4, 3, 2, 1], index=idx, dtype=float)
    out = scale_profile(p, w, 1200.0)
    assert (out * w).sum() == pytest.approx(1200.0)
    assert out.iloc[3] / out.iloc[0] == pytest.approx(4.0)
def test_subtract_imports_is_flat():   # 24 MWh over 24 h -> 1 MW every step
    ...; assert np.allclose(p - subtract_imports(p, w, 24.0), 1.0)
def test_subtract_imports_raises_when_load_goes_negative():
    with pytest.raises(ValueError, match="negative"): subtract_imports(p, w, 1e6)
def test_peak_check_flags_outside_tolerance():
    assert peak_check(pd.Series([5000.0, 6700.0]), 6000) == (6700.0, False)
    assert peak_check(pd.Series([5000.0, 6300.0]), 6000) == (6300.0, True)
```
- [x] **Step 2:** Run `pytest tests/test_demand.py -v`. Expected: 5 FAIL.
- [x] **Step 3:** Implement the four functions.
- [x] **Step 4:** Run. Expected: 5 passed.
- [x] **Step 5:** Commit: `git commit -m "feat: add 2030 demand calibration functions"`

### Task 10: Baseline validation

**Files:** Create `scripts/validate_baseline.py`, `docs/phase3-validation.md`, `results/validation.csv`

**Interfaces:**
- Consumes: the base network, `load_register`, `scale_profile`, `subtract_imports`.

- [x] **Step 1:** Script: (a) compare existing `p_nom` by carrier in the base network with `cap_2024_*` rows; (b) copy the network, freeze all capacities (`p_nom_extendable = False`), scale load to 2024 demand minus 2024 imports, solve a dispatch-only run, compare generation by carrier and gas share with `gen_2024_*` and `gas_share_2024`. Write `results/validation.csv` with columns `metric, model, reference, diff_pct, source`.
Verify: `python scripts/validate_baseline.py` writes the CSV with one row per compared metric.
- [x] **Step 2:** `docs/phase3-validation.md`: comparison table, explanation of each gap > 10%, and each calibration (what changed, why, source). Calibrations go into `config/tn_base.yaml` or the register, never as unexplained edits to the network.
- [ ] **Step 3:** Commit, then **Phase gate**. Evidence: validation table, explained gaps, calibration log.

---

# Phase 4: Scenario pipeline and runs (branch `phase-4-scenarios`)

All tests here use the `toy_network` fixture (48 h at 3 h steps) so they run in seconds.

### Task 11: Efficiency module

**Files:** Create `src/tn2030/efficiency.py`, `tests/test_efficiency.py`

**Interfaces:**
- Produces:
  - `SHOULDER_MONTHS = (4, 5, 10, 11)`, `SUMMER_MONTHS = (6, 7, 8, 9)`
  - `uniform_cut(profile: pd.Series, share: float) -> pd.Series`
  - `cooling_component(profile: pd.Series) -> pd.Series` (spec §5.2 steps 1–2; needs a full-year `DatetimeIndex`)
  - `cooling_weighted_cut(profile: pd.Series, weights: pd.Series, share: float) -> tuple[pd.Series, float]` returning (new profile, fraction of the saving placed on cooling)

Algorithm for `cooling_weighted_cut` (spec §5.2 steps 3–5):
```
S  = share * (profile * weights).sum()          # required saving, MWh
C  = cooling_component(profile); Ec = (C * weights).sum()
on_cooling = min(S, Ec)
out = profile - (C * on_cooling / Ec if Ec > 0 else 0)
rest = S - on_cooling
if rest > 0: out = out * (1 - rest / (out * weights).sum())
return out, on_cooling / S
```

- [x] **Step 1: Write the failing tests** (full 2030 hourly index; base 1000 MW flat, +500 MW at 12:00–17:00 in July):
```python
def test_uniform_cut_scales_every_hour():
    assert np.allclose(uniform_cut(p, 0.15), p * 0.85)
def test_cooling_component_only_in_summer_excess():
    c = cooling_component(p)
    assert c[july_peak_hours].eq(500).all() and c.drop(july_peak_hours).eq(0).all()
def test_cooling_weighted_cut_keeps_annual_saving():
    out, frac = cooling_weighted_cut(p, w, 0.15)
    assert ((p - out) * w).sum() == pytest.approx(0.15 * (p * w).sum())
def test_cooling_weighted_cut_never_negative():
    out, _ = cooling_weighted_cut(p, w, 0.15); assert (out >= 0).all()
def test_cooling_weighted_cut_flat_profile_falls_back_to_uniform():
    out, frac = cooling_weighted_cut(flat, w, 0.15)
    assert frac == 0.0 and np.allclose(out, flat * 0.85)
```
- [x] **Step 2:** Run `pytest tests/test_efficiency.py -v`. Expected: 5 FAIL.
- [x] **Step 3:** Implement.
- [x] **Step 4:** Run. Expected: 5 passed.
- [x] **Step 5:** Commit: `git commit -m "feat: add uniform and cooling-weighted efficiency cuts"`

### Task 12: Flexibility module

**Files:** Create `src/tn2030/flexibility.py`, `tests/test_flexibility.py`

**Interfaces:**
- Produces: `add_shiftable_load(n: pypsa.Network, p_max_mw: float, max_hours: float) -> None`. Adds one `StorageUnit` per load bus named `"demand_shift <bus>"`, carrier `"demand_shift"` (added to `n.carriers` if missing), `p_nom` = `p_max_mw` × (bus annual load share), `max_hours`, `efficiency_store = efficiency_dispatch = 1`, `capital_cost = marginal_cost = 0`, `p_nom_extendable = False`, `cyclic_state_of_charge = False`. `state_of_charge_set` = 0 at the last snapshot of each calendar day, NaN elsewhere (spec §5.3).

- [x] **Step 1: Write the failing tests:**
```python
def test_shift_split_by_bus_load_share(two_bus_network):        # loads 3:1
    add_shiftable_load(two_bus_network, 300.0, 3.0)
    assert two_bus_network.storage_units.p_nom.tolist() == pytest.approx([225.0, 75.0])
def test_shift_soc_zero_at_each_day_end(toy_network):
    add_shiftable_load(toy_network, 300.0, 3.0); toy_network.optimize(solver_name="highs")
    soc = toy_network.storage_units_t.state_of_charge["demand_shift TN"]
    assert soc[soc.index.hour == 21].abs().max() < 1e-6        # last 3 h step of each day
def test_shift_soc_reset_on_partial_last_day(toy_network_partial_day):  # 52 h horizon
    add_shiftable_load(toy_network_partial_day, 300.0, 3.0)
    s = toy_network_partial_day.storage_units_t.state_of_charge_set["demand_shift TN"]
    assert s.iloc[-1] == 0.0
def test_shift_is_energy_neutral(toy_network): ...
    assert (p * w).sum() == pytest.approx(0.0, abs=1e-6)
```
- [x] **Step 2:** Run. Expected: 4 FAIL.
- [x] **Step 3:** Implement. Add fixtures `two_bus_network` and `toy_network_partial_day` to `conftest.py`.
- [x] **Step 4:** Run. Expected: 4 passed.
- [x] **Step 5:** Commit: `git commit -m "feat: add shiftable load as daily energy-neutral virtual storage"`

### Task 13: RES constraint and solve wrapper

**Files:** Create `src/tn2030/constraints.py`, `tests/test_constraints.py`

**Interfaces:**
- Produces:
  - `RES_CARRIERS: tuple[str, ...]` = names confirmed in Task 6 (expected `("solar", "onwind", "ror", "hydro")`)
  - `add_min_res_share(n: pypsa.Network, share: float, res_carriers: tuple[str, ...] = RES_CARRIERS) -> None` (call inside `extra_functionality`). Numerator: weighted dispatch of `Generator`s with RES carriers + `StorageUnit` `p_dispatch` with carrier `hydro`. Denominator: all `Generator`s + hydro `p_dispatch`. Batteries and `demand_shift` excluded. `ValueError` if no component matches `res_carriers`.
  - `solve_network(n: pypsa.Network, res_share: float, solver_name: str = "highs") -> None` (`RuntimeError` if status ≠ `"ok"`)
  - `res_share(n: pypsa.Network, res_carriers: tuple[str, ...] = RES_CARRIERS) -> float` (ex-post, same definition)

- [x] **Step 1: Write the failing tests:**
```python
def test_res_share_binding_when_gas_is_cheap(toy_network_cheap_gas):
    toy_network_cheap_gas.optimize(solver_name="highs")
    assert res_share(toy_network_cheap_gas) < 0.35               # unconstrained
def test_solve_network_enforces_35pct(toy_network_cheap_gas):
    solve_network(toy_network_cheap_gas, 0.35)
    assert res_share(toy_network_cheap_gas) >= 0.35 - 1e-6
def test_res_constraint_raises_when_no_carrier_matches(toy_network):
    with pytest.raises(ValueError, match="carrier"):
        solve_network_with(toy_network, res_carriers=("wind",))
```
(`solve_network_with` is a test helper calling `n.optimize(extra_functionality=lambda n, s: add_min_res_share(n, 0.35, ("wind",)))`.)
- [x] **Step 2:** Run. Expected: FAIL.
- [x] **Step 3:** Add fixture `toy_network_cheap_gas` to `conftest.py` (toy network with solar and wind `capital_cost` × 5, so the unconstrained RES share falls below 35%). Implement with linopy: `n.model["Generator-p"]` and `n.model["StorageUnit-p_dispatch"]`, multiplied by `n.snapshot_weightings.generators`. If Task 6 found a built-in option, still keep `res_share` for the check and document why the custom constraint is kept or dropped.
- [x] **Step 4:** Run. Expected: 3 passed.
- [x] **Step 5:** Commit: `git commit -m "feat: add 35% renewable share constraint and solve wrapper"`

### Task 14: Results and sanity checks

**Files:** Create `src/tn2030/results.py`, `src/tn2030/checks.py`, `tests/test_results.py`, `tests/test_checks.py`

**Interfaces:**
- Produces:
  - `summarize(n: pypsa.Network) -> pd.Series` with keys `cap_<carrier>_mw`, `new_cap_<carrier>_mw` (= `p_nom_opt − p_nom_min` for extendable components), `new_cap_total_mw`, `gen_<carrier>_twh`, `demand_twh` (total load + imports is **not** added; domestic load only, imports cancel in differences), `gas_use_twh_th`, `co2_mt`, `system_cost_meur` (`n.statistics.capex().sum() + n.statistics.opex().sum()`, M EUR), `avg_price_eur_mwh` (load-weighted bus marginal price)
  - `avoided_per_mwh(base: pd.Series, scen: pd.Series) -> pd.Series` with keys `cost_eur_per_mwh`, `co2_t_per_mwh`, `gas_mwh_th_per_mwh`, `capacity_mw_per_twh`. `ValueError` "zero saving" if `base.demand_twh == scen.demand_twh`.
  - `sanity_check(n: pypsa.Network, res_share_min: float, committed: pd.DataFrame, peak_ref_mw: float) -> list[str]` raising `AssertionError` on: energy balance gap > 1e-4 relative, RES share < min − 1e-6, any load-shedding dispatch > 0, any committed capacity not met; returns warnings (peak outside ±10%).

- [x] **Step 1: Write the failing tests:**
```python
def test_summary_uses_snapshot_weightings(solved_toy):
    s = summarize(solved_toy)
    w = solved_toy.snapshot_weightings.generators
    assert s["demand_twh"] == pytest.approx((solved_toy.loads_t.p_set.sum(axis=1) * w).sum() / 1e6)
def test_gas_use_and_co2_follow_efficiency(solved_toy):
    s = summarize(solved_toy)
    assert s["co2_mt"] == pytest.approx(s["gas_use_twh_th"] * co2_factor)   # factor from fixture register
def test_avoided_per_mwh_values():
    base = pd.Series({"system_cost_meur": 100.0, "co2_mt": 2.0, "gas_use_twh_th": 5.0, "new_cap_total_mw": 1000.0, "demand_twh": 10.0})
    scen = pd.Series({"system_cost_meur": 90.0, "co2_mt": 1.8, "gas_use_twh_th": 4.5, "new_cap_total_mw": 900.0, "demand_twh": 9.0})
    a = avoided_per_mwh(base, scen)
    assert a["cost_eur_per_mwh"] == pytest.approx(10.0)
    assert a["co2_t_per_mwh"] == pytest.approx(0.2)
    assert a["gas_mwh_th_per_mwh"] == pytest.approx(0.5)
    assert a["capacity_mw_per_twh"] == pytest.approx(100.0)
def test_avoided_per_mwh_raises_on_zero_saving():
    with pytest.raises(ValueError, match="zero saving"): avoided_per_mwh(base, base)
def test_sanity_check_passes_on_solved_toy(solved_toy): assert isinstance(sanity_check(...), list)
def test_sanity_check_fails_on_res_shortfall(solved_toy):
    with pytest.raises(AssertionError, match="renewable share"): sanity_check(solved_toy, 0.99, ...)
def test_sanity_check_fails_on_missing_committed(solved_toy):
    with pytest.raises(AssertionError, match="committed"): sanity_check(solved_toy, 0.0, committed_10gw_solar, ...)
```
- [x] **Step 2:** Run. Expected: FAIL.
- [x] **Step 3:** Implement both modules. Add fixture `solved_toy` (toy solved with `solve_network(n, 0.35)`).
- [x] **Step 4:** Run. Expected: 7 passed.
- [x] **Step 5:** Commit: `git commit -m "feat: add result metrics, avoided-per-MWh and sanity checks"`

### Task 15: Scenario builder

**Files:** Create `src/tn2030/scenario.py`, `tests/test_scenario.py`, `config/scenarios/*.yaml` (11 files)

**Interfaces:**
- Consumes: Tasks 9, 10 (calibrations), 11, 12.
- Produces:
  - `calibrate_base(n_base: pypsa.Network, register: dict[str, float]) -> pypsa.Network` (copy). Applies the Phase 3 calibrations (see `docs/phase3-validation.md`):
    - `fleet.rebuild_thermal_fleet` with the ONEM capacities (steam counted with OCGT) and `existing_gas_efficiency_factor`;
    - `fleet.add_ocgt_candidates`, with capital cost = annuity(`discount_rate`, `ocgt_lifetime`) × `ocgt_investment` + FOM;
    - existing solar and onwind floor `p_nom_min = p_nom` (PyPSA-Earth's 2024 estimate, incl. the IRENA top-up the validation run used).
    The toy fixture has no existing gas, so scenario unit tests call `build_scenario(..., calibrate=False)`; the calibration functions have their own tests.
  - `load_scenario(path: Path) -> dict` validating keys `name, reference, efficiency.share, efficiency.mode ∈ {uniform, cooling}, flexibility.p_max_mw, gas_price_factor` (`ValueError` naming the bad key)
  - `apply_committed(n: pypsa.Network, committed: pd.DataFrame) -> None`: raises `p_nom_min` (and `p_nom` floor) of the extendable component with the same `carrier` and `bus` by `p_nom_mw`; `ValueError` if none exists
  - `scale_gas_cost(n: pypsa.Network, factor: float, gas_price_eur_per_mwh_th: float) -> None`: for carriers `CCGT`, `OCGT`, `marginal_cost += (factor − 1) × price / efficiency`
  - `build_scenario(n_base: pypsa.Network, scenario: dict, register: dict[str, float], committed: pd.DataFrame, calibrate: bool = True) -> pypsa.Network` (returns a copy). Order fixed by spec §5.1: `calibrate_base` (if `calibrate`) → reshape total load with `demand.reshape_profile` (load factor = `demand_2024_twh` / 8,784 h / `peak_2024_mw`, `min_to_peak_2030`) → scale to `annual_demand_2030` split by base bus shares → efficiency cut → subtract imports split by the same shares → `apply_committed` (all rows of `data/committed_projects.csv`, including `operating_since_*`) → `scale_gas_cost` (existing and new CCGT/OCGT) → `add_shiftable_load` if `p_max_mw > 0`.
  - Decided 2026-10-28 (author): the efficiency-factor issue (it also absorbs outages; see `docs/phase3-validation.md`, gap 2) is recorded as a limitation, no sensitivity run. Added instead: STEG's 10% reserve margin in all runs (spec D14) and a two-way 3 h shift limit (spec D5).

Scenario files (`reference` is the scenario it is compared against):

| file | efficiency | mode | p_max_mw | gas factor | reference |
|---|---|---|---|---|---|
| `S0.yaml` | 0 | uniform | 0 | 1.0 | S0 |
| `S1-10/15/20.yaml` | 0.10/0.15/0.20 | uniform | 0 | 1.0 | S0 |
| `S1-15C.yaml` | 0.15 | cooling | 0 | 1.0 | S0 |
| `S2-300.yaml`, `S2-600.yaml` | 0.15 | uniform | 300 / 600 | 1.0 | S0 |
| `G-lo-S0`, `G-hi-S0` | 0 | uniform | 0 | 0.5 / 1.5 | itself |
| `G-lo-S1-15`, `G-hi-S1-15` | 0.15 | uniform | 0 | 0.5 / 1.5 | G-lo-S0 / G-hi-S0 |

Flex sizes and gas factors in YAML are register ids (`flex_cap_mw`, `gas_price_factor_lo`), resolved by `build_scenario`, so no number lives in two places.

- [x] **Step 1: Write the failing tests:**
```python
def test_build_scenario_hits_2030_demand_minus_saving_minus_imports(toy_network, reg): ...
    expected = annual_demand_2030(reg["demand_2024_twh"], reg["demand_growth"]) * 0.85 - reg["imports_2024_twh"]
    assert weighted_load_twh(out) == pytest.approx(expected)
def test_build_scenario_does_not_modify_base(toy_network, reg): ...
def test_scale_gas_cost_adds_fuel_part_only(toy_network):
    before = mc("CCGT"); scale_gas_cost(toy_network, 1.5, 30.0)
    assert mc("CCGT") - before == pytest.approx(0.5 * 30.0 / eff("CCGT"))
def test_apply_committed_raises_p_nom_min(toy_network): ...
def test_apply_committed_unknown_carrier_raises(toy_network):
    with pytest.raises(ValueError, match="no extendable"): ...
def test_load_scenario_rejects_bad_mode(tmp_path):
    with pytest.raises(ValueError, match="efficiency.mode"): ...
def test_all_scenario_files_load():
    assert len([load_scenario(p) for p in Path("config/scenarios").glob("*.yaml")]) == 11
```
- [x] **Step 2:** Run. Expected: FAIL.
- [x] **Step 3:** Implement and write the 11 YAML files.
- [x] **Step 4:** Run `pytest -v`. Expected: all pass.
- [x] **Step 5:** Commit: `git commit -m "feat: add scenario builder and 11 scenario definitions"`

### Task 16: Snakemake pipeline and full run

**Files:** Create `src/tn2030/pipeline.py`, `Snakefile`, `config/pipeline.yaml`, `tests/test_pipeline.py`; outputs `results/summary.csv`, `results/avoided.csv`

**Interfaces:**
- Produces (called from Snakemake `run:` blocks):
  - `build_step(base_path: Path, scenario_path: Path, register_path: Path, committed_path: Path, out_path: Path) -> None`
  - `solve_step(in_path: Path, out_path: Path, register_path: Path, committed_path: Path) -> None` (solve, then `sanity_check`; warnings printed and written to `<out>.warnings.txt`)
  - `summarize_step(solved_paths: list[Path], scenario_paths: list[Path], summary_out: Path, avoided_out: Path) -> None` (one row per scenario; `avoided.csv` compares each with its `reference`, skips self-references)
- Rules: `all` → `build_scenario` (`results/networks/{s}_built.nc`) → `solve` (`results/networks/{s}_solved.nc`) → `summarize`. `.nc` files are gitignored; CSVs are committed.

- [x] **Step 1: Write the failing integration test** (toy base saved to `tmp_path`, two scenario YAMLs S0 and S1-15, fixture register and empty committed CSV):
```python
def test_pipeline_end_to_end_on_toy(tmp_path):
    ...build_step → solve_step → summarize_step...
    summary = pd.read_csv(tmp_path / "summary.csv", index_col=0)
    avoided = pd.read_csv(tmp_path / "avoided.csv", index_col=0)
    assert list(summary.index) == ["S0", "S1-15"]
    assert summary.loc["S1-15", "demand_twh"] < summary.loc["S0", "demand_twh"]
    assert avoided.loc["S1-15", "cost_eur_per_mwh"] > 0
```
- [x] **Step 2:** Run. Expected: FAIL.
- [x] **Step 3:** Implement `pipeline.py` and `Snakefile`.
- [x] **Step 4:** Run `pytest -v`. Expected: all pass. Then `snakemake -n` lists 11 build + 11 solve + 1 summarize jobs.
- [x] **Step 5:** Run `snakemake -j 1` on the real base network. Expected: `results/summary.csv` (11 rows), `results/avoided.csv` (8 rows: every scenario except the three self-referenced ones), no sanity-check failure. Failures → `superpowers:systematic-debugging` + `operations-planning-mitigation`.
- [x] **Step 6:** `docs/phase4-scenarios.md`: how efficiency and flexibility are represented (spec §5.2–5.3 in plain words), runtimes, all warnings.
- [x] **Step 7:** Commit, then **Phase gate**. Evidence: Snakemake log, both CSVs, pytest output.

---

# Phase 5: Analysis and deliverables (branch `phase-5-deliverables`)

### Task 17: Figures

**Files:** Create `src/tn2030/plotting.py`, `scripts/make_figures.py`, `tests/test_plotting.py`; outputs `results/figures/*.png`

**Interfaces:**
- Produces: `PALETTE: dict[str, str]` (one colour per carrier, fixed across all figures); `finish_figure(fig, ax, title: str, ylabel: str, source: str) -> None` (title, unit label, source footer).

Use the `dataviz` skill before writing any chart code.

- [x] **Step 1: Write the failing test:**
```python
def test_finish_figure_adds_source_footer():
    fig, ax = plt.subplots(); finish_figure(fig, ax, "T", "GW", "Source: X")
    assert any("Source: X" in t.get_text() for t in fig.texts)
def test_palette_covers_all_carriers(solved_toy):
    assert set(solved_toy.generators.carrier) <= set(PALETTE)
```
- [x] **Step 2:** Run. Expected: FAIL. **Step 3:** Implement. **Step 4:** Run. Expected: pass.
- [x] **Step 5:** `scripts/make_figures.py` writes: capacity mix, generation mix, gas use, system cost, CO2, price duration curves, S0 vs S2-300 summer-week dispatch (7 days centred on the annual peak hour), avoided-per-MWh bar chart (headline), uniform vs cooling comparison.
Verify: 9 PNGs exist; inspect each visually.
- [x] **Step 6:** Commit: `git commit -m "feat: add result figures"`

### Task 18: README, environment, report, deck

**Files:** Create `README.md`, `environment.yml`, `report/report.docx`, `report/deck.pptx`

- [x] **Step 1:** `conda env export -n pypsa-earth --from-history > environment.yml`; add the PyPSA-Earth tag and `pip install -e .` line to README.
Verify: README "How to reproduce" steps run from a clean clone up to `pytest` passing.
- [x] **Step 2:** `README.md` (`technical-writing-guide`, then `humanizer`): question, method, assumptions (link to register), results (headline table + figure), limitations (programme costs not modelled, R1 resolution, secondary sources R6/R7, flat imports), how to reproduce.
- [x] **Step 3:** `report/report.docx` via `anthropic-skills:docx`; `report/deck.pptx` (6–8 slides) via `presentation-builder` + `anthropic-skills:pptx`. Numbers are pulled only from `results/*.csv`.
- [x] **Step 4:** `test-coverage-analyzer` on `src/tn2030`; record the coverage figure in the README.
- [x] **Step 5:** Commit: `git commit -m "docs: add README, environment, report and deck"`

### Task 19: Reusable skill

- [ ] **Step 1:** With `anthropic-skills:skill-creator` and `superpowers:writing-skills`, package the workflow as `pypsa-country-study` (country config → validation → scenario pipeline → deliverables), with this repo as the worked example. Ask the author where it should live (user skills folder and/or a `skill/` folder in this repo).
- [ ] **Step 2:** **Phase gate.** Evidence: figures, report, deck, README reproduce check, coverage figure. Ask before any push to GitHub.

### Task 20 (optional): ELMED

Decided after Phase 4 (spec D13). If the author says go: add a sourced Italy link scenario `S3.yaml` (capacity and Italian price profile from cited sources in the register), extend the summary, rerun.
