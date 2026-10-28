# Reader Guide Implementation Plan

> Work through the tasks in order; each step is a checkbox to tick when done.

**Goal:** Turn the repository into something an average engineering student can learn from: a story README, a numbered learning path, readable sources, and the build history moved out of the way.

**Architecture:** Documentation and file moves only, plus two small code additions (a register-to-Markdown export and a headline figure) and a link-checking test. The model, pipeline and results do not change.

**Tech Stack:** Markdown (GitHub-rendered, Mermaid diagrams), Python 3.11, pandas, matplotlib, pytest, Snakemake 7.32 (pypsa-earth conda env).

**Spec:** `docs/project-history/specs/2026-10-28-reader-guide-design.md`

## Global Constraints

- No number, source or claim outside `results/*.csv`, `data/assumptions_register.xlsx` and existing docs; new context facts get a register row with a source URL.
- Voice: a curious engineering student, first person, playful but never hype; no emoji walls.
- No AI or tool attribution in any tracked file or commit; commits as RayenRomdhani with the noreply email; no push without approval.
- Paths code relies on stay valid: `Snakefile`, `config/`, `data/`, `src/`, `results/`, `tests/`.
- Licence: code MIT; text, figures, report and slides CC BY 4.0.
- Every task ends with `python -m pytest -q` passing.

## Review Focus

1. A relative Markdown link that points to a moved or missing file: GitHub shows a 404. Pinned by `tests/test_docs_links.py::test_relative_links_resolve` (Task 1).
2. A tool or AI product name left in a tracked file. Pinned by `tests/test_docs_links.py::test_no_tool_attribution` (Task 1).
3. The Markdown register drifting from the Excel source after someone edits one of them. Pinned by `tests/test_register_export.py::test_markdown_register_matches_excel` (Task 3).
4. A script moved to `scripts/dev/` that still imports or is referenced by its old path. Checked by grep plus `snakemake -n` in Task 2.
5. A Mermaid block GitHub cannot render (syntax error): checked by keeping diagrams to plain `flowchart LR` nodes and edges, and viewing them in the browser pane after writing (Task 7).

---

### Task 1: Move the build history out of the way

**Files:**
- Move (git mv): `docs/phase1-toy-model.md`, `docs/phase2-base-network.md`, `docs/phase3-validation.md`, `docs/phase4-scenarios.md`, `docs/plan.md`, `docs/config-changes.md`, `docs/evidence/` -> `docs/project-history/`; the original design spec -> `docs/project-history/specs/`
- Create: `docs/project-history/README.md` (what this folder is: the build log, phase by phase, with links)
- Modify: every file that links to a moved path (find with grep); tool names in moved docs reworded to neutral descriptions
- Test: `tests/test_docs_links.py`

- [ ] **Step 1: Write the failing tests**
```python
def test_relative_links_resolve():  # every [text](relative/path) in tracked .md files points to an existing file
    assert broken_links() == []
def test_no_tool_attribution():     # no tracked text file names an AI product or the skill library
    assert files_naming_tools() == []
```
`broken_links()` walks `git ls-files '*.md'`, extracts `](target)` links that are not `http(s):`, `#anchors` or `mailto:`, strips `#fragment` and `:line`, and resolves relative to the file. `files_naming_tools()` greps tracked text files (excluding `.gitignore`) for AI product and tool-library names, case-insensitively.
- [ ] **Step 2:** Run `pytest tests/test_docs_links.py -v`. Expected: FAIL (plan.md names skills; the new spec path is not yet linked anywhere but existing links are fine before the move).
- [ ] **Step 3:** `git mv` the files; write `docs/project-history/README.md`; fix every link and pointer (`src/tn2030/*.py` docstrings, `config/*.yaml` comments, `scripts/*.py` text, README, skill); reword tool names.
- [ ] **Step 4:** Run `pytest -q`. Expected: all pass.
- [ ] **Step 5:** Commit `docs: move the build history into docs/project-history`.

### Task 2: Separate one-off helpers from the scripts readers run

**Files:** Move `scripts/peak_ram.py`, `scripts/inspect_base.py`, `scripts/phase1_toy_model.py` -> `scripts/dev/`; update references (grep).
- [ ] **Step 1:** `git mv`; update references; any `parents[1]` path logic in moved scripts becomes `parents[2]`.
- [ ] **Step 2:** Run `python scripts/dev/phase1_toy_model.py --help` or a dry import check, `snakemake -n` (expected: nothing to do), `pytest -q`.
- [ ] **Step 3:** Commit `chore: move one-off helper scripts to scripts/dev`.

### Task 3: Make the sources readable on GitHub

