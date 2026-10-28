# Design: make the repository easy to learn from

Date: 2026-10-28. Branch: `reader-guide`. Author of the request: Rayen Romdhani.

## Intent

The repository works and is correct, but it reads like a lab notebook: the README opens on results full of codes (S1-15C, OCGT, MWh_th), the docs follow the order the study was built in (phase 1 to 4, a checkbox plan, run logs), and the sources sit in an Excel file GitHub cannot show.

The author wants an average engineering student or engineer to open the repo and:
1. first get the whole picture (Tunisia's power system, the 2030 target, what efficiency and flexibility are, the question being asked);
2. then understand the role of the model (what a least-cost model does, what PyPSA-Earth is, what this repo adds);
3. then the answer and how far to trust it.

It should feel "dramatic and interestingly cool", told in the voice of a curious engineering student (the author), not a consultancy report.

## Goals

- A newcomer understands the question, the method and the headline answer from the README alone in about 5 minutes.
- A learner who wants more follows a numbered path of short chapters, each ending with a link to the next.
- Every term is explained the first time it appears, and again in one glossary.
- Every scenario code appears next to a plain name.
- The sources can be read on GitHub without downloading anything.
- The build history stays available for anyone checking the work, but out of the reader's way.

## Non-goals

- No change to the model, the pipeline logic, the scenarios or any result number.
- No website, hosting or new tools: everything is GitHub-rendered Markdown, PNG figures and Mermaid diagrams, which GitHub renders natively.
- No rewrite of the report and slides beyond updating links.

## Anti-goals (failure even if it "works")

- Any number, source or claim that is not in `results/*.csv`, the register or the existing phase docs. Drama comes from structure and real numbers, never from invented or rounded-up facts.
- Hype words that overstate the study ("revolutionary", "proves", "will save Tunisia"). The study is a least-cost model, and the text says so.
- Broken links or a broken pipeline after files move.
- Cringe: forced jokes, emoji walls, memes. Playful means a confident, curious student voice with the odd light line, not a stand-up routine.

## Constraints

- Project rules stand: no invented data; simple, commented code; English; no AI or tool attribution anywhere; commits in the author's name; no push without approval.
- Paths used by code stay valid: `Snakefile`, `config/`, `data/`, `src/`, `results/`, `tests/`, and the scripts the README tells people to run.
- All tests keep passing; figures, report and deck regenerate from the same commands.

## The reader's path (decided with the author)

```
README.md  (5-minute story: hook -> question -> experiment -> answer -> twist -> fine print)
   |
   v
docs/learn/
  01-the-problem.md          Tunisia's electricity, gas, the 35% target, why 2030
  02-key-ideas.md            energy vs capacity, efficiency vs flexibility, merit order, reserve margin, CO2
  03-how-the-model-works.md  least-cost planning as a game with rules; PyPSA-Earth; what this repo adds; diagram
  04-the-experiment.md       the 11 scenarios in plain words; what is compared with what
  05-results.md              each figure, what to look at, what it means
  06-how-far-to-trust-it.md  validation against 2024, limitations, what would change the answer
  07-try-it-yourself.md      reproduce, then change one scenario and rerun (an exercise)
  glossary.md                every term, one or two lines each
```

## The README as a story (my call on structure, in the author's voice)

1. **Hook:** one line on the stakes with real numbers (94.5% of Tunisia's electricity from gas in 2024; a 35% renewable target for 2030; demand growing 3.2% a year).
2. **The question:** "If Tunisia uses one MWh less, what doesn't it have to buy or build?"
3. **The answer up front:** a headline graphic (new figure, numbers read from `avoided.csv`): 1 MWh saved = 60 EUR + 0.91 MWh of gas + 0.18 t CO2.
4. **Three findings that surprise:** the 423 MW of gas turbines a 10% saving avoids; saving at air-conditioning time beats saving evenly; the gas price flips what a saved MWh displaces.
5. **How we know:** a Mermaid diagram of the pipeline (open data -> PyPSA-Earth -> calibrated to 2024 -> 11 scenarios -> least-cost solve -> checks -> results), three sentences on what a least-cost model is.
6. **The fine print:** the three limitations that matter most, with a link to the full chapter.
7. **Go deeper:** the learning path, the report and slides, the skill, how to reproduce.
8. **Repo map, licence, citation.**

## Other changes

- **New headline figure** `results/figures/0_headline.png`: the four "avoided per MWh" numbers as a poster-style graphic, drawn by `scripts/make_figures.py` from `avoided.csv` (same palette and footer rules).
- **Readable register:** `scripts/export_register.py` writes `data/assumptions_register.md` (a Markdown table GitHub renders) from the Excel file; a test checks the Markdown matches the Excel so they cannot drift. The Excel stays the source.
- **Project history:** move `docs/phase*.md`, `docs/plan.md`, `docs/config-changes.md`, `docs/evidence/` and the existing design spec into `docs/project-history/` (with a short index explaining it is the build log). The old specs folder named after a tool disappears; tool names in the moved plan are reworded to neutral descriptions (e.g. "with a Word library").
- **Scripts:** keep the ones readers run (`make_figures`, `make_report`, `make_deck`, `validate_baseline`, `export_register`) in `scripts/`; move one-off helpers (`peak_ram.py`, `inspect_base.py`, `phase1_toy_model.py`) to `scripts/dev/`, updating every reference.
- **Folder guides:** a short `README.md` in `results/`, `data/`, `config/` and `src/tn2030/` saying what each file is.
- **Scenario names:** one table (in chapter 04 and the README) maps each code to a plain name; figure labels already carry a plain description.
- **Licence and citation:** a `LICENSE` file and a `CITATION.cff` (author name, title, year, repository URL).
- **Report and slides:** links updated to the new paths; regenerated only if their text references moved files.

## Decided by the author (2026-10-28, after the builder check)

- **Context research is allowed.** Chapters 01-02 and the README hook may use a handful of new facts about Tunisia's power sector (gas supply and imports, STEG's role, why 2030). Each new number gets a register row with its source URL (type `sourced`); qualitative statements cite their source inline. Reading public pages is fine; nothing large is downloaded without asking.
- **Licence:** code under MIT; text, figures, report and slides under CC BY 4.0. `LICENSE` holds MIT, `LICENSE-docs` (or a section) holds the CC BY 4.0 notice, and the README states which covers what. Third-party inputs keep their own terms (noted in the register and SOURCES).

## Builder's calls (settled without the author; check while reading)

- Results: chapters and the README use only numbers already in `results/*.csv`, `data/assumptions_register.xlsx` and the existing docs. No new solves, except the chapter 07 exercise below.
- Headline figure: cost, gas and CO2 are per MWh saved; capacity is shown in its own unit (MW per TWh saved per year) with that label.
- Chapter 07 exercise: the reader edits one scenario YAML (a copy of S1-15 with a different saving) and runs one Snakemake target. The builder runs that exact exercise on the D: base network and quotes only the real output.
- Repository URL: the current `github.com/RayenRomdhani/TEP30-35` (GitHub redirects after a rename).
- Tool names: removed from every moved history doc, not just the plan. The `skill/` folder stays (the author chose to publish it); its text names no AI product.
- Docstrings and config comments that point at moved docs are updated; the report and slides are regenerated because their text cites moved paths.

## Left to the builder

- Exact wording of each chapter, within the voice and anti-goals above.
- Which existing figures each chapter reuses.
- Mermaid diagram details.

## Open for the author (no work blocked)

- Repository name: "TEP30-35" says nothing about the topic. Renaming is done on GitHub by the author; suggested names go in the summary.
