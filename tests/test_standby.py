import pytest

from robot_allocation.domain import BRAVO, CHARLIE, DELTA, Inventory
from robot_allocation.errors import InsufficientCapacityError, NoRobotsAvailableError
from robot_allocation.standby import StandbyActivationService


def test_deck_example_activates_cheapest_standby_option():
    active = Inventory({BRAVO: 1, CHARLIE: 1, DELTA: 1})  # 16h capacity
    standby = Inventory({BRAVO: 5, CHARLIE: 5, DELTA: 5})

    result = StandbyActivationService().allocate(active, standby, 21)

    assert result.counts == {BRAVO: 1, CHARLIE: 1, DELTA: 1}
    assert result.standby_counts == {CHARLIE: 1}
    assert result.total_hours == 21
    assert result.total_cost == 9 + 3


def test_no_standby_needed_when_active_capacity_suffices():
    active = Inventory({BRAVO: 1, CHARLIE: 1, DELTA: 1})
    standby = Inventory({BRAVO: 5})

    result = StandbyActivationService().allocate(active, standby, 10)

    assert result.standby_counts == {}


def test_insufficient_even_with_standby():
    active = Inventory({BRAVO: 1})
    standby = Inventory({BRAVO: 1})

    with pytest.raises(InsufficientCapacityError):
        StandbyActivationService().allocate(active, standby, 100)


def test_raises_when_both_fleets_empty():
    with pytest.raises(NoRobotsAvailableError):
        StandbyActivationService().allocate(Inventory(), Inventory(), 10)
