# Robot Work Allocation System

Terminal application for EverBot Solutions: assigns Bravo/Charlie/Delta robots to
client work requests across four levels of increasing complexity, plus a bonus
multi-client summary.

## Design

There's one shared allocation engine (`robot_allocation/solver.py`) behind every
level: a bounded-knapsack "minimum weight cover" search that finds the cheapest
(or least-excess) combination of robots whose total hours meet or exceed a
target, given a limited inventory. Minimising *cost* gives Level 2's strategy;
minimising *hours themselves* gives Level 1's "least excess" strategy, since
overshoot is just `total_hours - target` and the target is fixed. Level 3 and
Level 4 both build on top of that same engine rather than reimplementing it.

```
robot_allocation/
  domain.py       robot types, Inventory, AllocationResult
  errors.py       the exact error messages from the spec
  solver.py       the shared min-weight-cover search
  strategies.py   Level 1 (diversity-first) and Level 2 (cost-optimal)
  standby.py      Level 3 (active fleet + standby top-up)
  multiclient.py  Level 4 (priority ordering, parsing, skip-and-continue)
  summary.py      bonus allocation summary / utilization metrics
  cli.py          interactive prompts + non-interactive flags
```

## Assumptions

A few judgment calls the spec doesn't fully pin down:

- **Level 1 with a missing category.** If one robot type has zero units
  available, the system still allocates with whatever categories exist rather
  than hard-erroring — "include multiple categories" is read as best-effort,
  not mandatory. It only errors out if the requested hours genuinely can't be
  met.
- **Level 4 shortfalls.** If a client's request can't be fulfilled even after
  tapping standby robots, that client is skipped (with an error shown) and the
  rest of the batch still runs, rather than aborting everything.
- **"Utilization" in the bonus metrics.** Since a robot always works its full
  fixed shift or not at all, hours-based utilization is trivially 100% for any
  robot that's used. The more informative number for "evaluating categories
  for future purchases" is deployment rate — `robots_used / robots_available`
  per category — so that's what's reported.
- **Level 3's active fleet.** The example in the spec uses the *entire* active
  fleet before touching standby (rather than cost-optimizing which active
  robots to use), so that's the behavior implemented: use all of active first,
  then cover only the remaining deficit with the cheapest standby combination.

## Running it

Interactive (matches the spec's terminal mock-ups):

```
python main.py
```

Non-interactive, for scripting/CI:

```
python main.py --bravo 2 --charlie 3 --delta 2 --hours 16 --level 1
python main.py --bravo 2 --charlie 3 --delta 2 --hours 20 --level 2
python main.py --bravo 1 --charlie 1 --delta 1 \
  --standby-bravo 5 --standby-charlie 5 --standby-delta 5 --hours 21 --level 3
python main.py --bravo 5 --charlie 5 --delta 5 --hours "12,16,17,10,21" --summary
```

Omitting `--level` runs Level 1 and Level 2 side by side with the required cost
comparison - unless the active fleet alone can't reach the requested hours, in
which case that comparison is skipped (it wouldn't be meaningful) and it falls
straight through to Level 3's standby logic instead. Multiple `--hours` values
(comma or space separated, optionally wrapped in brackets like the bonus
section's own `[16, 10, 22, 7]` notation) automatically switch to the Level 4
multi-client flow.

**Exit codes:** 0 on success. For a Level 4 batch, 0 as long as at least one
client was served; 1 only if every client in the batch failed. 1 for any
single-request failure (insufficient capacity, invalid input, no robots
available).

## Tests

```
pip install pytest
pytest -v
```

Tests are organised by module and include every worked example from the spec
(the 16h/17h/24h/21h Level 1 cases, both Level 2 cost examples, the Level 1 vs
Level 2 $1 difference, and the Level 3 standby example), plus edge cases for
each documented error.

**Note on TDD:** tests were written alongside each module rather than strictly
test-first, commit-by-commit. That said, they did their job as tests, not
paperwork — while building the solver's tie-breaking logic, the test suite
caught three real bugs (two allocations that hit the target hours but picked
the wrong combination) before this was called done, and those cases are now
permanently pinned down as regression tests.

**Note on the later review pass:** after the initial implementation, a
dedicated re-check against every rule in the spec (not just re-reading the
code, but deliberately trying to break each documented constraint) found six
more edge-case bugs — negative counts crashing instead of erroring cleanly,
the default flow not falling through to Level 3, a float-formatted cost in
the summary, a Level 4 batch aborting entirely when a client hit a fully
drained pool, the batch exit code never reflecting total failure, and the
bonus section's bracketed input notation not parsing. All six are fixed with
dedicated regression tests (suite: 48 → 58).
