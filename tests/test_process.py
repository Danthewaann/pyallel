import time

import pytest
from pyallel.process import Process


def test_process_from_command() -> None:
    Process.from_command("sleep 0.1")


@pytest.mark.parametrize(
    "env",
    (
        pytest.param("TEST_VAR=1", id="Single env var"),
        pytest.param("TEST_VAR=1 OTHER_VAR=2", id="Multiple env vars"),
    ),
)
def test_process_from_command_with_env(env: str) -> None:
    Process.from_command(f"{env} sleep 0.1")


def test_read() -> None:
    process = Process.from_command('sh -c \'echo "first"; echo "second"\'')
    process.run()
    while process.poll() is None:
        time.sleep(0.5)
        continue
    output = process.read()
    assert output == b"first\nsecond\n"


def test_readline() -> None:
    process = Process.from_command('sh -c \'echo "first"; echo "second"\'')
    process.run()
    while process.poll() is None:
        time.sleep(0.5)
        continue
    output = process.readline()
    assert output == b"first\n"
    output = process.readline()
    assert output == b"second\n"
