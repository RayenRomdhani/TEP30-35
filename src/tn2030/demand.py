"""2030 demand: grow the 2024 total, scale the hourly shape, remove imports, check the peak (spec §5.1)."""

import pandas as pd


def annual_demand_2030(d2024_twh: float, growth: float, years: int = 6) -> float:
    """2030 demand (TWh) = 2024 demand grown at a constant yearly rate, 2024 -> 2030 is 6 years."""
    return d2024_twh * (1 + growth) ** years


def scale_profile(profile: pd.Series, weights: pd.Series, annual_total_mwh: float) -> pd.Series:
    """Rescale a load profile (MW) so its energy over the year equals annual_total_mwh. The shape is kept.

    weights = hours each snapshot stands for (n.snapshot_weightings.generators), so energy = sum(MW x h).
    """
    return profile * annual_total_mwh / (profile * weights).sum()


def reshape_profile(profile: pd.Series, weights: pd.Series, load_factor: float, min_to_peak: float) -> pd.Series:
    """Stretch a too-flat load profile to an official load factor and minimum/peak ratio (Phase 3 calibration).

    Every hour keeps its rank (the timing of peaks and troughs comes from the input), the annual energy is kept,
    and the new shape relative to the peak is  min_to_peak + (1 - min_to_peak) * x**k,  where x runs from 0 at the
    lowest hour to 1 at the highest. The exponent k is found by bisection so the weighted mean (= load factor) matches.
    """
    if not min_to_peak < load_factor < 1:
        raise ValueError(f"load factor {load_factor} must lie between min_to_peak {min_to_peak} and 1")
    x = (profile - profile.min()) / (profile.max() - profile.min())

    def shape(k):
        return min_to_peak + (1 - min_to_peak) * x**k

    def mean_over_peak(k):  # the load factor of shape(k); it falls as k grows
        return float((shape(k) * weights).sum() / weights.sum())

    lo, hi = 1e-3, 1e3
    for _ in range(100):  # bisection on a log scale
        mid = (lo * hi) ** 0.5
        lo, hi = (mid, hi) if mean_over_peak(mid) > load_factor else (lo, mid)
    return scale_profile(shape((lo * hi) ** 0.5), weights, (profile * weights).sum())


def subtract_imports(profile: pd.Series, weights: pd.Series, annual_imports_mwh: float) -> pd.Series:
    """Remove a flat import flow from the load: what is left must be served by domestic plants (spec D3)."""
    flat_mw = annual_imports_mwh / weights.sum()  # same MW in every hour of the year
    out = profile - flat_mw
    if (out < 0).any():
        raise ValueError(f"imports of {flat_mw:,.0f} MW make the domestic load negative at {out.idxmin()}")
    return out


def peak_check(profile: pd.Series, reference_mw: float, tolerance: float = 0.10) -> tuple[float, bool]:
    """Peak of the profile (MW) and whether it is within +-tolerance of a reference peak. A warning, not a hard fail."""
    peak = float(profile.max())
    return peak, abs(peak - reference_mw) <= tolerance * reference_mw
