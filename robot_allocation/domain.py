from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass(frozen=True)
class RobotType:
    name: str
    hours: int
    cost: int


BRAVO = RobotType("Bravo", 3, 2)
CHARLIE = RobotType("Charlie", 5, 3)
DELTA = RobotType("Delta", 8, 4)
ALL_TYPES = (BRAVO, CHARLIE, DELTA)


class Inventory:
    """Immutable snapshot of how many robots of each type are on hand."""

    def __init__(self, counts: Optional[Dict[RobotType, int]] = None):
        self._counts = {t: 0 for t in ALL_TYPES}
        if counts:
            for robot_type, amount in counts.items():
                if amount < 0:
                    raise ValueError(f"Robot count for {robot_type.name} cannot be negative")
                self._counts[robot_type] = amount

    def count(self, robot_type: RobotType) -> int:
        return self._counts[robot_type]

    def total_hours(self) -> int:
        return sum(t.hours * n for t, n in self._counts.items())

    def total_robots(self) -> int:
        return sum(self._counts.values())

    def is_empty(self) -> bool:
        return self.total_robots() == 0

    def minus(self, used: Dict[RobotType, int]) -> "Inventory":
        remaining = dict(self._counts)
        for robot_type, amount in used.items():
            if amount > remaining.get(robot_type, 0):
                raise ValueError(f"Cannot remove {amount} {robot_type.name} robots, only {remaining.get(robot_type, 0)} available")
            remaining[robot_type] -= amount
        return Inventory(remaining)

    def as_dict(self) -> Dict[RobotType, int]:
        return dict(self._counts)

    def __repr__(self) -> str:
        parts = ", ".join(f"{t.name}={n}" for t, n in self._counts.items())
        return f"Inventory({parts})"


@dataclass
class AllocationResult:
    counts: Dict[RobotType, int] = field(default_factory=dict)
    standby_counts: Dict[RobotType, int] = field(default_factory=dict)

    @property
    def total_hours(self) -> int:
        active = sum(t.hours * n for t, n in self.counts.items())
        standby = sum(t.hours * n for t, n in self.standby_counts.items())
        return active + standby

    @property
    def total_cost(self) -> int:
        active = sum(t.cost * n for t, n in self.counts.items())
        standby = sum(t.cost * n for t, n in self.standby_counts.items())
        return active + standby


@dataclass
class ClientAllocation:
    requested_hours: int
    result: Optional[AllocationResult] = None
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None
