from pyallel import main
from pytest import CaptureFixture


def test_run_single_command(capsys: CaptureFixture[str]) -> None:
    assert main.run("sleep 0.1") == 0
    captured = capsys.readouterr()
    out = captured.out.splitlines(keepends=True)
    assert out == [
        "Running commands...\n",
        "\n",
        "[sleep] done ✓\n",
        "\n",
        "Success!\n",
    ]


def test_run_multiple_commands(capsys: CaptureFixture[str]) -> None:
    assert main.run("sleep 0.1", "echo 'hi'") == 0
    captured = capsys.readouterr()
    out = captured.out.splitlines(keepends=True)
    assert out == [
        "Running commands...\n",
        "\n",
        "[echo] done ✓\n",
        "    hi\n",
        "\n",
        "[sleep] done ✓\n",
        "\n",
        "Success!\n",
    ]


def test_run_fail_fast(capsys: CaptureFixture[str]) -> None:
    assert main.run("sleep 1", 'sh -c "exit 1"', "-f") == 1
    captured = capsys.readouterr()
    out = captured.out.splitlines(keepends=True)
    assert out == [
        "Running commands...\n",
        "\n",
        "[sh] failed ✗\n",
        "\n",
        "A command failed!\n",
    ]


def test_run_verbose_mode(capsys: CaptureFixture[str]) -> None:
    assert main.run("sleep 0.1", "-V") == 0
    captured = capsys.readouterr()
    out = captured.out.splitlines(keepends=True)
    assert out == [
        "Arguments:\n",
        "    commands    : ['sleep 0.1']\n",
        "    fail_fast   : False\n",
        "    interactive : True\n",
        "    debug       : False\n",
        "    verbose     : True\n",
        "    version     : False\n",
        "\n",
        "Running commands...\n",
        "\n",
        "[sleep] done ✓\n",
        "\n",
        "Success!\n",
    ]


def test_run_debug_mode(capsys: CaptureFixture[str]) -> None:
    assert main.run("sleep 0.1", "-d") == 0
    captured = capsys.readouterr()
    out = captured.out.splitlines(keepends=True)
    assert out == [
        "Running commands...\n",
        "\n",
        "[sleep 0.1] done in 0s ✓\n",
        "\n",
        "Success!\n",
        "\n",
        "Time taken : 0s\n",
    ]


def test_handles_invalid_executable(capsys: CaptureFixture[str]) -> None:
    assert main.run("invalid_exe") == 1
    captured = capsys.readouterr()
    out = captured.out.splitlines(keepends=True)
    assert out == [
        "Error: executables [invalid_exe] were not found\n",
    ]


def test_handles_many_invalid_executables(capsys: CaptureFixture[str]) -> None:
    assert main.run("invalid_exe", "other_invalid_exe") == 1
    captured = capsys.readouterr()
    out = captured.out.splitlines(keepends=True)
    assert out == [
        "Error: executables [invalid_exe, other_invalid_exe] were not found\n",
    ]
