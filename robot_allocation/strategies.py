from abc import ABC, abstractmethod
from typing import Tuple

from .domain import ALL_TYPES, AllocationResult, Inventory
from .errors import InsufficientCapacityError, InvalidInputError, NoRobotsAvailableError
from .solver import min_weight_cover


def _validate(inventory: Inventory, requested_hours: int) -> None:
    if requested_hours <= 0:
        raise InvalidInputError()
    if inventory.is_empty():
        raise NoRobotsAvailableError()


class AllocationStrategy(ABC):
    @abstractmethod
    def allocate(self, inventory: Inventory, requested_hours: int) -> AllocationResult:
        raise NotImplementedError


class DiversityFirstStrategy(AllocationStrategy):
    """Level 1: use at least one of every available category, then top up
    with whatever minimises leftover excess hours."""

    def allocate(self, inventory: Inventory, requested_hours: int) -> AllocationResult:
        _validate(inventory, requested_hours)

        base = {t: 1 for t in ALL_TYPES if inventory.count(t) > 0}
        base_hours = sum(t.hours * n for t, n in base.items())

        if base_hours >= requested_hours:
            return AllocationResult(counts=base)

        leftover_inventory = inventory.minus(base)
        remaining_needed = requested_hours - base_hours
        cover = min_weight_cover(leftover_inventory, remaining_needed, weight_fn=lambda t: t.hours)
        if cover is None:
            raise InsufficientCapacityError()

        final_counts = dict(base)
        for robot_type, amount in cover.counts.items():
            final_counts[robot_type] = final_counts.get(robot_type, 0) + amount
        return AllocationResult(counts=final_counts)


class CostOptimalStrategy(AllocationStrategy):
    """Level 2: ignore category diversity, minimise total charging cost."""

    def allocate(self, inventory: Inventory, requested_hours: int) -> AllocationResult:
        _validate(inventory, requested_hours)

        cover = min_weight_cover(inventory, requested_hours, weight_fn=lambda t: t.cost)
        if cover is None:
            raise InsufficientCapacityError()
        return AllocationResult(counts=cover.counts)


def compare_strategies(
    inventory: Inventory, requested_hours: int
) -> Tuple[AllocationResult, AllocationResult, int]:
    level1_result = DiversityFirstStrategy().allocate(inventory, requested_hours)
    level2_result = CostOptimalStrategy().allocate(inventory, requested_hours)
    return level1_result, level2_result, level1_result.total_cost - level2_result.total_cost
