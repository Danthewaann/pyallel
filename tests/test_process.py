from __future__ import annotations

import time

import pytest
from pyallel.process import Process, ProcessGroup, ProcessGroupManager, get_num_lines


def test_from_args() -> None:
    expected_process_group_manager = ProcessGroupManager(
        process_groups=[
            ProcessGroup(
                processes=[
                    Process(id=1, command="sleep 0.1"),
                    Process(id=2, command="sleep 0.2"),
                ]
            )
        ]
    )
    process_group_manager = ProcessGroupManager.from_args("sleep 0.1", "sleep 0.2")
    assert process_group_manager == expected_process_group_manager


@pytest.mark.parametrize(
    "args, expected_process_group_manager",
    (
        (
            ["sleep 0.1", "::", "sleep 0.2", "sleep 0.3", "::", "sleep 0.4"],
            ProcessGroupManager(
                process_groups=[
                    ProcessGroup(
                        processes=[
                            Process(id=1, command="sleep 0.1"),
                        ],
                    ),
                    ProcessGroup(
                        processes=[
                            Process(id=1, command="sleep 0.2"),
                            Process(id=2, command="sleep 0.3"),
                        ]
                    ),
                    ProcessGroup(
                        processes=[
                            Process(id=1, command="sleep 0.4"),
                        ]
                    ),
                ]
            ),
        ),
        (
            [
                "sleep 0.1",
                "sleep 0.2",
                "::",
                "sleep 0.3",
                "sleep 0.4",
                "::",
                "sleep 0.5",
                "sleep 0.6",
            ],
            ProcessGroupManager(
                process_groups=[
                    ProcessGroup(
                        processes=[
                            Process(id=1, command="sleep 0.1"),
                            Process(id=2, command="sleep 0.2"),
                        ],
                    ),
                    ProcessGroup(
                        processes=[
                            Process(id=1, command="sleep 0.3"),
                            Process(id=2, command="sleep 0.4"),
                        ],
                    ),
                    ProcessGroup(
                        processes=[
                            Process(id=1, command="sleep 0.5"),
                            Process(id=2, command="sleep 0.6"),
                        ],
                    ),
                ]
            ),
        ),
    ),
)
def test_from_args_with_separators(
    args: list[str], expected_process_group_manager: ProcessGroupManager
) -> None:
    process_group_manager = ProcessGroupManager.from_args(*args)
    assert process_group_manager == expected_process_group_manager


def test_from_command() -> None:
    expected_process = Process(id=1, command="sleep 0.1")
    process = Process.from_command(1, "sleep 0.1")
    assert process == expected_process


def test_from_commands() -> None:
    expected_process_group = ProcessGroup(
        processes=[
            Process(id=1, command="sleep 0.1"),
            Process(id=2, command="sleep 0.2"),
            Process(id=3, command="sleep 0.3"),
        ]
    )
    process_group = ProcessGroup.from_commands("sleep 0.1", "sleep 0.2", "sleep 0.3")
    assert process_group == expected_process_group


def test_read() -> None:
    process = Process.from_command(1, "echo first; echo second")
    process.run()
    output = process.read()
    assert output == b""
    time.sleep(0.01)
    output = process.read()
    assert output == b"first\nsecond\n"


def test_readline() -> None:
    process = Process.from_command(1, "echo first; echo second")
    process.run()
    output = process.readline()
    assert output == b""
    time.sleep(0.01)
    output = process.readline()
    assert output == b"first\n"
    output = process.readline()
    assert output == b"second\n"


def test_readline_with_read() -> None:
    process = Process.from_command(1, "echo first; echo second")
    process.run()
    output = process.readline()
    assert output == b""
    time.sleep(0.01)
    output = process.readline()
    assert output == b"first\n"
    output = process.read()
    assert output == b"second\n"


def test_readline_handles_delayed_newline() -> None:
    process = Process.from_command(1, "printf first; sleep 0.1; echo second")
    process.run()
    time.sleep(0.01)
    output = process.readline()
    assert output == b"first"
    time.sleep(0.3)
    output = process.readline()
    assert output == b"second\n"


@pytest.mark.parametrize(
    "output,expected",
    (
        (
            "Hello Mr Anderson",
            1,
        ),
        (
            "Hello Mr Anderson\nIt is inevitable",
            2,
        ),
        (
            "Hello Mr Anderson\nIt is inevitable\nHAHAHAHAH",
            3,
        ),
    ),
)
def test_get_num_lines(output: str, expected: int) -> None:
    assert get_num_lines(output) == expected


@pytest.mark.parametrize("columns,lines", ((8, 3), (5, 4)))
def test_get_num_lines_with_columns(columns: int, lines: int) -> None:
    assert get_num_lines("Hello Mr Anderson", columns=columns) == lines


def test_get_num_lines_with_long_line() -> None:
    assert get_num_lines(" " * 250, columns=200) == 2


def test_get_num_lines_ignores_ansi_chars() -> None:
    assert get_num_lines("\x1B[0m" * 100, columns=10) == 1
