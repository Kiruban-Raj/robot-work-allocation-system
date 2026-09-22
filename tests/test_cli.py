from robot_allocation.cli import main, run_interactive


def test_non_interactive_level1(capsys):
    exit_code = main(["--bravo", "2", "--charlie", "3", "--delta", "2", "--hours", "16", "--level", "1"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Robot Assignment" in output
    assert "Bravo: 1" in output
    assert "Charlie: 1" in output
    assert "Delta: 1" in output
    assert "Total Work Hours Provided: 16" in output
    assert "Client Work Hours Requested: 16" in output


def test_non_interactive_level2(capsys):
    exit_code = main(["--bravo", "2", "--charlie", "3", "--delta", "2", "--hours", "20", "--level", "2"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Cost Optimized Allocation" in output
    assert "Total Hours Provided: 21" in output
    assert "Total Charging Cost: $11" in output


def test_non_interactive_level3(capsys):
    exit_code = main([
        "--bravo", "1", "--charlie", "1", "--delta", "1",
        "--standby-bravo", "5", "--standby-charlie", "5", "--standby-delta", "5",
        "--hours", "21", "--level", "3",
    ])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Additional Standby Robots Required" in output
    assert "Charlie: 1" in output


def test_non_interactive_level4_multi_client(capsys):
    exit_code = main([
        "--bravo", "5", "--charlie", "5", "--delta", "5",
        "--hours", "12,16,17,10,21", "--summary",
    ])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert output.count("Client work hours requested:") == 5
    assert "Allocation Summary" in output
    assert "Efficiency Metrics" in output


def test_zero_robots_error(capsys):
    exit_code = main(["--hours", "10", "--level", "1"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "Error: No robots available for assignment." in output


def test_insufficient_capacity_error(capsys):
    exit_code = main(["--bravo", "1", "--hours", "100", "--level", "1"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "Error: Insufficient robot capacity to complete the requested work." in output


def test_invalid_hours_error(capsys):
    exit_code = main(["--bravo", "1", "--hours", "-5", "--level", "1"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "Error: Work hours must be a positive integer." in output


def test_interactive_flow_matches_deck_example(monkeypatch, capsys):
    inputs = iter(["2", "3", "2", "16"])
    monkeypatch.setattr("builtins.input", lambda *_args: next(inputs))

    exit_code = run_interactive()
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Robot Assignment" in output
    assert "Total Work Hours Provided: 16" in output
    assert "Client Work Hours Requested: 16" in output


def test_negative_active_robot_count_is_a_clean_error_not_a_crash(capsys):
    exit_code = main(["--bravo", "-5", "--hours", "10", "--level", "1"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "Error: Robot counts must be non-negative integers." in output


def test_negative_standby_robot_count_is_a_clean_error_not_a_crash(capsys):
    exit_code = main(["--bravo", "1", "--standby-bravo", "-2", "--hours", "10", "--level", "3"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "Error: Robot counts must be non-negative integers." in output


def test_default_flow_falls_through_to_standby_when_active_alone_is_insufficient(capsys):
    # Regression test: the default (no --level) flow used to call
    # compare_strategies() first, which raised InsufficientCapacityError
    # before ever checking whether standby robots could cover the gap.
    exit_code = main([
        "--bravo", "1", "--charlie", "1", "--delta", "1",
        "--standby-charlie", "5", "--hours", "21",
    ])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "insufficient for a Level 1/2 comparison" in output
    assert "Additional Standby Robots Required" in output
    assert "Charlie: 1" in output
    assert "Total Hours Provided: 21" in output


def test_level4_batch_survives_a_client_hitting_a_fully_drained_pool(capsys):
    # Regression test: a later client hitting a completely empty pool (both
    # active and standby drained by earlier higher-priority clients) used to
    # raise NoRobotsAvailableError uncaught by the multi-client loop, aborting
    # the whole batch instead of just failing that one client.
    exit_code = main(["--bravo", "2", "--hours", "6,3,3", "--summary"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert output.count("Client work hours requested:") == 3
    assert output.count("Error: No robots available for assignment.") == 2
    assert "Allocation Summary" in output


def test_level4_batch_exit_code_is_nonzero_when_every_client_fails(capsys):
    # Regression test: _run_multi_client always returned 0 regardless of
    # outcome, so a script checking $? would see "success" even when zero
    # of the requested clients were actually served.
    exit_code = main(["--hours", "5,10,15"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert output.count("Error: No robots available for assignment.") == 3


def test_level4_batch_exit_code_stays_zero_on_partial_success(capsys):
    exit_code = main(["--bravo", "2", "--hours", "6,3,3", "--summary"])
    capsys.readouterr()

    assert exit_code == 0


def test_interactive_default_flow_falls_through_to_standby(monkeypatch, capsys):
    inputs = iter(["1", "1", "1", "21", "0", "5", "0"])
    monkeypatch.setattr("builtins.input", lambda *_args: next(inputs))

    exit_code = run_interactive()
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "insufficient for a Level 1/2 comparison" in output
    assert "Additional Standby Robots Required" in output
    assert "Total Hours Provided: 21" in output
