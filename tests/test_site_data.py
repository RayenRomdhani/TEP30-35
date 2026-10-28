import pandas as pd
import pytest

from tn2030.site_data import grid_lines, hour_grid


def hourly(values, start="2013-01-01"):
    return pd.Series(values, index=pd.date_range(start, periods=len(values), freq="h"))


def test_hour_grid_is_days_by_hours():
    s = hourly(range(8760))
    grid = hour_grid(s)
    assert len(grid) == 365 and all(len(day) == 24 for day in grid)
    assert grid[1][0] == 24 and grid[364][23] == 8759  # day 2 starts at hour 24; last value at the end


def test_hour_grid_rounds_to_whole_mw():
    assert hour_grid(hourly([1.6] * 8760))[0][0] == 2


def test_hour_grid_refuses_other_lengths():  # a 3-hour network or a leap year would silently misplace hours
    with pytest.raises(ValueError, match="8760"):
        hour_grid(hourly(range(2920)))


def test_grid_lines_keeps_country_and_rounds():
    geo = {"features": [
        {"geometry": {"type": "LineString", "coordinates": [[10.123456, 36.987654], [10.2, 36.9]]},
         "properties": {"country": "TN", "voltage": 225000}},
        {"geometry": {"type": "LineString", "coordinates": [[7.0, 10.0], [7.1, 10.1]]},
         "properties": {"country": "NG", "voltage": 330000}},
    ]}
    lines = grid_lines(geo, "TN", decimals=3)
    assert lines == [{"kv": 225, "c": [[10.123, 36.988], [10.2, 36.9]]}]
