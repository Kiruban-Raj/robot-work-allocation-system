import argparse
import sys
from typing import List

from .domain import ALL_TYPES, AllocationResult, Inventory
from .errors import AllocationError
from .multiclient import MultiClientAllocator, parse_client_hours
from .standby import StandbyActivationService
from .strategies import CostOptimalStrategy, DiversityFirstStrategy, compare_strategies
from .summary import SummaryReport


# ---------------------------------------------------------------------------
# Interactive prompts
# ---------------------------------------------------------------------------

def _prompt_robot_count(label: str) -> int:
    while True:
        raw = input(label).strip()
        try:
            value = int(raw)
        except ValueError:
            print("Error: Robot counts must be non-negative integers.")
            continue
        if value < 0:
            print("Error: Robot counts must be non-negative integers.")
            continue
        return value


def _read_inventory_interactive() -> Inventory:
    print("Enter number of robots available:")
    counts = {t: _prompt_robot_count(f"{t.name}: ") for t in ALL_TYPES}
    return Inventory(counts)


def _prompt_client_hours() -> List[int]:
    while True:
        raw = input("\nEnter client work hours:\n")
        try:
            return parse_client_hours(raw)
        except AllocationError as exc:
            print(str(exc))


def _prompt_yes_no(label: str) -> bool:
    return input(label).strip().lower() in ("y", "yes")


def run_interactive() -> int:
    try:
        active = _read_inventory_interactive()
        hours_list = _prompt_client_hours()

        if len(hours_list) > 1:
            standby = Inventory()
            if _prompt_yes_no("\nDo any clients need standby robots activated? (y/n): "):
                print("\nEnter number of standby robots available:")
                standby = Inventory({t: _prompt_robot_count(f"{t.name}: ") for t in ALL_TYPES})
            _run_multi_client(active, standby, hours_list, show_summary=True)
            return 0

        requested_hours = hours_list[0]
        level1_result, level2_result, cost_difference = compare_strategies(active, requested_hours)
        _print_level1_result(level1_result, requested_hours)
        _print_level2_result(level2_result, requested_hours)
        _print_comparison(level1_result, level2_result, cost_difference)

        active_capacity = active.total_hours()
        if active_capacity < requested_hours:
            print("\nActive capacity is insufficient - checking standby robots.")
            print("\nEnter number of standby robots available:")
            standby = Inventory({t: _prompt_robot_count(f"{t.name}: ") for t in ALL_TYPES})
            standby_result = StandbyActivationService().allocate(active, standby, requested_hours)
            _print_standby_result(standby_result, active_capacity, requested_hours)

        return 0
    except AllocationError as exc:
        print(str(exc))
        return 1


# ---------------------------------------------------------------------------
# Non-interactive (flags) entry point
# ---------------------------------------------------------------------------

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="EverBot Solutions robot work allocation system")
    parser.add_argument("--bravo", type=int, default=0)
    parser.add_argument("--charlie", type=int, default=0)
    parser.add_argument("--delta", type=int, default=0)
    parser.add_argument("--standby-bravo", type=int, default=0)
    parser.add_argument("--standby-charlie", type=int, default=0)
    parser.add_argument("--standby-delta", type=int, default=0)
    parser.add_argument("--hours", type=str, help="single value, or comma/space separated list")
    parser.add_argument("--level", type=int, choices=[1, 2, 3, 4])
    parser.add_argument("--summary", action="store_true", help="print the bonus allocation summary")
    return parser


def _inventories_from_args(args: argparse.Namespace):
    active = Inventory({
        ALL_TYPES[0]: args.bravo,
        ALL_TYPES[1]: args.charlie,
        ALL_TYPES[2]: args.delta,
    })
    standby = Inventory({
        ALL_TYPES[0]: args.standby_bravo,
        ALL_TYPES[1]: args.standby_charlie,
        ALL_TYPES[2]: args.standby_delta,
    })
    return active, standby


