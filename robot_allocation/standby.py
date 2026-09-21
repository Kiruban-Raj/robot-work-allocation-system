from .domain import AllocationResult, Inventory
from .errors import InsufficientCapacityError, InvalidInputError, NoRobotsAvailableError
from .solver import min_weight_cover
from .strategies import AllocationStrategy, CostOptimalStrategy


class StandbyActivationService:
    """Level 3: cover a client's hours from the active fleet first, and only
    wake up standby robots - picking the cheapest combination - to close
    whatever gap remains."""

    def __init__(self, active_strategy: AllocationStrategy = None):
        self._active_strategy = active_strategy or CostOptimalStrategy()

    def allocate(self, active: Inventory, standby: Inventory, requested_hours: int) -> AllocationResult:
        if requested_hours <= 0:
            raise InvalidInputError()
        if active.is_empty() and standby.is_empty():
            raise NoRobotsAvailableError()

        active_capacity = active.total_hours()
        if active_capacity >= requested_hours:
            return self._active_strategy.allocate(active, requested_hours)

        deficit = requested_hours - active_capacity
        active_used = {t: n for t, n in active.as_dict().items() if n > 0}

        cover = min_weight_cover(standby, deficit, weight_fn=lambda t: t.cost)
        if cover is None:
            raise InsufficientCapacityError()

        return AllocationResult(counts=active_used, standby_counts=cover.counts)
