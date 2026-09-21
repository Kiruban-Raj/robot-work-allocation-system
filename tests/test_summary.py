from robot_allocation.domain import BRAVO, CHARLIE, DELTA, Inventory
from robot_allocation.multiclient import MultiClientAllocator
from robot_allocation.summary import SummaryReport


def test_summary_totals_and_utilization():
    active = Inventory({BRAVO: 2, CHARLIE: 2, DELTA: 2})
    standby = Inventory()

    results, _, _ = MultiClientAllocator().allocate_all(active, standby, [3, 5])

    report = SummaryReport.from_results(results, active, standby)

    total_used = sum(report.total_robots_used.values())
    assert total_used == 2  # one robot per client
    assert report.total_charging_cost == sum(
        client.result.total_cost for client in results if client.success
    )
    assert 0 <= report.avg_robot_utilization <= 100
    assert all(0 <= pct <= 100 for pct in report.category_utilization.values())


def test_utilization_is_zero_when_a_category_is_never_available():
    active = Inventory({BRAVO: 2, CHARLIE: 0, DELTA: 0})
    standby = Inventory()

    results, _, _ = MultiClientAllocator().allocate_all(active, standby, [3])
    report = SummaryReport.from_results(results, active, standby)

    assert report.category_utilization[CHARLIE] == 0.0
    assert report.category_utilization[DELTA] == 0.0
