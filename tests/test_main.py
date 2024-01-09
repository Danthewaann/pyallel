import subprocess
from pyallel import main
from pytest import CaptureFixture


def prettify_error(out: str) -> str:
    return f"Got an error\n\n{out}"


def test_run_single_command(capsys: CaptureFixture[str]) -> None:
    exit_code = main.run("sleep 0.1")
    captured = capsys.readouterr()
    out = captured.out.splitlines(keepends=True)
    assert exit_code == 0, prettify_error(captured.out)
    assert out == [
        "Running commands...\n",
        "\n",
        "[sleep] done ✓\n",
        "\n",
        "Success!\n",
    ]


def test_run_single_command_with_output(capsys: CaptureFixture[str]) -> None:
    exit_code = main.run("echo 'hi'")
    captured = capsys.readouterr()
    out = captured.out.splitlines(keepends=True)
    assert exit_code == 0, prettify_error(captured.out)
    assert out == [
        "Running commands...\n",
        "\n",
        "[echo] done ✓\n",
        "    hi\n",
        "\n",
        "Success!\n",
    ]


def test_run_single_command_with_env(capsys: CaptureFixture[str]) -> None:
    exit_code = main.run("TEST_VAR=1 sleep 0.1")
    captured = capsys.readouterr()
    out = captured.out.splitlines(keepends=True)
    assert exit_code == 0, prettify_error(captured.out)
    assert out == [
        "Running commands...\n",
        "\n",
        "[sleep] done ✓\n",
        "\n",
        "Success!\n",
    ]


def test_run_single_command_with_tail_mode(capsys: CaptureFixture[str]) -> None:
    exit_code = main.run("tail=10 :: sleep 0.1")
    captured = capsys.readouterr()
    out = captured.out.splitlines(keepends=True)
    assert exit_code == 0, prettify_error(captured.out)
    assert out == [
        "Running commands...\n",
        "\n",
        "[sleep] done ✓\n",
        "\n",
        "Success!\n",
    ]


def test_run_multiple_commands(capsys: CaptureFixture[str]) -> None:
    exit_code = main.run("sh -c 'sleep 0.1; echo \"first\"'", "echo 'hi'")
    captured = capsys.readouterr()
    out = captured.out.splitlines(keepends=True)
    assert exit_code == 0, prettify_error(captured.out)
    assert out == [
        "Running commands...\n",
        "\n",
        "[echo] done ✓\n",
        "    hi\n",
        "\n",
        "[sh] done ✓\n",
        "    first\n",
        "\n",
        "Success!\n",
    ]


def test_run_multiple_commands_streamed_mode(capsys: CaptureFixture[str]) -> None:
    exit_code = main.run(
        "sh -c 'sleep 0.1; echo \"first\"'",
        'sh -c \'echo "hi"; echo "bye"\'',
        "-s",
        "-n",
    )
    captured = capsys.readouterr()
    out = captured.out.splitlines(keepends=True)
    assert exit_code == 0, prettify_error(captured.out)
    assert out == [
        "Running commands...\n",
        "\n",
        "[sh] running... \n",
        "    first\n",
        "[sh] done ✓\n",
        "\n",
        "[sh] running... \n",
        "    hi\n",
        "    bye\n",
        "[sh] done ✓\n",
        "\n",
        "Success!\n",
    ]


def test_run_fail_fast(capsys: CaptureFixture[str]) -> None:
    exit_code = main.run("sleep 0.1", 'sh -c "exit 1"', "-f")
    captured = capsys.readouterr()
    out = captured.out.splitlines(keepends=True)
    assert exit_code == 1, prettify_error(captured.out)
    assert out == [
        "Running commands...\n",
        "\n",
        "[sh] failed ✗\n",
        "\n",
        "A command failed!\n",
    ]


def test_run_verbose_mode(capsys: CaptureFixture[str]) -> None:
    exit_code = main.run("sleep 0.1", "-V")
    captured = capsys.readouterr()
    out = captured.out.splitlines(keepends=True)
    assert exit_code == 0, prettify_error(captured.out)
    assert out == [
        "Arguments:\n",
        "    commands    : ['sleep 0.1']\n",
        "    fail_fast   : False\n",
        "    interactive : True\n",
        "    debug       : False\n",
        "    stream      : False\n",
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
    exit_code = main.run("sleep 0.1", "-d")
    captured = capsys.readouterr()
    out = captured.out.splitlines(keepends=True)
    assert exit_code == 0, prettify_error(captured.out)
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
    exit_code = main.run("invalid_exe")
    captured = capsys.readouterr()
    out = captured.out.splitlines(keepends=True)
    assert exit_code == 1, prettify_error(captured.out)
    assert out == [
        "Error: executables [invalid_exe] were not found\n",
    ]


def test_handles_many_invalid_executables(capsys: CaptureFixture[str]) -> None:
    exit_code = main.run("invalid_exe", "other_invalid_exe")
    captured = capsys.readouterr()
    out = captured.out.splitlines(keepends=True)
    assert exit_code == 1, prettify_error(captured.out)
    assert out == [
        "Error: executables [invalid_exe, other_invalid_exe] were not found\n",
    ]


def test_does_not_run_executables_on_parsing_error(capsys: CaptureFixture[str]) -> None:
    exit_code = main.run("invalid_exe", "other_invalid_exe", "sleep 10")
    captured = capsys.readouterr()
    assert exit_code == 1, prettify_error(captured.out)
    status = subprocess.run(["pgrep", "sleep"])
    assert status.returncode == 1, "sleep shouldn't be running!"