**Files:**
- Modify: `src/tn2030/register.py` (add `register_markdown(path: Path) -> str`)
- Create: `scripts/export_register.py` (writes `data/assumptions_register.md`), `data/assumptions_register.md`
- Test: `tests/test_register_export.py`

**Interfaces:** Produces `register_markdown(path) -> str`: a Markdown document with a short header and one table (columns id, parameter, value, unit, type, source as `[source_title](source_url)` or the title alone, notes), rows in register order, `|` in cells escaped.

- [ ] **Step 1: Failing tests**
```python
def test_markdown_register_matches_excel():
    assert (ROOT / "data/assumptions_register.md").read_text(encoding="utf-8") == register_markdown(REGISTER)
def test_register_markdown_links_sources():
    md = register_markdown(REGISTER)
    assert "| demand_2024_twh |" in md and "](http" in md
```
- [ ] **Step 2:** Run; expected FAIL (function missing).
- [ ] **Step 3:** Implement; write the exporter; generate the file.
- [ ] **Step 4:** Run `pytest -q`; expected PASS.
- [ ] **Step 5:** Commit `feat: export the assumptions register as a readable Markdown table`.

### Task 4: Research the context facts

**Files:** Modify `data/assumptions_register.xlsx` (new `sourced` rows, each with URL and access date), regenerate `data/assumptions_register.md`, note sources in `data/raw/SOURCES.md` if a document was read.
- [ ] **Step 1:** Find public, citable sources for: how much of Tunisia's gas comes from Algeria (domestic production vs imports), STEG's role (single buyer/grid operator), and why 2030 (the national plan the 35% target belongs to). Read pages only; ask before downloading any file over a few MB.
- [ ] **Step 2:** Add only facts with a source; anything not confirmed is left out (not labelled as assumption: context is optional).
- [ ] **Step 3:** Run `python scripts/export_register.py`, `pytest -q`. Commit `data: add sourced context on Tunisia's gas supply and power sector`.

### Task 5: Headline figure

**Files:** Modify `scripts/make_figures.py` (add `headline(avoided_df)` writing `results/figures/0_headline.png`).
- [ ] **Step 1:** Implement: four large numbers for S1-15 (cost EUR, gas MWh, CO2 t per MWh saved; capacity MW per TWh saved per year), each with its unit and a one-line label, read from `avoided.csv`; same footer as other figures.
- [ ] **Step 2:** Run `python scripts/make_figures.py`; open the PNG and check text fits.
- [ ] **Step 3:** Commit `feat: add a headline figure`.

### Task 6: The learning path

**Files:** Create `docs/learn/01-the-problem.md` ... `07-try-it-yourself.md`, `docs/learn/glossary.md`.
- [ ] **Step 1:** Write chapters 01-06 (voice per spec; each ends with "Next:" link; terms link to the glossary; numbers only from the allowed sources).
- [ ] **Step 2:** Chapter 07 exercise: copy `config/scenarios/S1-15.yaml` to a new scenario with a 12% saving, run `snakemake -j 1 results/networks/<name>_solved.nc` on the D: base network, read its avoided metrics with a short snippet, quote the real output; delete the exercise scenario afterwards so the 11-scenario results stay unchanged.
- [ ] **Step 3:** Write the glossary.
- [ ] **Step 4:** `pytest -q` (link test covers the new files). Commit `docs: add the learning path`.

### Task 7: Story README, folder guides, licence, citation

**Files:** Rewrite `README.md`; create `results/README.md`, `data/README.md`, `config/README.md`, `src/tn2030/README.md`, `LICENSE` (MIT), `LICENSE-docs.md` (CC BY 4.0 notice), `CITATION.cff`.
- [ ] **Step 1:** README in the spec's story order with the headline figure and a Mermaid `flowchart LR` of the pipeline.
- [ ] **Step 2:** Folder guides (what each file is, one line each).
- [ ] **Step 3:** Licence files and `CITATION.cff` (cff-version 1.2.0; title; author Rayen Romdhani; repository-code URL; date-released 2026-10-28; license MIT).
- [ ] **Step 4:** Plain-language pass on README and chapters; view README and one chapter in the browser pane to check Mermaid renders (or note it cannot be checked offline).
- [ ] **Step 5:** `pytest -q`. Commit `docs: tell the study as a story and add folder guides, licence and citation`.

### Task 8: Regenerate, review, verify

- [ ] **Step 1:** Regenerate report and deck (paths cited in their text); validate both.
- [ ] **Step 2:** Code review of the branch by a fresh reviewer; fix findings.
- [ ] **Step 3:** Fresh clean-clone `pytest`; grep for tool names; commit.