def run_non_interactive(args: argparse.Namespace) -> int:
    try:
        active, standby = _inventories_from_args(args)
        hours_list = parse_client_hours(args.hours)

        if len(hours_list) > 1 or args.level == 4:
            _run_multi_client(active, standby, hours_list, show_summary=args.summary)
            return 0

        requested_hours = hours_list[0]

        if args.level == 1:
            result = DiversityFirstStrategy().allocate(active, requested_hours)
            _print_level1_result(result, requested_hours)
        elif args.level == 2:
            result = CostOptimalStrategy().allocate(active, requested_hours)
            _print_level2_result(result, requested_hours)
        elif args.level == 3:
            result = StandbyActivationService().allocate(active, standby, requested_hours)
            _print_standby_result(result, active.total_hours(), requested_hours)
        else:
            level1_result, level2_result, cost_difference = compare_strategies(active, requested_hours)
            _print_level1_result(level1_result, requested_hours)
            _print_level2_result(level2_result, requested_hours)
            _print_comparison(level1_result, level2_result, cost_difference)
            if not standby.is_empty():
                standby_result = StandbyActivationService().allocate(active, standby, requested_hours)
                _print_standby_result(standby_result, active.total_hours(), requested_hours)

        return 0
    except AllocationError as exc:
        print(str(exc))
        return 1


def _run_multi_client(active: Inventory, standby: Inventory, hours_list: List[int], show_summary: bool) -> None:
    results, _final_active, _final_standby = MultiClientAllocator().allocate_all(active, standby, hours_list)

    for client in results:
        print(f"\nClient work hours requested: {client.requested_hours}")
        if not client.success:
            print(client.error)
            continue
        _print_client_allocation(client.result)

    if show_summary:
        report = SummaryReport.from_results(results, active, standby)
        _print_summary(report)


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def _print_counts(result: AllocationResult) -> None:
    for robot_type in ALL_TYPES:
        amount = result.counts.get(robot_type, 0)
        if amount:
            print(f"{robot_type.name}: {amount}")


def _print_level1_result(result: AllocationResult, requested_hours: int) -> None:
    print("\nRobot Assignment")
    _print_counts(result)
    print(f"\nTotal Work Hours Provided: {result.total_hours}")
    print(f"Client Work Hours Requested: {requested_hours}")


def _print_level2_result(result: AllocationResult, requested_hours: int) -> None:
    print("\nCost Optimized Allocation")
    _print_counts(result)
    print(f"\nTotal Hours Provided: {result.total_hours}")
    print(f"Total Charging Cost: ${result.total_cost}")


def _print_comparison(level1_result: AllocationResult, level2_result: AllocationResult, cost_difference: int) -> None:
    print("\nLevel 1 vs Level 2 Comparison")
    print(f"Level 1 Cost: ${level1_result.total_cost}")
    print(f"Level 2 Cost: ${level2_result.total_cost}")
    print(f"Cost Difference: ${cost_difference}")
    if cost_difference > 0:
        print(
            f"\nInsight: Level 1 strategy resulted in ${cost_difference} additional cost due to "
            "mandatory usage of multiple robot categories."
        )
    else:
        print("\nInsight: Both strategies produced the same cost for this input.")


def _print_standby_result(result: AllocationResult, active_capacity: int, requested_hours: int) -> None:
    print(f"\nActive Robot Capacity: {active_capacity} hours")
    print(f"Client Work Requested: {requested_hours} hours")
    if result.standby_counts:
        print("\nAdditional Standby Robots Required:")
        for robot_type in ALL_TYPES:
            amount = result.standby_counts.get(robot_type, 0)
            if amount:
                print(f"{robot_type.name}: {amount} - cost ${robot_type.cost * amount}")
    else:
        print("\nNo standby robots required.")
    print(f"\nTotal Hours Provided: {result.total_hours}")
    print(f"Total Charging Cost: ${result.total_cost}")


def _print_client_allocation(result: AllocationResult) -> None:
    print("Active robots used:")
    _print_counts(result)
    if result.standby_counts:
        print("Standby robots activated:")
        for robot_type in ALL_TYPES:
            amount = result.standby_counts.get(robot_type, 0)
            if amount:
                print(f"{robot_type.name}: {amount}")
    print(f"Total Hours Provided: {result.total_hours}")
    print(f"Total Charging Cost: ${result.total_cost}")


def _print_summary(report: SummaryReport) -> None:
    print("\nAllocation Summary")
    print(f"Total Robots Used: {sum(report.total_robots_used.values())}")
    for robot_type in ALL_TYPES:
        print(f"  {robot_type.name}: {report.total_robots_used.get(robot_type, 0)}")
    print(f"Total Charging Cost: ${report.total_charging_cost}")
    print(f"Avg Robot Utilization: {report.avg_robot_utilization:.1f}%")

    print("\nEfficiency Metrics")
    for robot_type in ALL_TYPES:
        print(f"{robot_type.name} utilization: {report.category_utilization.get(robot_type, 0):.1f}%")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: List[str] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    if args.hours is None:
        return run_interactive()
    return run_non_interactive(args)


if __name__ == "__main__":
    sys.exit(main())
