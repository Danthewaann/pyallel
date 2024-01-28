from __future__ import annotations

import os
import time
from typing import Any
from uuid import uuid4

import pytest
from pyallel.errors import InvalidExecutableError
from pyallel.process import DumpMode, Process, TailMode, get_num_lines


def test_from_command() -> None:
    expected_process = Process(
        id=uuid4(), name="sleep", args=["0.1"], env=os.environ.copy()
    )
    process = Process.from_command("sleep 0.1")
    assert process == expected_process


@pytest.mark.parametrize(
    "env",
    (
        pytest.param("TEST_VAR=1", id="Single env var"),
        pytest.param("TEST_VAR=1 OTHER_VAR=2", id="Multiple env vars"),
    ),
)
def test_from_command_with_env(env: str) -> None:
    env_dict: dict[str, str] = {}
    for t in env.split():
        key, value = t.split("=")
        env_dict[key] = value
    expected_process = Process(
        id=uuid4(), name="sleep", args=["0.1"], env={**os.environ.copy(), **env_dict}
    )
    process = Process.from_command(f"{env} sleep 0.1")
    assert process == expected_process


@pytest.mark.parametrize(
    "modes,expected",
    (
        (
            "tail=10",
            {
                "tail_mode": TailMode(enabled=True, lines=10),
            },
        ),
        (
            "tail=10,dump",
            {
                "tail_mode": TailMode(enabled=True, lines=10),
                "dump_mode": DumpMode(enabled=True),
            },
        ),
    ),
)
def test_from_command_with_modes(modes: str, expected: dict[str, Any]) -> None:
    expected_process = Process(
        id=uuid4(), name="sleep", args=["0.1"], env=os.environ.copy(), **expected
    )
    process = Process.from_command(f"{modes} :: sleep 0.1")
    assert process == expected_process


@pytest.mark.parametrize("mode", ("tail", "tail=hi", "tail=-1", "tail=0"))
def test_from_command_with_tail_mode_handles_errors(mode: str) -> None:
    with pytest.raises(
        InvalidExecutableError, match="tail mode requires a positive number"
    ):
        Process.from_command(f"{mode} :: sleep 0.1")


def test_from_command_with_modes_and_env() -> None:
    expected_process = Process(
        id=uuid4(),
        name="sleep",
        args=["0.1"],
        env={**os.environ.copy(), **{"TEST_VAR": "1"}},
        tail_mode=TailMode(enabled=True, lines=10),
    )
    process = Process.from_command("tail=10 :: TEST_VAR=1 sleep 0.1")
    assert process == expected_process


def test_read() -> None:
    process = Process.from_command('sh -c \'echo "first"; echo "second"\'')
    process.run()
    output = process.read()
    assert output == b""
    time.sleep(0.01)
    output = process.read()
    assert output == b"first\nsecond\n"


def test_readline() -> None:
    process = Process.from_command('sh -c \'echo "first"; echo "second"\'')
    process.run()
    output = process.readline()
    assert output == b""
    time.sleep(0.01)
    output = process.readline()
    assert output == b"first\n"
    output = process.readline()
    assert output == b"second\n"


def test_readline_with_read() -> None:
    process = Process.from_command('sh -c \'echo "first"; echo "second"\'')
    process.run()
    output = process.readline()
    assert output == b""
    time.sleep(0.01)
    output = process.readline()
    assert output == b"first\n"
    output = process.read()
    assert output == b"second\n"


def test_readline_handles_delayed_newline() -> None:
    process = Process.from_command('sh -c \'printf "first"; sleep 0.1; echo "second"\'')
    process.run()
    time.sleep(0.01)
    output = process.readline()
    assert output == b"first"
    time.sleep(0.2)
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


@pytest.mark.parametrize("columns,lines", ((8, 2), (5, 3)))
def test_get_num_lines_with_columns(columns: int, lines: int) -> None:
    assert get_num_lines("Hello Mr Anderson", columns=columns) == lines
