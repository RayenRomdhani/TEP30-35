from pathlib import Path

from tn2030.register import register_markdown

ROOT = Path(__file__).parents[1]
REGISTER = ROOT / "data" / "assumptions_register.xlsx"


def test_markdown_register_matches_excel():  # the readable copy must never drift from the Excel source
    md = (ROOT / "data" / "assumptions_register.md").read_text(encoding="utf-8")
    assert md == register_markdown(REGISTER), "run: python scripts/export_register.py"


def test_register_markdown_links_sources():
    md = register_markdown(REGISTER)
    assert "| demand_2024_twh |" in md and "](http" in md
    assert "| 1962 | year |" in md  # a year is not a quantity: no thousands separator


def test_register_markdown_escapes_pipes(tmp_path):  # a | inside a cell would split the table column
    import pandas as pd
    row = {"id": "x", "parameter": "a | b", "value": 1.0, "unit": "MW", "type": "assumption",
           "source_title": None, "source_url": None, "accessed": None, "notes": None}
    path = tmp_path / "reg.xlsx"
    pd.DataFrame([row]).to_excel(path, sheet_name="register", index=False)
    assert "a \\| b" in register_markdown(path)
