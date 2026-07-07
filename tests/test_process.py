from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from pyallel.errors import InvalidLinesModifierError
from pyallel.process import Process


def test_from_command() -> None:
    expected_process = Process(id=1, command="sleep 0.1")
    process = Process.from_command(1, "sleep 0.1")
    assert process.id == expected_process.id
    assert process.command == "sleep 0.1"
    assert process.percentage_lines == 0.0


@pytest.mark.parametrize(("value", "expected"), [("1", 0.01), ("100", 1.0), ("50", 0.5), ("10", 0.1)])
def test_from_command_with_lines_modifier(value: str, expected: float) -> None:
    expected_process = Process(id=1, command="sleep 0.1")
    process = Process.from_command(1, f"lines={value} :::: sleep 0.1")
    assert process.id == expected_process.id
    assert process.command == "sleep 0.1"
    assert process.percentage_lines == expected


@pytest.mark.parametrize("value", ["invalid", "0", "-1", "110", ""])
def test_from_command_with_invalid_lines_modifier(value: str) -> None:
    with pytest.raises(
        InvalidLinesModifierError,
        match="lines modifier must be a number between 1 and 100",
    ):
        Process.from_command(1, f"lines={value} :::: sleep 0.1")


def test_from_command_handles_invalid_args_syntax() -> None:
    expected_process = Process(id=1, command="sleep 0.1")
    process = Process.from_command(1, " :::: sleep 0.1 :::: echo hi")
    assert process.id == expected_process.id
    assert process.command == "sleep 0.1 :::: echo hi"
    assert process.percentage_lines == 0.0


def test_from_command_ignores_invalid_arg() -> None:
    expected_process = Process(id=1, command="sleep 0.1")
    process = Process.from_command(1, "bad=value :::: sleep 0.1 :::: echo hi")
    assert process.id == expected_process.id
    assert process.command == "sleep 0.1 :::: echo hi"
    assert process.percentage_lines == 0.0


def test_from_command_with_lines_modifier_handles_multiple_separators() -> None:
    expected_process = Process(id=1, command="sleep 0.1")
    process = Process.from_command(1, "lines=50 :::: sleep 0.1 :::: echo hi")
    assert process.id == expected_process.id
    assert process.command == "sleep 0.1 :::: echo hi"
    assert process.percentage_lines == 0.5


@patch.object(subprocess, "Popen")
def test_read(popen_mock: MagicMock) -> None:
    popen_mock.return_value.stdout.read1.side_effect = [b"first\nsecond\n", b""]
    process = Process(1, "echo first; echo second")
    process.run()
    output = process.read()
    assert output == b"first\nsecond\n"
