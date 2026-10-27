"""Phase 1 single-node toy model of Tunisia (illustrative inputs, real cost data)."""


def annuity(rate: float, lifetime_years: float) -> float:
    """Share of an investment paid back each year over its lifetime (capital recovery factor)."""
    if rate == 0:
        return 1 / lifetime_years
    return rate / (1 - (1 + rate) ** -lifetime_years)


def annualised_capex(investment: float, fom_pct: float, lifetime_years: float, rate: float) -> float:
    """Yearly cost of one unit of capacity: annuity of the investment plus fixed O&M (FOM, % of investment)."""
    return investment * (annuity(rate, lifetime_years) + fom_pct / 100)
