import matplotlib

matplotlib.use("Agg")  # no window: tests only draw into memory
import matplotlib.pyplot as plt
import pytest

from tn2030.plotting import PALETTE, annual_generation_twh, dispatch_by_carrier, finish_figure, load_weighted_price


def test_finish_figure_adds_source_footer():
    fig, ax = plt.subplots()
    finish_figure(fig, ax, "T", "GW", "Source: X")
    assert any("Source: X" in t.get_text() for t in fig.texts)
    plt.close(fig)


def test_finish_figure_sets_title_and_unit():
    fig, ax = plt.subplots()
    finish_figure(fig, ax, "Gas use", "TWh", "Source: X")
    assert ax.get_title(loc="left") == "Gas use" and ax.get_ylabel() == "TWh"
    plt.close(fig)


def test_palette_covers_all_carriers(solved_toy):
    assert set(solved_toy.generators.carrier) <= set(PALETTE)


def test_dispatch_by_carrier_matches_generation_plus_storage_output(solved_toy):
    n = solved_toy
    d = dispatch_by_carrier(n)
    expected = n.generators_t.p.sum(axis=1) + n.storage_units_t.p_dispatch.sum(axis=1)
    assert d.sum(axis=1).values == pytest.approx(expected.values)
    assert set(d.columns) <= set(PALETTE)


def test_dispatch_counts_pypsa_earth_battery_discharge(pe_battery_network):
    from tn2030.constraints import solve_network
    n = pe_battery_network
    solve_network(n, 0.35)
    discharger = n.links.index[n.links.carrier == "battery discharger"]
    assert dispatch_by_carrier(n)["battery"].values == pytest.approx(-n.links_t.p1[discharger].sum(axis=1).values)


def test_dispatch_handles_battery_not_built(pe_battery_network):  # PyPSA drops all-zero outputs from links_t
    from tn2030.constraints import solve_network
    n = pe_battery_network
    solve_network(n, 0.35)
    n.links_t.p1 = n.links_t.p1.drop(columns=n.links.index[n.links.carrier == "battery discharger"])
    assert (dispatch_by_carrier(n)["battery"] == 0).all()


def test_annual_generation_uses_snapshot_weightings(solved_toy):  # review focus 1: the toy has 3 h steps
    n = solved_toy
    twh = annual_generation_twh(n)
    hourly_sum = dispatch_by_carrier(n).sum().sum() / 1e6
    assert twh.sum() == pytest.approx(3 * hourly_sum)


def test_load_weighted_price_with_one_bus_is_the_bus_price(solved_toy):
    n = solved_toy
    assert load_weighted_price(n).values == pytest.approx(n.buses_t.marginal_price["TN"].values)
