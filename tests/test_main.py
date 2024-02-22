import os
import re
import signal
import subprocess
import time
from pyallel import main
from pytest import CaptureFixture

import pytest


def prettify_error(out: str) -> str:
    return f"Got an error\n\n{out}"


PREFIX = "=> "


class TestStreamedMode:
    """Test streamed mode with interactivity

    NOTE: These tests can only verify the exit code consistently
    as terminal output is re-written which isn't easy to consistently assert against
    """

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

    def test_handles_invalid_executable(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run("invalid_exe", "-t")
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)
        assert captured.out == "Error: executables [invalid_exe] were not found\n"

    def test_handles_many_invalid_executables(
        self, capsys: CaptureFixture[str]
    ) -> None:
        exit_code = main.run("invalid_exe", "other_invalid_exe", "-t")
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)
        assert (
            captured.out
            == "Error: executables [invalid_exe, other_invalid_exe] were not found\n"
        )

    def test_does_not_run_executables_on_parsing_error(
        self, capsys: CaptureFixture[str]
    ) -> None:
        exit_code = main.run("invalid_exe", "other_invalid_exe", "sleep 10", "-t")
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)
        assert (
            captured.out
            == "Error: executables [invalid_exe, other_invalid_exe] were not found\n"
        )
        status = subprocess.run(["pgrep", "-f", "^sleep 10$"])
        assert status.returncode == 1, "sleep shouldn't be running!"

    def test_handles_interrupt_signal(self) -> None:
        process = subprocess.Popen(
            ["pyallel", "./tests/assets/test_process_interrupt_with_trapped_output.sh"],
            env=os.environ.copy(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        time.sleep(0.5)
        process.send_signal(signal.SIGINT)
        assert process.wait() == 2


class TestStreamedNonInteractiveMode:
    def test_run_single_command(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run("echo 'hi'", "-n", "-t")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        assert captured.out == "".join(
            [
                "Running commands...\n",
                "\n",
                "[echo] running... \n",
                f"{PREFIX}hi\n",
                "[echo] done ✓\n",
                "\n",
                "Success!\n",
            ]
        )

    def test_run_single_command_failure(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run('sh -c "exit 1"', "-n", "-t")
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)
        assert captured.out == "".join(
            [
                "Running commands...\n",
                "\n",
                "[sh] running... \n",
                "[sh] failed ✗\n",
                "\n",
                "A command failed!\n",
            ]
        )

    def test_run_single_command_with_env(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run("TEST_VAR=1 echo 'hi'", "-n", "-t")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        assert captured.out == "".join(
            [
                "Running commands...\n",
                "\n",
                "[echo] running... \n",
                f"{PREFIX}hi\n",
                "[echo] done ✓\n",
                "\n",
                "Success!\n",
            ]
        )

    def test_run_multiple_commands(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run(
            "sh -c 'sleep 0.1; echo \"first\"'", "echo 'hi'", "-n", "-t"
        )
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        assert captured.out == "".join(
            [
                "Running commands...\n",
                "\n",
                "[sh] running... \n",
                f"{PREFIX}first\n",
                "[sh] done ✓\n",
                "\n",
                "[echo] running... \n",
                f"{PREFIX}hi\n",
                "[echo] done ✓\n",
                "\n",
                "Success!\n",
            ]
        )

    def test_run_multiple_commands_single_failure(
        self, capsys: CaptureFixture[str]
    ) -> None:
        exit_code = main.run('sh -c "exit 1"', 'echo "hi"', "-n", "-t")
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)
        assert captured.out == "".join(
            [
                "Running commands...\n",
                "\n",
                "[sh] running... \n",
                "[sh] failed ✗\n",
                "\n",
                "[echo] running... \n",
                f"{PREFIX}hi\n",
                "[echo] done ✓\n",
                "\n",
                "A command failed!\n",
            ]
        )

    def test_run_multiple_commands_multiple_failures(
        self,
        capsys: CaptureFixture[str],
    ) -> None:
        exit_code = main.run('sh -c "exit 1"', 'sh -c "exit 1"', "-n", "-t")
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)
        assert captured.out == "".join(
            [
                "Running commands...\n",
                "\n",
                "[sh] running... \n",
                "[sh] failed ✗\n",
                "\n",
                "[sh] running... \n",
                "[sh] failed ✗\n",
                "\n",
                "A command failed!\n",
            ]
        )

    def test_run_verbose_mode(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run("echo 'hi'", "-n", "-V", "-t")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        assert captured.out == "".join(
            [
                "Running commands...\n",
                "\n",
                "[echo hi] running... \n",
                f"{PREFIX}hi\n",
                "[echo hi] done ✓\n",
                "\n",
                "Success!\n",
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
                        "Running commands...\n",
                        "\n",
                        r"\[echo\] running... \n",
                        f"{PREFIX}hi\n",
                        r"\[echo\] done ✓ \(0\..*\)\n",
                        "\n",
                        "Success!\n",
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
                        "Running commands...\n",
                        "\n",
                        r"\[sleep\] running... \n",
                        r"\[sleep\] done ✓ \(1\..*s\)\n",
                        "\n",
                        r"\[echo\] running... \n",
                        f"{PREFIX}hi\n",
                        r"\[echo\] done ✓ \(0\..*s\)\n",
                        "\n",
                        "Success!\n",
                    ]
                ),
                captured.out,
            )
            is not None
        ), prettify_error(captured.out)

    @pytest.mark.parametrize("wait", ["0.1", "0.5"])
    def test_handles_single_command_output_with_delayed_newlines(
        self, capsys: CaptureFixture[str], wait: str
    ) -> None:
        exit_code = main.run(f"sh -c 'printf hi; sleep {wait}; echo bye'", "-n", "-t")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        assert captured.out == "".join(
            [
                "Running commands...\n",
                "\n",
                "[sh] running... \n",
                f"{PREFIX}hibye\n",
                "[sh] done ✓\n",
                "\n",
                "Success!\n",
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
        assert captured.out == "".join(
            [
                "Running commands...\n",
                "\n",
                "[sh] running... \n",
                f"{PREFIX}hibye\n",
                "[sh] done ✓\n",
                "\n",
                "[sh] running... \n",
                f"{PREFIX}hibye\n",
                "[sh] done ✓\n",
                "\n",
                "Success!\n",
            ]
        )

    def test_handles_invalid_executable(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run("invalid_exe", "-n", "-t")
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)
        assert captured.out == "Error: executables [invalid_exe] were not found\n"

    def test_handles_many_invalid_executables(
        self, capsys: CaptureFixture[str]
    ) -> None:
        exit_code = main.run("invalid_exe", "other_invalid_exe", "-n", "-t")
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)
        assert (
            captured.out
            == "Error: executables [invalid_exe, other_invalid_exe] were not found\n"
        )

    def test_does_not_run_executables_on_parsing_error(
        self, capsys: CaptureFixture[str]
    ) -> None:
        exit_code = main.run("invalid_exe", "other_invalid_exe", "sleep 10", "-n", "-t")
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)
        assert (
            captured.out
            == "Error: executables [invalid_exe, other_invalid_exe] were not found\n"
        )
        status = subprocess.run(["pgrep", "-f", "^sleep 10$"])
        assert status.returncode == 1, "sleep shouldn't be running!"

    def test_handles_interrupt_signal(self) -> None:
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
        time.sleep(0.5)
        process.send_signal(signal.SIGINT)
        assert process.stdout is not None
        out = process.stdout.read()
        assert process.wait() == 2, prettify_error(out.decode())
        assert out.decode() == "".join(
            [
                "Running commands...\n",
                "\n",
                "[./tests/assets/test_process_interrupt_with_trapped_output.sh] running... \n",
                f"{PREFIX}hi\n",
                f"{PREFIX}error\n",
                "[./tests/assets/test_process_interrupt_with_trapped_output.sh] failed ✗\n",
                "\n",
                "Interrupt!\n",
            ]
        )
