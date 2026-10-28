# data/

The inputs. Every number the model uses comes from here.

| File | What it is |
|---|---|
| [`assumptions_register.md`](assumptions_register.md) | **Start here.** Every input number with its unit, type (sourced or assumption) and linked source, readable on GitHub |
| `assumptions_register.xlsx` | The same register as an Excel file: the one the code reads. Edit this one, then run `python scripts/export_register.py` |
| [`committed_projects.csv`](committed_projects.csv) | Solar and wind projects under construction or contracted, which the model must build, each with its source |
| [`raw/SOURCES.md`](raw/SOURCES.md) | Where the downloaded source documents came from (the documents themselves are not stored here) |

Rule of the project: no number without a source. A value with no published source is typed `assumption` and explained in the notes.
