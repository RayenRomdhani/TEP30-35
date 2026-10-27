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
    missing_url = sourced["id"][sourced["source_url"].fillna("").str.strip() == ""].tolist()
    if missing_url:
        raise ValueError(f"sourced rows without source_url: {missing_url}")

    return {row.id: float(row.value) for row in usable.itertuples()}
