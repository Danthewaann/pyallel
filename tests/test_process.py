import os

import pytest
from pyallel.process import Process
from concurrent.futures import ThreadPoolExecutor


def test_process_from_command() -> None:
    expected_process = Process(name="sleep", args=["0.1"], env=os.environ.copy())
    process = Process.from_command("sleep 0.1")
    assert process == expected_process


@pytest.mark.parametrize(
    "env",
    (
        pytest.param({"TEST_VAR": "1"}, id="Single env var"),
        pytest.param({"TEST_VAR": "1", "OTHER_VAR": "2"}, id="Multiple env vars"),
    ),
)
def test_process_from_command_with_env(env: dict[str, str]) -> None:
    expected_process = Process(name="sleep", args=["0.1"], env=os.environ.copy() | env)
    env_str = " ".join(f"{key}={value}" for key, value in env.items())
    process = Process.from_command(f"{env_str} sleep 0.1")
    assert process == expected_process


def test_run_multiple_commands() -> None:
    process1 = Process.from_command('sh -c \'echo "first"; sleep 1; echo "second"\'')
    process2 = Process.from_command('sh -c \'echo "first"; sleep 3; echo "second"\'')
    process1.run()
    process2.run()

    def readline(process: Process) -> bytes:
        output = b""
        while line := process.stdout().readline():
            output += line
        return output

    # with ThreadPoolExecutor(max_workers=2) as executor:
    #     future1 = executor.submit(readline, process1)
    #     future2 = executor.submit(readline, process2)

    assert readline(process1) == b"first\nsecond\n"
    assert readline(process2) == b"first\nsecond\n"
    # assert future1.result() == b"first\nsecond\n"
    # assert future2.result() == b"first\nsecond\n"


def test_stream_command_output() -> None:
    process = Process.from_command('sh -c \'echo "first"; echo "second"\'')
    process.run()
    output = process.stream()
    assert output == b"first\n"
    assert process.output == b"first\n"
    output = process.stream()
    assert output == b"second\n"
    assert process.output == b"first\nsecond\n"


def test_read_command_output() -> None:
    process = Process.from_command('sh -c \'echo "first"; echo "second"\'')
    process.run()
    output = process.read()
    assert output == b"first\nsecond\n"
    assert process.output == b"first\nsecond\n"
