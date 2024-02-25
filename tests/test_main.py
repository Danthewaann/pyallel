import os
import re
import signal
import subprocess
import time

import pytest
from pyallel import main
from pytest import CaptureFixture, MonkeyPatch


def prettify_error(out: str) -> str:
    return f"Got an error\n\n{out}"


PREFIX = "=> "


class TestStreamedMode:
    """Test streamed mode with interactivity

    NOTE: These tests can only verify the exit code consistently
    as terminal output is re-written which isn't easy to consistently assert against
    """

    @pytest.fixture(autouse=True)
    def in_tty(self, monkeypatch: MonkeyPatch) -> None:
        ## Trick pyallel into thinking we are in an interactive terminal
        ## so we can test the interactive mode
        monkeypatch.setattr(main.constants, "IN_TTY", True)  # type: ignore[attr-defined]

    def test_run_single_command(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run("echo 'hi'", "-t")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)

    def test_run_single_command_with_output(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run("echo 'hi'", "-t")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)

    def test_run_single_command_failure(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run('sh -c "exit 1"', "-t")
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)

    def test_run_single_command_with_env(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run("TEST_VAR=1 echo 'hi'", "-t")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)

    def test_run_multiple_commands(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run("sh -c 'sleep 0.1; echo \"first\"'", "echo 'hi'", "-t")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)

    def test_run_multiple_commands_single_failure(
        self, capsys: CaptureFixture[str]
    ) -> None:
        exit_code = main.run('sh -c "exit 1"', 'echo "hi"', "-t")
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)

    def test_run_multiple_commands_multiple_failures(
        self,
        capsys: CaptureFixture[str],
    ) -> None:
        exit_code = main.run('sh -c "exit 1"', 'sh -c "exit 1"', "-t")
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)

    def test_run_verbose_mode(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run("echo 'hi'", "-V", "-t")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)

    def test_run_timer_mode(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run("echo 'hi'")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)

    def test_handles_running_pyallel_within_pyallel(
        self, capsys: CaptureFixture[str]
    ) -> None:
        exit_code = main.run(
            "pyallel ./tests/assets/test_handle_multiple_signals.sh -t", "-t"
        )
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)

    def test_handles_invalid_executable(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run("invalid_exe", "-t", "--colour", "no")
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)
        assert (
            captured.out == f"{PREFIX}Error: executables [invalid_exe] were not found\n"
        ), prettify_error(captured.out)

    def test_handles_many_invalid_executables(
        self, capsys: CaptureFixture[str]
    ) -> None:
        exit_code = main.run("invalid_exe", "other_invalid_exe", "-t", "--colour", "no")
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)
        assert (
            captured.out
            == f"{PREFIX}Error: executables [invalid_exe, other_invalid_exe] were not found\n"
        )

    def test_does_not_run_executables_on_parsing_error(
        self, capsys: CaptureFixture[str]
    ) -> None:
        exit_code = main.run(
            "invalid_exe", "other_invalid_exe", "sleep 10", "-t", "--colour", "no"
        )
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)
        assert (
            captured.out
            == f"{PREFIX}Error: executables [invalid_exe, other_invalid_exe] were not found\n"
        )
        status = subprocess.run(["pgrep", "-f", "^sleep 10$"])
        assert status.returncode == 1, "sleep shouldn't be running!"

    @pytest.mark.parametrize(
        "signal,exit_code", ((signal.SIGINT, 130), (signal.SIGTERM, 143))
    )
    def test_handles_signals(self, signal: int, exit_code: int) -> None:
        process = subprocess.Popen(
            ["pyallel", "./tests/assets/test_process_interrupt_with_trapped_output.sh"],
            env=os.environ.copy(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        time.sleep(0.3)
        process.send_signal(signal)
        assert process.wait() == exit_code

    @pytest.mark.parametrize(
        "signal,exit_code", ((signal.SIGINT, 130), (signal.SIGTERM, 143))
    )
    def test_handles_multiple_signals(self, signal: int, exit_code: int) -> None:
        process = subprocess.Popen(
            [
                "pyallel",
                "./tests/assets/test_handle_multiple_signals.sh",
            ],
            env=os.environ.copy(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        time.sleep(0.3)
        process.send_signal(signal)
        time.sleep(0.1)
        process.send_signal(signal)
        assert process.wait() == exit_code


class TestStreamedNonInteractiveMode:
    def test_run_single_command(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run("echo 'hi'", "-n", "-t")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        assert captured.out.splitlines(keepends=True) == (
            [
                f"{PREFIX}Running commands...\n",
                f"{PREFIX}\n",
                f"{PREFIX}[echo] running... \n",
                f"{PREFIX}hi\n",
                f"{PREFIX}[echo] done ✓\n",
                f"{PREFIX}\n",
                f"{PREFIX}Done!\n",
            ]
        )

    def test_run_single_command_failure(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run('sh -c "exit 1"', "-n", "-t")
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)
        assert captured.out.splitlines(keepends=True) == (
            [
                f"{PREFIX}Running commands...\n",
                f"{PREFIX}\n",
                f"{PREFIX}[sh] running... \n",
                f"{PREFIX}[sh] failed ✗\n",
                f"{PREFIX}\n",
                f"{PREFIX}Failed!\n",
            ]
        )

    def test_run_single_command_with_env(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run("TEST_VAR=1 echo 'hi'", "-n", "-t")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        assert captured.out.splitlines(keepends=True) == (
            [
                f"{PREFIX}Running commands...\n",
                f"{PREFIX}\n",
                f"{PREFIX}[echo] running... \n",
                f"{PREFIX}hi\n",
                f"{PREFIX}[echo] done ✓\n",
                f"{PREFIX}\n",
                f"{PREFIX}Done!\n",
            ]
        )

    def test_run_multiple_commands(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run(
            "sh -c 'sleep 0.1; echo \"first\"'", "echo 'hi'", "-n", "-t"
        )
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        assert captured.out.splitlines(keepends=True) == (
            [
                f"{PREFIX}Running commands...\n",
                f"{PREFIX}\n",
                f"{PREFIX}[sh] running... \n",
                f"{PREFIX}first\n",
                f"{PREFIX}[sh] done ✓\n",
                f"{PREFIX}\n",
                f"{PREFIX}[echo] running... \n",
                f"{PREFIX}hi\n",
                f"{PREFIX}[echo] done ✓\n",
                f"{PREFIX}\n",
                f"{PREFIX}Done!\n",
            ]
        )

    def test_run_multiple_commands_single_failure(
        self, capsys: CaptureFixture[str]
    ) -> None:
        exit_code = main.run('sh -c "exit 1"', 'echo "hi"', "-n", "-t")
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)
        assert captured.out.splitlines(keepends=True) == (
            [
                f"{PREFIX}Running commands...\n",
                f"{PREFIX}\n",
                f"{PREFIX}[sh] running... \n",
                f"{PREFIX}[sh] failed ✗\n",
                f"{PREFIX}\n",
                f"{PREFIX}[echo] running... \n",
                f"{PREFIX}hi\n",
                f"{PREFIX}[echo] done ✓\n",
                f"{PREFIX}\n",
                f"{PREFIX}Failed!\n",
            ]
        )

    def test_run_multiple_commands_multiple_failures(
        self,
        capsys: CaptureFixture[str],
    ) -> None:
        exit_code = main.run('sh -c "exit 1"', 'sh -c "exit 1"', "-n", "-t")
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)
        assert captured.out.splitlines(keepends=True) == (
            [
                f"{PREFIX}Running commands...\n",
                f"{PREFIX}\n",
                f"{PREFIX}[sh] running... \n",
                f"{PREFIX}[sh] failed ✗\n",
                f"{PREFIX}\n",
                f"{PREFIX}[sh] running... \n",
                f"{PREFIX}[sh] failed ✗\n",
                f"{PREFIX}\n",
                f"{PREFIX}Failed!\n",
            ]
        )

    def test_run_verbose_mode(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run("echo 'hi'", "-n", "-V", "-t")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        assert captured.out.splitlines(keepends=True) == (
            [
                f"{PREFIX}Running commands...\n",
                f"{PREFIX}\n",
                f"{PREFIX}[echo hi] running... \n",
                f"{PREFIX}hi\n",
                f"{PREFIX}[echo hi] done ✓\n",
                f"{PREFIX}\n",
                f"{PREFIX}Done!\n",
            ]
        )

    def test_run_timer_mode(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run("echo 'hi'", "-n")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        assert (
            re.search(
                "".join(
                    [
                        f"{PREFIX}Running commands...\n",
                        f"{PREFIX}\n",
                        rf"{PREFIX}\[echo\] running... \n",
                        f"{PREFIX}hi\n",
                        rf"{PREFIX}\[echo\] done ✓ \(0\..*\)\n",
                        f"{PREFIX}\n",
                        f"{PREFIX}Done!\n",
                    ]
                ),
                captured.out,
            )
            is not None
        ), prettify_error(captured.out)

    def test_run_with_longer_first_command(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run("sleep 1", "echo 'hi'", "-n")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        assert (
            re.search(
                "".join(
                    [
                        f"{PREFIX}Running commands...\n",
                        f"{PREFIX}\n",
                        rf"{PREFIX}\[sleep\] running... \n",
                        rf"{PREFIX}\[sleep\] done ✓ \(1\..*s\)\n",
                        f"{PREFIX}\n",
                        rf"{PREFIX}\[echo\] running... \n",
                        f"{PREFIX}hi\n",
                        rf"{PREFIX}\[echo\] done ✓ \(0\..*s\)\n",
                        f"{PREFIX}\n",
                        f"{PREFIX}Done!\n",
                    ]
                ),
                captured.out,
            )
            is not None
        ), prettify_error(captured.out)

    def test_handles_running_pyallel_within_pyallel(
        self, capsys: CaptureFixture[str]
    ) -> None:
        exit_code = main.run(
            "pyallel ./tests/assets/test_handle_multiple_signals.sh -t", "-n", "-t"
        )
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        assert captured.out.splitlines(keepends=True) == (
            [
                f"{PREFIX}Running commands...\n",
                f"{PREFIX}\n",
                f"{PREFIX}[pyallel] running... \n",
                f"{PREFIX}{PREFIX}Running commands...\n",
                f"{PREFIX}{PREFIX}\n",
                f"{PREFIX}{PREFIX}[./tests/assets/test_handle_multiple_signals.sh] running... \n",
                f"{PREFIX}{PREFIX}hi\n",
                f"{PREFIX}{PREFIX}bye\n",
                f"{PREFIX}{PREFIX}[./tests/assets/test_handle_multiple_signals.sh] done ✓\n",
                f"{PREFIX}{PREFIX}\n",
                f"{PREFIX}{PREFIX}Done!\n",
                f"{PREFIX}[pyallel] done ✓\n",
                f"{PREFIX}\n",
                f"{PREFIX}Done!\n",
            ]
        )

    @pytest.mark.parametrize("wait", ["0.1", "0.5"])
    def test_handles_single_command_output_with_delayed_newlines(
        self, capsys: CaptureFixture[str], wait: str
    ) -> None:
        exit_code = main.run(f"sh -c 'printf hi; sleep {wait}; echo bye'", "-n", "-t")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        assert captured.out.splitlines(keepends=True) == (
            [
                f"{PREFIX}Running commands...\n",
                f"{PREFIX}\n",
                f"{PREFIX}[sh] running... \n",
                f"{PREFIX}hibye\n",
                f"{PREFIX}[sh] done ✓\n",
                f"{PREFIX}\n",
                f"{PREFIX}Done!\n",
            ]
        )

    @pytest.mark.parametrize("wait", ["0.1", "0.5"])
    def test_handles_multiple_command_output_with_delayed_newlines(
        self, capsys: CaptureFixture[str], wait: str
    ) -> None:
        exit_code = main.run(
            f"sh -c 'printf hi; sleep {wait}; echo bye'",
            f"sh -c 'printf hi; sleep {wait}; echo bye'",
            "-n",
            "-t",
        )
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        assert captured.out.splitlines(keepends=True) == (
            [
                f"{PREFIX}Running commands...\n",
                f"{PREFIX}\n",
                f"{PREFIX}[sh] running... \n",
                f"{PREFIX}hibye\n",
                f"{PREFIX}[sh] done ✓\n",
                f"{PREFIX}\n",
                f"{PREFIX}[sh] running... \n",
                f"{PREFIX}hibye\n",
                f"{PREFIX}[sh] done ✓\n",
                f"{PREFIX}\n",
                f"{PREFIX}Done!\n",
            ]
        )

    def test_handles_invalid_executable(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run("invalid_exe", "-n", "-t")
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)
        assert (
            captured.out == f"{PREFIX}Error: executables [invalid_exe] were not found\n"
        )

    def test_handles_many_invalid_executables(
        self, capsys: CaptureFixture[str]
    ) -> None:
        exit_code = main.run("invalid_exe", "other_invalid_exe", "-n", "-t")
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)
        assert (
            captured.out
            == f"{PREFIX}Error: executables [invalid_exe, other_invalid_exe] were not found\n"
        )

    def test_does_not_run_executables_on_parsing_error(
        self, capsys: CaptureFixture[str]
    ) -> None:
        exit_code = main.run("invalid_exe", "other_invalid_exe", "sleep 10", "-n", "-t")
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)
        assert (
            captured.out
            == f"{PREFIX}Error: executables [invalid_exe, other_invalid_exe] were not found\n"
        )
        status = subprocess.run(["pgrep", "-f", "^sleep 10$"])
        assert status.returncode == 1, "sleep shouldn't be running!"

    @pytest.mark.parametrize(
        "signal,exit_code", ((signal.SIGINT, 130), (signal.SIGTERM, 143))
    )
    def test_handles_signals(self, signal: int, exit_code: int) -> None:
        process = subprocess.Popen(
            [
                "pyallel",
                "./tests/assets/test_process_interrupt_with_trapped_output.sh",
                "-n",
                "-t",
            ],
            env=os.environ.copy(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        time.sleep(0.3)
        process.send_signal(signal)
        assert process.stdout is not None
        out = process.stdout.read()
        assert process.wait() == exit_code, prettify_error(out.decode())
        assert out.decode().splitlines(keepends=True) == (
            [
                f"{PREFIX}Running commands...\n",
                f"{PREFIX}\n",
                f"{PREFIX}[./tests/assets/test_process_interrupt_with_trapped_output.sh] running... \n",
                f"{PREFIX}hi\n",
                f"{PREFIX}\n",
                f"{PREFIX}Interrupt!\n",
                f"{PREFIX}\n",
                f"{PREFIX}error\n",
                f"{PREFIX}[./tests/assets/test_process_interrupt_with_trapped_output.sh] failed ✗\n",
                f"{PREFIX}\n",
            ]
        )

    @pytest.mark.parametrize(
        "signal,exit_code", ((signal.SIGINT, 130), (signal.SIGTERM, 143))
    )
    def test_handles_multiple_signals(self, signal: int, exit_code: int) -> None:
        process = subprocess.Popen(
            [
                "pyallel",
                "./tests/assets/test_handle_multiple_signals.sh",
                "-n",
                "-t",
            ],
            env=os.environ.copy(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        time.sleep(0.3)
        process.send_signal(signal)
        time.sleep(0.1)
        process.send_signal(signal)
        assert process.stdout is not None
        out = process.stdout.read()
        assert process.wait() == exit_code, prettify_error(out.decode())
        assert out.decode().splitlines(keepends=True) == (
            [
                f"{PREFIX}Running commands...\n",
                f"{PREFIX}\n",
                f"{PREFIX}[./tests/assets/test_handle_multiple_signals.sh] running... \n",
                f"{PREFIX}hi\n",
                f"{PREFIX}\n",
                f"{PREFIX}Interrupt!\n",
                f"{PREFIX}\n",
                f"{PREFIX}[./tests/assets/test_handle_multiple_signals.sh] failed ✗\n",
                f"{PREFIX}\n",
                f"{PREFIX}Abort!\n",
            ]
        )
