import difflib
import os
import re
import signal
import subprocess
import time
from typing import Sequence

import pytest
from pyallel import main
from pytest import CaptureFixture, MonkeyPatch


def prettify_error(out: str) -> str:
    return f"Got an error\n\n{out}"


def compare_output(actual: Sequence[str], expected: Sequence[str]) -> None:
    diff = list(
        difflib.unified_diff(
            actual, expected, fromfile="expected", tofile="actual", lineterm=""
        )
    )
    if diff:
        pytest.fail("\n".join(diff))


PREFIX = "=> "


class TestInteractiveMode:
    """Test interactive mode that re-writes terminal output

    NOTE: These tests can only verify the exit code consistently
    as terminal output is re-written which isn't easy to consistently assert against
    """

    @pytest.fixture(autouse=True)
    def in_tty(self, monkeypatch: MonkeyPatch) -> None:
        # Trick pyallel into thinking we are in an interactive terminal
        # so we can test the interactive mode
        monkeypatch.setattr(main.constants, "IN_TTY", True)  # type: ignore[attr-defined]

    def test_run_single_command(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.entry_point("echo hi", "-t")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)

    def test_run_single_command_no_quotes(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.entry_point("echo", "hi", "-t")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)

    def test_run_single_command_with_output(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.entry_point("echo hi", "-t")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)

    def test_run_single_command_failure(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.entry_point("exit 1", "-t")
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)

    def test_run_single_command_with_env(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.entry_point("TEST_VAR=1 echo hi", "-t")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)

    def test_run_multiple_commands(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.entry_point("sleep 0.1; echo first", "echo hi", "-t")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)

    def test_run_multiple_commands_no_quotes(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.entry_point("echo", "first", "echo", "hi", "-t")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)

    def test_run_multiple_commands_single_failure(
        self, capsys: CaptureFixture[str]
    ) -> None:
        exit_code = main.entry_point("exit 1", "echo hi", "-t")
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)

    def test_run_multiple_commands_multiple_failures(
        self,
        capsys: CaptureFixture[str],
    ) -> None:
        exit_code = main.entry_point("exit 1", "exit 1", "-t")
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)

    def test_run_mulitiple_dependant_commands(
        self, capsys: CaptureFixture[str]
    ) -> None:
        exit_code = main.entry_point("echo first", ":::", "echo hi", "-t")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)

    def test_run_mulitiple_dependant_commands_single_failure(
        self, capsys: CaptureFixture[str]
    ) -> None:
        exit_code = main.entry_point("exit 1", ":::", "echo hi", "-t")
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)

    def test_run_timer_mode(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.entry_point("echo hi")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)

    def test_run_with_lines_modifier(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.entry_point("lines=50 :::: echo hi")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)

    @pytest.mark.parametrize("value", ["110", "-1", "0", "invalid", ""])
    def test_run_with_lines_modifier_invalid_value(
        self, capsys: CaptureFixture[str], value: str
    ) -> None:
        exit_code = main.entry_point(f"lines={value} :::: echo hi", "--colour", "no")
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)
        compare_output(
            actual=captured.out.splitlines(),
            expected=[
                "Error: lines modifier must be a number between 1 and 100",
            ],
        )

    def test_run_with_lines_modifier_exceeds_100(
        self, capsys: CaptureFixture[str]
    ) -> None:
        exit_code = main.entry_point(
            "lines=60 :::: echo hi",
            "::",
            "lines=80 :::: echo bye",
            "--colour",
            "no",
        )
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)
        compare_output(
            actual=captured.out.splitlines(),
            expected=[
                "Error: lines modifier must not exceed 100 across all processes within each process group",
            ],
        )

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

    @pytest.mark.parametrize(
        "signal,exit_code", ((signal.SIGINT, 130), (signal.SIGTERM, 143))
    )
    def test_handles_multiple_signals_with_dependant_commands(
        self, signal: int, exit_code: int
    ) -> None:
        process = subprocess.Popen(
            [
                "pyallel",
                "./tests/assets/test_handle_multiple_signals.sh",
                ":::",
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


class TestNonInteractiveMode:
    def test_run_single_command(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.entry_point("echo hi", "-n", "-t", "--colour", "no")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        compare_output(
            actual=captured.out.splitlines(),
            expected=[
                "[echo hi] running... ",
                f"{PREFIX}hi",
                "[echo hi] done ✔",
            ],
        )

    def test_run_single_command_no_quotes(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.entry_point("echo", "hi", "-n", "-t", "--colour", "no")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        compare_output(
            actual=captured.out.splitlines(),
            expected=[
                "[echo hi] running... ",
                f"{PREFIX}hi",
                "[echo hi] done ✔",
            ],
        )

    def test_run_single_command_failure(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.entry_point("exit 1", "-n", "-t", "--colour", "no")
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)
        compare_output(
            actual=captured.out.splitlines(),
            expected=[
                "[exit 1] running... ",
                "[exit 1] failed ✘",
                "",
                "ERROR: the following commands failed",
                "   exit 1",
            ],
        )

    def test_run_single_command_with_env(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.entry_point("TEST_VAR=1 echo hi", "-n", "-t", "--colour", "no")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        compare_output(
            actual=captured.out.splitlines(),
            expected=[
                "[TEST_VAR=1 echo hi] running... ",
                f"{PREFIX}hi",
                "[TEST_VAR=1 echo hi] done ✔",
            ],
        )

    def test_run_multiple_commands(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.entry_point(
            "sleep 0.1; echo first", "::", "echo hi", "-n", "-t", "--colour", "no"
        )
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        compare_output(
            actual=captured.out.splitlines(),
            expected=[
                "[sleep 0.1; echo first] running... ",
                f"{PREFIX}first",
                "[sleep 0.1; echo first] done ✔",
                "[echo hi] running... ",
                f"{PREFIX}hi",
                "[echo hi] done ✔",
            ],
        )

    def test_run_multiple_commands_no_quotes(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.entry_point(
            "echo", "first", "::", "echo", "hi", "-n", "-t", "--colour", "no"
        )
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        compare_output(
            actual=captured.out.splitlines(),
            expected=[
                "[echo first] running... ",
                f"{PREFIX}first",
                "[echo first] done ✔",
                "[echo hi] running... ",
                f"{PREFIX}hi",
                "[echo hi] done ✔",
            ],
        )

    def test_run_multiple_commands_single_failure(
        self, capsys: CaptureFixture[str]
    ) -> None:
        exit_code = main.entry_point(
            "exit 1", "::", "echo hi", "-n", "-t", "--colour", "no"
        )
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)
        compare_output(
            actual=captured.out.splitlines(),
            expected=[
                "[exit 1] running... ",
                "[exit 1] failed ✘",
                "[echo hi] running... ",
                f"{PREFIX}hi",
                "[echo hi] done ✔",
                "",
                "ERROR: the following commands failed",
                "   exit 1",
            ],
        )

    def test_run_multiple_commands_multiple_failures(
        self,
        capsys: CaptureFixture[str],
    ) -> None:
        exit_code = main.entry_point(
            "exit 1", "::", "exit 1", "-n", "-t", "--colour", "no"
        )
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)
        compare_output(
            actual=captured.out.splitlines(),
            expected=[
                "[exit 1] running... ",
                "[exit 1] failed ✘",
                "[exit 1] running... ",
                "[exit 1] failed ✘",
                "",
                "ERROR: the following commands failed",
                "   exit 1",
                "   exit 1",
            ],
        )

    def test_run_mulitiple_dependant_commands(
        self, capsys: CaptureFixture[str]
    ) -> None:
        exit_code = main.entry_point(
            "echo first", ":::", "echo hi", "-n", "-t", "--colour", "no"
        )
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        compare_output(
            actual=captured.out.splitlines(),
            expected=[
                "[echo first] running... ",
                f"{PREFIX}first",
                "[echo first] done ✔",
                "[echo hi] running... ",
                f"{PREFIX}hi",
                "[echo hi] done ✔",
            ],
        )

    def test_run_mulitiple_dependant_commands_single_failure(
        self, capsys: CaptureFixture[str]
    ) -> None:
        exit_code = main.entry_point(
            "exit 1", ":::", "echo hi", "-n", "-t", "--colour", "no"
        )
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)
        compare_output(
            actual=captured.out.splitlines(),
            expected=[
                "[exit 1] running... ",
                "[exit 1] failed ✘",
                "",
                "ERROR: the following commands failed",
                "   exit 1",
            ],
        )

    def test_run_timer_mode(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.entry_point("echo hi", "-n", "--colour", "no")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        assert (
            re.search(
                "".join(
                    [
                        r"\[echo hi\] running... \n",
                        f"{PREFIX}hi\n",
                        r"\[echo hi\] done ✔ \(0\..*\)\n",
                    ]
                ),
                captured.out,
            )
            is not None
        ), prettify_error(captured.out)

    def test_run_with_longer_first_command(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.entry_point("sleep 1", "::", "echo hi", "-n", "--colour", "no")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        assert (
            re.search(
                "".join(
                    [
                        r"\[sleep 1\] running... \n",
                        r"\[sleep 1\] done ✔ \(1\..*s\)\n",
                        r"\[echo hi\] running... \n",
                        f"{PREFIX}hi\n",
                        r"\[echo hi\] done ✔ \(0\..*s\)\n",
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
        exit_code = main.entry_point(
            f"printf hi; sleep {wait}; echo bye", "-n", "-t", "--colour", "no"
        )
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        compare_output(
            actual=captured.out.splitlines(),
            expected=[
                f"[printf hi; sleep {wait}; echo bye] running... ",
                f"{PREFIX}hibye",
                f"[printf hi; sleep {wait}; echo bye] done ✔",
            ],
        )

    @pytest.mark.parametrize("wait", ["0.1", "0.5"])
    def test_handles_multiple_command_output_with_delayed_newlines(
        self, capsys: CaptureFixture[str], wait: str
    ) -> None:
        exit_code = main.entry_point(
            f"printf hi; sleep {wait}; echo bye",
            "::",
            f"printf hi; sleep {wait}; echo bye",
            "-n",
            "-t",
            "--colour",
            "no",
        )
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        compare_output(
            actual=captured.out.splitlines(),
            expected=[
                f"[printf hi; sleep {wait}; echo bye] running... ",
                f"{PREFIX}hibye",
                f"[printf hi; sleep {wait}; echo bye] done ✔",
                f"[printf hi; sleep {wait}; echo bye] running... ",
                f"{PREFIX}hibye",
                f"[printf hi; sleep {wait}; echo bye] done ✔",
            ],
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
                "--colour",
                "no",
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

    @pytest.mark.parametrize(
        "signal,exit_code", ((signal.SIGINT, 130), (signal.SIGTERM, 143))
    )
    def test_handles_multiple_signals_with_dependant_commands(
        self, signal: int, exit_code: int
    ) -> None:
        process = subprocess.Popen(
            [
                "pyallel",
                "./tests/assets/test_handle_multiple_signals.sh",
                ":::",
                "./tests/assets/test_handle_multiple_signals.sh",
                "-n",
                "-t",
                "--colour",
                "no",
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
