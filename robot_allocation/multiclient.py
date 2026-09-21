import re
from typing import List, Tuple

from .domain import ClientAllocation, Inventory
from .errors import InsufficientCapacityError, InvalidInputError
from .standby import StandbyActivationService

_SEPARATORS = re.compile(r"[,\s]+")


def parse_client_hours(raw: str) -> List[int]:
    tokens = [tok for tok in _SEPARATORS.split(raw.strip()) if tok]
    if not tokens:
        raise InvalidInputError()

    hours = []
    for token in tokens:
        try:
            value = int(token)
        except ValueError:
            raise InvalidInputError()
        if value <= 0:
            raise InvalidInputError()
        hours.append(value)
    return hours


class MultiClientAllocator:
    """Level 4: serve several clients from one shared pool, highest request
    first, skipping (not aborting) any client that can't be fulfilled."""

    def __init__(self, standby_service: StandbyActivationService = None):
        self._standby_service = standby_service or StandbyActivationService()

    def allocate_all(
        self, active: Inventory, standby: Inventory, hours_list: List[int]
    ) -> Tuple[List[ClientAllocation], Inventory, Inventory]:
        priority_order = sorted(enumerate(hours_list), key=lambda pair: pair[1], reverse=True)

        results_by_index = {}
        remaining_active = active
        remaining_standby = standby

        for index, hours in priority_order:
            try:
                result = self._standby_service.allocate(remaining_active, remaining_standby, hours)
            except InsufficientCapacityError as exc:
                results_by_index[index] = ClientAllocation(requested_hours=hours, error=str(exc))
                continue

            remaining_active = remaining_active.minus(result.counts)
            remaining_standby = remaining_standby.minus(result.standby_counts)
            results_by_index[index] = ClientAllocation(requested_hours=hours, result=result)

        ordered_results = [results_by_index[i] for i in range(len(hours_list))]
        return ordered_results, remaining_active, remaining_standby
