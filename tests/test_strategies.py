import pytest

from robot_allocation.domain import BRAVO, CHARLIE, DELTA, Inventory
from robot_allocation.errors import InsufficientCapacityError, InvalidInputError, NoRobotsAvailableError
from robot_allocation.strategies import CostOptimalStrategy, DiversityFirstStrategy, compare_strategies


class TestDiversityFirstStrategy:
    def test_deck_example_16_hours(self):
        inventory = Inventory({BRAVO: 2, CHARLIE: 3, DELTA: 2})
        result = DiversityFirstStrategy().allocate(inventory, 16)

        assert result.counts == {BRAVO: 1, CHARLIE: 1, DELTA: 1}
        assert result.total_hours == 16

    @pytest.mark.parametrize(
        "requested_hours, extra_type",
        [
            (17, BRAVO),   # deficit 1h -> Bravo (least excess: 2h over)
            (24, DELTA),   # deficit 8h -> Delta (exact match, 0 excess)
            (21, CHARLIE),  # deficit 5h -> Charlie (exact match, 0 excess)
        ],
    )
    def test_deck_excess_minimisation_examples(self, requested_hours, extra_type):
        inventory = Inventory({BRAVO: 5, CHARLIE: 5, DELTA: 5})
        result = DiversityFirstStrategy().allocate(inventory, requested_hours)

        assert result.counts[BRAVO] >= 1 and result.counts[CHARLIE] >= 1 and result.counts[DELTA] >= 1
        assert result.total_hours >= requested_hours

        # the extra unit(s) beyond the mandatory one-of-each should have gone to `extra_type`
        base = {BRAVO: 1, CHARLIE: 1, DELTA: 1}
        top_up = {t: result.counts.get(t, 0) - base[t] for t in (BRAVO, CHARLIE, DELTA)}
        assert top_up[extra_type] > 0
        assert all(amount == 0 for t, amount in top_up.items() if t != extra_type)

    def test_best_effort_diversity_when_a_category_is_missing(self):
        inventory = Inventory({BRAVO: 3, CHARLIE: 0, DELTA: 0})
        result = DiversityFirstStrategy().allocate(inventory, 7)

        assert CHARLIE not in result.counts
        assert DELTA not in result.counts
        assert result.total_hours >= 7

    def test_raises_when_no_robots_available(self):
        with pytest.raises(NoRobotsAvailableError):
            DiversityFirstStrategy().allocate(Inventory(), 10)

    def test_raises_on_non_positive_hours(self):
        inventory = Inventory({BRAVO: 1})
        with pytest.raises(InvalidInputError):
            DiversityFirstStrategy().allocate(inventory, 0)

    def test_raises_when_capacity_insufficient(self):
        inventory = Inventory({BRAVO: 1})
        with pytest.raises(InsufficientCapacityError):
            DiversityFirstStrategy().allocate(inventory, 100)


class TestCostOptimalStrategy:
    def test_deck_example_1(self):
        inventory = Inventory({BRAVO: 2, CHARLIE: 3, DELTA: 2})
        result = CostOptimalStrategy().allocate(inventory, 20)

        assert result.counts == {CHARLIE: 1, DELTA: 2}
        assert result.total_hours == 21
        assert result.total_cost == 11

    def test_deck_example_2(self):
        inventory = Inventory({BRAVO: 2, CHARLIE: 2, DELTA: 3})
        result = CostOptimalStrategy().allocate(inventory, 6)

        assert result.counts == {BRAVO: 2}
        assert result.total_hours == 6
        assert result.total_cost == 4


class TestCompareStrategies:
    def test_deck_level1_vs_level2_comparison(self):
        inventory = Inventory({BRAVO: 2, CHARLIE: 3, DELTA: 2})
        level1_result, level2_result, cost_difference = compare_strategies(inventory, 20)

        assert level1_result.total_cost == 12
        assert level2_result.total_cost == 11
        assert cost_difference == 1
