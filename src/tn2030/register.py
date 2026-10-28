"""Read the assumptions register: the single source of every input number."""

from pathlib import Path

import pandas as pd

REGISTER_COLUMNS: tuple[str, ...] = (
    "id", "parameter", "value", "unit", "type",
    "source_title", "source_url", "accessed", "notes",
)

# "pending" rows are placeholders still to be sourced; code asking for them fails with KeyError.
USABLE_TYPES = {"sourced", "assumption"}


def load_register(path: Path) -> dict[str, float]:
    """Return {id: value} for every sourced or assumption row of the register."""
    df = pd.read_excel(path, sheet_name="register")

    duplicates = df["id"][df["id"].duplicated()].tolist()
    if duplicates:
        raise ValueError(f"duplicate ids in register: {duplicates}")

    usable = df[df["type"].isin(USABLE_TYPES)]

    # A "sourced" number without a link is not sourced: refuse it.
    sourced = usable[usable["type"] == "sourced"]
    # astype(str): an all-empty column is read as float NaN, which has no .str accessor.
    missing_url = sourced["id"][sourced["source_url"].fillna("").astype(str).str.strip() == ""].tolist()
    if missing_url:
        raise ValueError(f"sourced rows without source_url: {missing_url}")

    # A usable row must carry a number, otherwise NaN would flow silently into the model.
    no_value = usable["id"][usable["value"].isna()].tolist()
    if no_value:
        raise ValueError(f"rows without a value (fill it or mark them pending): {no_value}")

    return {row.id: float(row.value) for row in usable.itertuples()}


MARKDOWN_HEADER = """# Assumptions register

Every input number of the study, with its unit and where it comes from. This page is generated from
`assumptions_register.xlsx` by `scripts/export_register.py`: edit the Excel file, then rerun the script
(a test fails if the two differ).

- **sourced**: taken from the linked source.
- **assumption**: no published source; the notes say why the value was chosen.
- **pending**: placeholder, not used by the model.

"""


def _cell(value) -> str:
    """One table cell as text: numbers compact, empty cells blank, pipes escaped so the table holds."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    if isinstance(value, float):
        return f"{value:,.0f}" if abs(value) >= 1000 else f"{value:.4g}"
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%d")
    return str(value).replace("|", "\\|").replace("\n", " ")


def register_markdown(path: Path) -> str:
    """The whole register as a Markdown table, the source title linked to its URL."""
    df = pd.read_excel(path, sheet_name="register")
    lines = ["| id | parameter | value | unit | type | source | accessed | notes |",
             "|---|---|---|---|---|---|---|---|"]
    for r in df.itertuples():
        title, url = _cell(r.source_title), _cell(r.source_url)
        source = f"[{title or url}]({url})" if url else title
        value = str(int(r.value)) if r.unit == "year" else _cell(r.value)  # 1962, not 1,962
        lines.append("| " + " | ".join([_cell(r.id), _cell(r.parameter), value, _cell(r.unit),
                                        _cell(r.type), source, _cell(r.accessed), _cell(r.notes)]) + " |")
    return MARKDOWN_HEADER + "\n".join(lines) + "\n"
