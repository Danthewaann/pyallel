import os
import time

import pytest
from pyallel.process import Process


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


def test_read() -> None:
    process = Process.from_command('sh -c \'echo "first"; echo "second"\'')
    process.run()
    while process.poll() is None:
        time.sleep(0.5)
        continue
    output = process.read()
    assert output == b"first\nsecond\n"
