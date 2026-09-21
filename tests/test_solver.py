from robot_allocation.domain import BRAVO, CHARLIE, DELTA, Inventory
from robot_allocation.solver import min_weight_cover


def test_fewest_robots_preferred_on_a_weight_tie():
    # Delta alone (8h, weight 8) ties on weight with Bravo+Charlie (3h+5h,
    # weight 8) when weight_fn is hours itself - the single-robot combo wins.
    inventory = Inventory({BRAVO: 5, CHARLIE: 5, DELTA: 5})
    cover = min_weight_cover(inventory, 8, weight_fn=lambda t: t.hours)
    assert cover.total_hours == 8
    assert cover.counts == {DELTA: 1}


def test_minimises_overshoot_when_no_exact_match():
    inventory = Inventory({BRAVO: 2, CHARLIE: 0, DELTA: 0})
    # only bravo (3h) available, need 4 -> must take 2 bravos = 6h (excess 2)
    cover = min_weight_cover(inventory, 4, weight_fn=lambda t: t.hours)
    assert cover.total_hours == 6
    assert cover.counts == {BRAVO: 2}


def test_respects_bounded_counts():
    inventory = Inventory({BRAVO: 1})
    cover = min_weight_cover(inventory, 4, weight_fn=lambda t: t.hours)
    assert cover is None  # only one bravo (3h) available, can't reach 4h


def test_returns_none_when_target_unreachable():
    inventory = Inventory({BRAVO: 1, CHARLIE: 1, DELTA: 1})
    cover = min_weight_cover(inventory, 100, weight_fn=lambda t: t.cost)
    assert cover is None


def test_zero_target_returns_empty_cover():
    inventory = Inventory({BRAVO: 2})
    cover = min_weight_cover(inventory, 0, weight_fn=lambda t: t.cost)
    assert cover.counts == {}
    assert cover.total_hours == 0


def test_minimises_cost_not_just_hours():
    # Delta is the cheapest per hour ($4/8h = 0.5) vs Bravo ($2/3h = 0.667)
    inventory = Inventory({BRAVO: 3, DELTA: 3})
    cover = min_weight_cover(inventory, 8, weight_fn=lambda t: t.cost)
    assert cover.counts == {DELTA: 1}
    assert cover.weight == 4
