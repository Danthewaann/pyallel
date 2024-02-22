from __future__ import annotations

import os
import time
from typing import Any
from uuid import uuid4

import pytest
from pyallel.process import DumpMode, Process


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
            "dump",
            {
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


def test_process_interrupt_with_trapped_output() -> None:
    # Verify that only `hi` is outputted when running the script as normal
    process = Process.from_command(
        "./tests/assets/test_process_interrupt_with_trapped_output.sh"
    )
    process.run()
    assert process.wait() == 0, process.read()
    assert process.read() == b"hi\n"

    # Verify that `hi` and `error` is outputted when terminating the script
    # while it is running
    process = Process.from_command(
        "./tests/assets/test_process_interrupt_with_trapped_output.sh"
    )
    process.run()
    time.sleep(0.1)
    process.interrupt()
    assert process.wait() == 2, process.read()
    assert process.read() == b"hi\nerror\n"
