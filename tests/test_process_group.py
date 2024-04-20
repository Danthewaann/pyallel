from __future__ import annotations


import pytest
from pyallel.process import Process
from pyallel.process_group import ProcessGroup, get_num_lines


def test_from_command() -> None:
    expected_process = Process(id=1, command="sleep 0.1")
    process = Process(1, "sleep 0.1")
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
