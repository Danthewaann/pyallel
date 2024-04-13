from __future__ import annotations

import time

import pytest
from pyallel.process import Process, get_num_lines


def test_from_command() -> None:
    expected_process = Process(id=1, command="sleep 0.1")
    process = Process.from_command(1, "sleep 0.1")
    assert process == expected_process


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
