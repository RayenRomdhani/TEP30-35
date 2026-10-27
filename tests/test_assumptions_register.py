import pandas as pd
import pytest

from tn2030.register import REGISTER_COLUMNS, load_register


def _write_register(path, rows):
    """Write a minimal register workbook with the given rows."""
    df = pd.DataFrame(rows, columns=REGISTER_COLUMNS)
    df.to_excel(path, sheet_name="register", index=False)
    return path


def _row(id_, value, type_, url="https://example.org/source"):
    return {
        "id": id_, "parameter": id_, "value": value, "unit": "-", "type": type_,
        "source_title": "Example", "source_url": url, "accessed": "2026-10-27", "notes": "",
    }


def test_load_register_returns_sourced_and_assumption_rows(tmp_path):
    path = _write_register(tmp_path / "reg.xlsx", [
        _row("re_target_2030", 0.35, "sourced"),
        _row("flex_max_hours", 3, "assumption", url=""),
    ])
    reg = load_register(path)
    assert reg == {"re_target_2030": 0.35, "flex_max_hours": 3.0}


def test_load_register_skips_pending_rows(tmp_path):
    path = _write_register(tmp_path / "reg.xlsx", [
        _row("re_target_2030", 0.35, "sourced"),
        _row("demand_2024_twh", None, "pending", url=""),
    ])
    reg = load_register(path)
    assert "demand_2024_twh" not in reg


def test_load_register_rejects_sourced_row_without_url(tmp_path):
    path = _write_register(tmp_path / "reg.xlsx", [_row("re_target_2030", 0.35, "sourced", url="")])
    with pytest.raises(ValueError, match="source_url"):
        load_register(path)


def test_load_register_rejects_duplicate_ids(tmp_path):
    path = _write_register(tmp_path / "reg.xlsx", [
        _row("re_target_2030", 0.35, "sourced"),
        _row("re_target_2030", 0.30, "sourced"),
    ])
    with pytest.raises(ValueError, match="duplicate"):
        load_register(path)
