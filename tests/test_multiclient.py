import pytest

from robot_allocation.domain import BRAVO, CHARLIE, DELTA, Inventory
from robot_allocation.errors import InvalidInputError
from robot_allocation.multiclient import MultiClientAllocator, parse_client_hours


class TestParseClientHours:
    def test_single_value(self):
        assert parse_client_hours("20") == [20]

    def test_comma_separated(self):
        assert parse_client_hours("12,16,17,10,21") == [12, 16, 17, 10, 21]

    def test_space_separated(self):
        assert parse_client_hours("12 16 17 10 21") == [12, 16, 17, 10, 21]

    def test_mixed_separators_and_whitespace(self):
        assert parse_client_hours(" 12, 16 ,17  10 ") == [12, 16, 17, 10]

    def test_accepts_bracketed_list_notation_from_the_bonus_example(self):
        assert parse_client_hours("[16, 10, 22, 7]") == [16, 10, 22, 7]

    def test_malformed_bracket_placement_is_rejected_not_silently_misparsed(self):
        # Regression test: an earlier fix stripped every '[' and ']' anywhere
        # in the string, so "16]10[" became "1610" - a single wrong number,
        # silently, instead of an error. Only a single wrapping pair is
        # stripped now; anything else must fail cleanly.
        with pytest.raises(InvalidInputError):
            parse_client_hours("16]10[")
        with pytest.raises(InvalidInputError):
            parse_client_hours("[[16]]")

    def test_rejects_non_positive_values(self):
        with pytest.raises(InvalidInputError):
            parse_client_hours("12, -3, 10")

    def test_rejects_non_integer_tokens(self):
        with pytest.raises(InvalidInputError):
            parse_client_hours("12, abc")

    def test_rejects_empty_input(self):
        with pytest.raises(InvalidInputError):
            parse_client_hours("   ")


class TestMultiClientAllocator:
    def test_higher_priority_client_served_first(self):
        # Total active capacity is 16h; the two requests together (8 + 10 = 18h)
        # can't both be satisfied. The higher one (10h) should be served first,
        # leaving too little behind for the 8h request.
        active = Inventory({BRAVO: 1, CHARLIE: 1, DELTA: 1})
        standby = Inventory()

        results, _, _ = MultiClientAllocator().allocate_all(active, standby, [8, 10])

        by_hours = {r.requested_hours: r for r in results}
        assert by_hours[10].success
        assert not by_hours[8].success

    def test_results_returned_in_original_input_order(self):
        active = Inventory({BRAVO: 5, CHARLIE: 5, DELTA: 5})
        standby = Inventory()

        results, _, _ = MultiClientAllocator().allocate_all(active, standby, [12, 16, 17, 10, 21])

        assert [r.requested_hours for r in results] == [12, 16, 17, 10, 21]
        assert all(r.success for r in results)

    def test_skip_and_continue_on_unfulfillable_client(self):
        active = Inventory({BRAVO: 1})  # 3h total
        standby = Inventory()

        results, _, _ = MultiClientAllocator().allocate_all(active, standby, [100, 2])

        by_hours = {r.requested_hours: r for r in results}
        assert not by_hours[100].success
        assert by_hours[2].success  # untouched inventory still serves the smaller request

    def test_skip_and_continue_when_pool_becomes_fully_drained(self):
        # Regression test: once a higher-priority client consumes every last
        # robot (active AND standby both hit zero), a later client's allocate()
        # call raises NoRobotsAvailableError rather than InsufficientCapacityError.
        # The loop used to only catch the latter, so this used to propagate out
        # and abort the whole batch instead of just skipping this one client.
        active = Inventory({BRAVO: 2})  # exactly 6h, no standby at all
        standby = Inventory()

        results, _, _ = MultiClientAllocator().allocate_all(active, standby, [6, 3, 3])

        by_hours = {}
        for r in results:
            by_hours.setdefault(r.requested_hours, []).append(r)

        assert by_hours[6][0].success
        # both leftover 3h requests should fail cleanly, not crash the batch
        assert not any(r.success for r in results if r.requested_hours == 3)

    def test_inventory_decreases_across_clients(self):
        active = Inventory({BRAVO: 2, CHARLIE: 0, DELTA: 0})  # 2 bravos, 3h each
        standby = Inventory()

        results, final_active, final_standby = MultiClientAllocator().allocate_all(active, standby, [3, 3])

        assert all(r.success for r in results)
        assert final_active.count(BRAVO) == 0
