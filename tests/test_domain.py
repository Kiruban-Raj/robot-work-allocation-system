import pytest

from robot_allocation.domain import BRAVO, CHARLIE, DELTA, AllocationResult, Inventory


def test_inventory_defaults_to_zero_for_every_type():
    inventory = Inventory()
    assert inventory.count(BRAVO) == 0
    assert inventory.count(CHARLIE) == 0
    assert inventory.count(DELTA) == 0
    assert inventory.is_empty()


def test_inventory_total_hours():
    inventory = Inventory({BRAVO: 2, CHARLIE: 3, DELTA: 2})
    assert inventory.total_hours() == 2 * 3 + 3 * 5 + 2 * 8


def test_inventory_rejects_negative_counts():
    with pytest.raises(ValueError):
        Inventory({BRAVO: -1})


def test_inventory_minus_returns_new_reduced_inventory():
    inventory = Inventory({BRAVO: 2, CHARLIE: 3, DELTA: 2})
    reduced = inventory.minus({BRAVO: 1, CHARLIE: 1})

    assert reduced.count(BRAVO) == 1
    assert reduced.count(CHARLIE) == 2
    assert reduced.count(DELTA) == 2
    # original untouched
    assert inventory.count(BRAVO) == 2


def test_inventory_minus_rejects_removing_more_than_available():
    inventory = Inventory({BRAVO: 1})
    with pytest.raises(ValueError):
        inventory.minus({BRAVO: 2})


def test_allocation_result_totals():
    result = AllocationResult(counts={BRAVO: 1, CHARLIE: 1}, standby_counts={DELTA: 1})
    assert result.total_hours == 3 + 5 + 8
    assert result.total_cost == 2 + 3 + 4
