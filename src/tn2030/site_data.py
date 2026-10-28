"""Small reshaping helpers for the website's data files (scripts/export_site_data.py)."""

import pandas as pd

HOURS_PER_YEAR = 8760


def hour_grid(series: pd.Series) -> list[list[int]]:
    """One year of hourly MW as 365 days x 24 hours of whole MW (the 3D landscape's height map)."""
    if len(series) != HOURS_PER_YEAR:
        raise ValueError(f"expected 8760 hourly values, got {len(series)}")
    values = series.round().astype(int).to_numpy()
    return values.reshape(365, 24).tolist()


def grid_lines(geojson: dict, country: str, decimals: int = 3) -> list[dict]:
    """Transmission lines of one country from an OpenStreetMap GeoJSON: voltage in kV and rounded lon/lat points."""
    out = []
    for feature in geojson["features"]:
        props, geom = feature["properties"], feature["geometry"]
        if props.get("country") != country or geom["type"] != "LineString":
            continue
        coords = [[round(lon, decimals), round(lat, decimals)] for lon, lat in geom["coordinates"]]
        out.append({"kv": round((props.get("voltage") or 0) / 1000), "c": coords})
    return out
