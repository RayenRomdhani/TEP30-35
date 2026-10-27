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
