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
