from dataclasses import dataclass, field
from typing import Dict, List

from .domain import ALL_TYPES, ClientAllocation, Inventory, RobotType


@dataclass
class SummaryReport:
    total_robots_used: Dict[RobotType, int] = field(default_factory=dict)
    total_charging_cost: int = 0
    category_utilization: Dict[RobotType, float] = field(default_factory=dict)

    @property
    def avg_robot_utilization(self) -> float:
        if not self.category_utilization:
            return 0.0
        return sum(self.category_utilization.values()) / len(self.category_utilization)

    @classmethod
    def from_results(
        cls,
        results: List[ClientAllocation],
        original_active: Inventory,
        original_standby: Inventory,
    ) -> "SummaryReport":
        used = {t: 0 for t in ALL_TYPES}
        total_cost = 0

        for client in results:
            if not client.success:
                continue
            for robot_type, amount in client.result.counts.items():
                used[robot_type] += amount
            for robot_type, amount in client.result.standby_counts.items():
                used[robot_type] += amount
            total_cost += client.result.total_cost

        available = {t: original_active.count(t) + original_standby.count(t) for t in ALL_TYPES}
        utilization = {
            t: (used[t] / available[t] * 100) if available[t] else 0.0 for t in ALL_TYPES
        }

        return cls(total_robots_used=used, total_charging_cost=total_cost, category_utilization=utilization)
