"""Efficiency scenarios: cut demand uniformly, or put the same saving on the cooling load (spec D4, §5.2)."""

import pandas as pd

SHOULDER_MONTHS = (4, 5, 10, 11)  # little heating or cooling: the "no-cooling" baseline
SUMMER_MONTHS = (6, 7, 8, 9)


def uniform_cut(profile: pd.Series, share: float) -> pd.Series:
    """Every hour falls by the same share (main runs S1-10/15/20)."""
    return profile * (1 - share)


def cooling_component(profile: pd.Series) -> pd.Series:
    """Cooling load (MW) = summer load above the shoulder-month average for the same hour of day; 0 elsewhere."""
    shoulder = profile[profile.index.month.isin(SHOULDER_MONTHS)]
    if shoulder.empty:
        raise ValueError("cooling_component needs shoulder months (Apr, May, Oct, Nov) to build its baseline")
    baseline = shoulder.groupby(shoulder.index.hour).mean()  # MW by hour of day
    excess = (profile - baseline.reindex(profile.index.hour).to_numpy()).clip(lower=0)
    return excess.where(profile.index.month.isin(SUMMER_MONTHS), 0.0)


def cooling_weighted_cut(profile: pd.Series, weights: pd.Series, share: float) -> tuple[pd.Series, float]:
    """Save `share` of annual energy, first from the cooling load, the rest uniformly (sensitivity S1-15C).

    Returns the new profile and the fraction of the saving that could be placed on cooling.
    """
    saving = share * (profile * weights).sum()  # MWh to save
    if saving == 0:
        return profile.copy(), 0.0
    cooling = cooling_component(profile)
    cooling_mwh = (cooling * weights).sum()
    on_cooling = min(saving, cooling_mwh)
    out = profile - (cooling * on_cooling / cooling_mwh if cooling_mwh > 0 else 0.0)
    rest = saving - on_cooling  # cooling too small: cut the remainder uniformly
    if rest > 0:
        out = out * (1 - rest / (out * weights).sum())
    return out, on_cooling / saving
