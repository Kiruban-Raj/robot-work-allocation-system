"""
Generic bounded-knapsack "minimum weight cover" solver.

Given an inventory of robots and a target number of hours, find the
combination of robots whose combined hours are >= target, minimising a
caller-supplied weight function. Minimising cost gives Level 2's
cost-optimal strategy; minimising hours themselves gives Level 1's
minimum-excess strategy (since overshoot = total_hours - target, and
target is fixed, minimising total_hours minimises overshoot too).
"""
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional

from .domain import ALL_TYPES, Inventory, RobotType


@dataclass
class CoverResult:
    counts: Dict[RobotType, int] = field(default_factory=dict)
    total_hours: int = 0
    weight: float = 0.0


def min_weight_cover(
    inventory: Inventory,
    target_hours: int,
    weight_fn: Callable[[RobotType], float],
) -> Optional[CoverResult]:
    if target_hours <= 0:
        return CoverResult(counts={}, total_hours=0, weight=0.0)

    max_hours = inventory.total_hours()
    if max_hours < target_hours:
        return None

    infinity = float("inf")
    # State per reachable hour total: (weight, robot_count) plus the combo that produced it.
    # robot_count is a tie-breaker so that, e.g., one Delta (8h) is preferred over a
    # Bravo+Charlie combo (3h+5h) when both reach the same hours with the same weight.
    best_state = [(infinity, infinity)] * (max_hours + 1)
    best_counts = [None] * (max_hours + 1)
    best_state[0] = (0.0, 0)
    best_counts[0] = {}

    def is_better(candidate, current):
        weight_diff = candidate[0] - current[0]
        if weight_diff < -1e-9:
            return True
        if weight_diff > 1e-9:
            return False
        return candidate[1] < current[1]

    for robot_type in ALL_TYPES:
        available = inventory.count(robot_type)
        if available == 0:
            continue
        hours = robot_type.hours
        weight = weight_fn(robot_type)

        next_state = list(best_state)
        next_counts = list(best_counts)

        for reached in range(max_hours + 1):
            base_weight, base_count = best_state[reached]
            if base_weight == infinity:
                continue
            base_counts = best_counts[reached]
            for units in range(1, available + 1):
                new_hours = reached + hours * units
                if new_hours > max_hours:
                    break
                candidate = (base_weight + weight * units, base_count + units)
                if is_better(candidate, next_state[new_hours]):
                    next_state[new_hours] = candidate
                    combined = dict(base_counts)
                    combined[robot_type] = combined.get(robot_type, 0) + units
                    next_counts[new_hours] = combined

        best_state = next_state
        best_counts = next_counts

    # Picking which total-hours bucket to use only compares weight: less overshoot
    # is preferred over fewer robots when the two are in tension (e.g. two Bravos
    # covering 6h exactly beats one Delta covering 8h, even at equal cost).
    best_reached = None
    for hours in range(target_hours, max_hours + 1):
        weight = best_state[hours][0]
        if weight == infinity:
            continue
        if best_reached is None or weight < best_state[best_reached][0] - 1e-9:
            best_reached = hours

    if best_reached is None:
        return None

    return CoverResult(
        counts=best_counts[best_reached],
        total_hours=best_reached,
        weight=best_state[best_reached][0],
    )
