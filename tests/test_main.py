import subprocess
from pyallel import main
from pytest import CaptureFixture

import pytest


def prettify_error(out: str) -> str:
    return f"Got an error\n\n{out}"


class TestNonStreamedMode:
    def test_run_single_command(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run("echo 'hi'", "-s")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        assert captured.out == "".join(
            [
                "Running commands...\n",
                "\n",
                "[echo] done ✓\n",
                "    hi\n",
                "\n",
                "Success!\n",
            ]
        )

    def test_run_single_command_failure(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run('sh -c "exit 1"', "-s")
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)
        assert captured.out == "".join(
            [
                "Running commands...\n",
                "\n",
                "[sh] failed ✗\n",
                "\n",
                "A command failed!\n",
            ]
        )

    def test_run_single_command_with_env(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run("TEST_VAR=1 echo 'hi'", "-s")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        assert captured.out == "".join(
            [
                "Running commands...\n",
                "\n",
                "[echo] done ✓\n",
                "    hi\n",
                "\n",
                "Success!\n",
            ]
        )

    def test_run_single_command_with_tail_mode(
        self, capsys: CaptureFixture[str]
    ) -> None:
        exit_code = main.run("tail=10 :: echo 'hi'", "-s")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        assert captured.out == "".join(
            [
                "Running commands...\n",
                "\n",
                "[echo] done ✓\n",
                "    hi\n",
                "\n",
                "Success!\n",
            ]
        )

    def test_run_multiple_commands(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run("sh -c 'sleep 0.1; echo \"first\"'", "echo 'hi'", "-s")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        assert captured.out == "".join(
            [
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
        )

    def test_run_multiple_commands_single_failure(
        self, capsys: CaptureFixture[str]
    ) -> None:
        exit_code = main.run('sh -c "exit 1"', 'echo "hi"', "-s")
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)
        assert captured.out == "".join(
            [
                "Running commands...\n",
                "\n",
                "[sh] failed ✗\n",
                "\n",
                "[echo] done ✓\n",
                "    hi\n",
                "\n",
                "A command failed!\n",
            ]
        )

    def test_run_multiple_commands_multiple_failures(
        self,
        capsys: CaptureFixture[str],
    ) -> None:
        exit_code = main.run('sh -c "exit 1"', 'sh -c "exit 1"', "-s")
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)
        assert captured.out == "".join(
            [
                "Running commands...\n",
                "\n",
                "[sh] failed ✗\n",
                "\n",
                "[sh] failed ✗\n",
                "\n",
                "A command failed!\n",
            ]
        )

    def test_run_verbose_mode(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run("echo 'hi'", "-V", "-s")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        assert captured.out == "".join(
            [
                "Running commands...\n",
                "\n",
                "[echo hi] done ✓\n",
                "    hi\n",
                "\n",
                "Success!\n",
            ]
        )

    def test_run_timer_mode(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run("echo 'hi'", "-t", "-s")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        assert captured.out == "".join(
            [
                "Running commands...\n",
                "\n",
                "[echo] done in 0s ✓\n",
                "    hi\n",
                "\n",
                "Success!\n",
                "\n",
                "Time taken : 0s\n",
            ]
        )

    @pytest.mark.parametrize("wait", ["0.1", "0.5"])
    def test_handles_single_command_output_with_delayed_newlines(
        self, capsys: CaptureFixture[str], wait: str
    ) -> None:
        exit_code = main.run(f"sh -c 'echo -n hi; sleep {wait}; echo bye'", "-s")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        assert captured.out == "".join(
            [
                "Running commands...\n",
                "\n",
                "[sh] done ✓\n",
                "    hibye\n",
                "\n",
                "Success!\n",
            ]
        )

    @pytest.mark.parametrize("wait", ["0.1", "0.5"])
    def test_handles_multiple_command_output_with_delayed_newlines(
        self, capsys: CaptureFixture[str], wait: str
    ) -> None:
        exit_code = main.run(
            f"sh -c 'echo -n hi; sleep {wait}; echo bye'",
            f"sh -c 'echo -n hi; sleep {wait}; echo bye'",
            "-s",
        )
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        assert captured.out == "".join(
            [
                "Running commands...\n",
                "\n",
                "[sh] done ✓\n",
                "    hibye\n",
                "\n",
                "[sh] done ✓\n",
                "    hibye\n",
                "\n",
                "Success!\n",
            ]
        )

    def test_handles_invalid_executable(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run("invalid_exe", "-s")
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)
        assert captured.out == "Error: executables [invalid_exe] were not found\n"

    def test_handles_many_invalid_executables(
        self, capsys: CaptureFixture[str]
    ) -> None:
        exit_code = main.run("invalid_exe", "other_invalid_exe", "-s")
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)
        assert (
            captured.out
            == "Error: executables [invalid_exe, other_invalid_exe] were not found\n"
        )

    def test_does_not_run_executables_on_parsing_error(
        self, capsys: CaptureFixture[str]
    ) -> None:
        exit_code = main.run("invalid_exe", "other_invalid_exe", "sleep 10", "-s")
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)
        assert (
            captured.out
            == "Error: executables [invalid_exe, other_invalid_exe] were not found\n"
        )
        status = subprocess.run(["pgrep", "-f", "^sleep 10$"])
        assert status.returncode == 1, "sleep shouldn't be running!"


class TestNonStreamedNonInteractiveMode:
    def test_run_single_command(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run("echo 'hi'", "-n", "-s")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        assert captured.out == "".join(
            [
                "Running commands...\n",
                "\n",
                "[echo] done ✓\n",
                "    hi\n",
                "\n",
                "Success!\n",
            ]
        )

    def test_run_single_command_failure(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run('sh -c "exit 1"', "-n", "-s")
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)
        assert captured.out == "".join(
            [
                "Running commands...\n",
                "\n",
                "[sh] failed ✗\n",
                "\n",
                "A command failed!\n",
            ]
        )

    def test_run_single_command_with_env(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run("TEST_VAR=1 echo 'hi'", "-n", "-s")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        assert captured.out == "".join(
            [
                "Running commands...\n",
                "\n",
                "[echo] done ✓\n",
                "    hi\n",
                "\n",
                "Success!\n",
            ]
        )

    def test_run_single_command_with_tail_mode(
        self, capsys: CaptureFixture[str]
    ) -> None:
        exit_code = main.run("tail=10 :: echo 'hi'", "-n", "-s")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        assert captured.out == "".join(
            [
                "Running commands...\n",
                "\n",
                "[echo] done ✓\n",
                "    hi\n",
                "\n",
                "Success!\n",
            ]
        )

    def test_run_multiple_commands(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run(
            "sh -c 'sleep 0.1; echo \"first\"'", "echo 'hi'", "-n", "-s"
        )
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        assert captured.out == "".join(
            [
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
        )

    def test_run_multiple_commands_single_failure(
        self, capsys: CaptureFixture[str]
    ) -> None:
        exit_code = main.run('sh -c "exit 1"', 'echo "hi"', "-n", "-s")
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)
        assert captured.out == "".join(
            [
                "Running commands...\n",
                "\n",
                "[sh] failed ✗\n",
                "\n",
                "[echo] done ✓\n",
                "    hi\n",
                "\n",
                "A command failed!\n",
            ]
        )

    def test_run_multiple_commands_multiple_failures(
        self,
        capsys: CaptureFixture[str],
    ) -> None:
        exit_code = main.run('sh -c "exit 1"', 'sh -c "exit 1"', "-n", "-s")
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)
        assert captured.out == "".join(
            [
                "Running commands...\n",
                "\n",
                "[sh] failed ✗\n",
                "\n",
                "[sh] failed ✗\n",
                "\n",
                "A command failed!\n",
            ]
        )

    def test_run_verbose_mode(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run("echo 'hi'", "-V", "-n", "-s")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        assert captured.out == "".join(
            [
                "Running commands...\n",
                "\n",
                "[echo hi] done ✓\n",
                "    hi\n",
                "\n",
                "Success!\n",
            ]
        )

    def test_run_timer_mode(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run("echo 'hi'", "-t", "-n", "-s")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        assert captured.out == "".join(
            [
                "Running commands...\n",
                "\n",
                "[echo] done in 0s ✓\n",
                "    hi\n",
                "\n",
                "Success!\n",
                "\n",
                "Time taken : 0s\n",
            ]
        )

    @pytest.mark.parametrize("wait", ["0.1", "0.5"])
    def test_handles_single_command_output_with_delayed_newlines(
        self, capsys: CaptureFixture[str], wait: str
    ) -> None:
        exit_code = main.run(f"sh -c 'echo -n hi; sleep {wait}; echo bye'", "-n", "-s")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        assert captured.out == "".join(
            [
                "Running commands...\n",
                "\n",
                "[sh] done ✓\n",
                "    hibye\n",
                "\n",
                "Success!\n",
            ]
        )

    @pytest.mark.parametrize("wait", ["0.1", "0.5"])
    def test_handles_multiple_command_output_with_delayed_newlines(
        self, capsys: CaptureFixture[str], wait: str
    ) -> None:
        exit_code = main.run(
            f"sh -c 'echo -n hi; sleep {wait}; echo bye'",
            f"sh -c 'echo -n hi; sleep {wait}; echo bye'",
            "-n",
            "-s",
        )
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        assert captured.out == "".join(
            [
                "Running commands...\n",
                "\n",
                "[sh] done ✓\n",
                "    hibye\n",
                "\n",
                "[sh] done ✓\n",
                "    hibye\n",
                "\n",
                "Success!\n",
            ]
        )

    def test_handles_invalid_executable(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run("invalid_exe", "-n", "-s")
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)
        assert captured.out == "Error: executables [invalid_exe] were not found\n"

    def test_handles_many_invalid_executables(
        self, capsys: CaptureFixture[str]
    ) -> None:
        exit_code = main.run("invalid_exe", "other_invalid_exe", "-n", "-s")
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)
        assert (
            captured.out
            == "Error: executables [invalid_exe, other_invalid_exe] were not found\n"
        )

    def test_does_not_run_executables_on_parsing_error(
        self, capsys: CaptureFixture[str]
    ) -> None:
        exit_code = main.run("invalid_exe", "other_invalid_exe", "sleep 10", "-n", "-s")
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)
        assert (
            captured.out
            == "Error: executables [invalid_exe, other_invalid_exe] were not found\n"
        )
        status = subprocess.run(["pgrep", "-f", "^sleep 10$"])
        assert status.returncode == 1, "sleep shouldn't be running!"


class TestStreamedMode:
    """Test streamed mode with interactivity

    NOTE: These tests can only verify the exit code consistently
    as terminal output is re-written which isn't easy to consistently assert against
    """

    def test_run_single_command(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run("echo 'hi'")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)

    def test_run_single_command_with_output(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run("echo 'hi'")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)

    def test_run_single_command_failure(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run('sh -c "exit 1"')
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)

    def test_run_single_command_with_env(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run("TEST_VAR=1 echo 'hi'")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)

    def test_run_single_command_with_tail_mode(
        self, capsys: CaptureFixture[str]
    ) -> None:
        exit_code = main.run("tail=10 :: echo 'hi'")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)

    def test_run_multiple_commands(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run("sh -c 'sleep 0.1; echo \"first\"'", "echo 'hi'")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)

    def test_run_multiple_commands_single_failure(
        self, capsys: CaptureFixture[str]
    ) -> None:
        exit_code = main.run('sh -c "exit 1"', 'echo "hi"')
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)

    def test_run_multiple_commands_multiple_failures(
        self,
        capsys: CaptureFixture[str],
    ) -> None:
        exit_code = main.run('sh -c "exit 1"', 'sh -c "exit 1"')
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)

    def test_run_verbose_mode(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run("echo 'hi'", "-V")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)

    def test_run_timer_mode(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run("echo 'hi'", "-t")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)

    def test_handles_invalid_executable(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run("invalid_exe")
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)
        assert captured.out == "Error: executables [invalid_exe] were not found\n"

    def test_handles_many_invalid_executables(
        self, capsys: CaptureFixture[str]
    ) -> None:
        exit_code = main.run("invalid_exe", "other_invalid_exe")
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)
        assert (
            captured.out
            == "Error: executables [invalid_exe, other_invalid_exe] were not found\n"
        )

    def test_does_not_run_executables_on_parsing_error(
        self, capsys: CaptureFixture[str]
    ) -> None:
        exit_code = main.run("invalid_exe", "other_invalid_exe", "sleep 10")
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)
        assert (
            captured.out
            == "Error: executables [invalid_exe, other_invalid_exe] were not found\n"
        )
        status = subprocess.run(["pgrep", "-f", "^sleep 10$"])
        assert status.returncode == 1, "sleep shouldn't be running!"


class TestStreamedNonInteractiveMode:
    def test_run_single_command(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run("echo 'hi'", "-n")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        assert captured.out == "".join(
            [
                "Running commands...\n",
                "\n",
                "[echo] running... \n",
                "    hi\n",
                "[echo] done ✓\n",
                "\n",
                "Success!\n",
            ]
        )

    def test_run_single_command_failure(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run('sh -c "exit 1"', "-n")
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
        exit_code = main.run("TEST_VAR=1 echo 'hi'", "-n")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        assert captured.out == "".join(
            [
                "Running commands...\n",
                "\n",
                "[echo] running... \n",
                "    hi\n",
                "[echo] done ✓\n",
                "\n",
                "Success!\n",
            ]
        )

    def test_run_single_command_with_tail_mode(
        self, capsys: CaptureFixture[str]
    ) -> None:
        exit_code = main.run("tail=10 :: echo 'hi'", "-n")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        assert captured.out == "".join(
            [
                "Running commands...\n",
                "\n",
                "[echo] running... \n",
                "    hi\n",
                "[echo] done ✓\n",
                "\n",
                "Success!\n",
            ]
        )

    def test_run_multiple_commands(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run("sh -c 'sleep 0.1; echo \"first\"'", "echo 'hi'", "-n")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        assert captured.out == "".join(
            [
                "Running commands...\n",
                "\n",
                "[sh] running... \n",
                "    first\n",
                "[sh] done ✓\n",
                "\n",
                "[echo] running... \n",
                "    hi\n",
                "[echo] done ✓\n",
                "\n",
                "Success!\n",
            ]
        )

    def test_run_multiple_commands_single_failure(
        self, capsys: CaptureFixture[str]
    ) -> None:
        exit_code = main.run('sh -c "exit 1"', 'echo "hi"', "-n")
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
                "    hi\n",
                "[echo] done ✓\n",
                "\n",
                "A command failed!\n",
            ]
        )

    def test_run_multiple_commands_multiple_failures(
        self,
        capsys: CaptureFixture[str],
    ) -> None:
        exit_code = main.run('sh -c "exit 1"', 'sh -c "exit 1"', "-n")
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
        exit_code = main.run("echo 'hi'", "-n", "-V")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        assert captured.out == "".join(
            [
                "Running commands...\n",
                "\n",
                "[echo hi] running... \n",
                "    hi\n",
                "[echo hi] done ✓\n",
                "\n",
                "Success!\n",
            ]
        )

    def test_run_timer_mode(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run("echo 'hi'", "-n", "-t")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        assert captured.out == "".join(
            [
                "Running commands...\n",
                "\n",
                "[echo] running... \n",
                "    hi\n",
                "[echo] done in 0s ✓\n",
                "\n",
                "Success!\n",
                "\n",
                "Time taken : 0s\n",
            ]
        )

    def test_run_timer_mode_with_longer_first_command(
        self, capsys: CaptureFixture[str]
    ) -> None:
        exit_code = main.run("sleep 1", "echo 'hi'", "-n", "-t")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        assert captured.out == "".join(
            [
                "Running commands...\n",
                "\n",
                "[sleep] running... \n",
                "[sleep] done in 1s ✓\n",
                "\n",
                "[echo] running... \n",
                "    hi\n",
                "[echo] done in 0s ✓\n",
                "\n",
                "Success!\n",
                "\n",
                "Time taken : 1s\n",
            ]
        )

    @pytest.mark.parametrize("wait", ["0.1", "0.5"])
    def test_handles_single_command_output_with_delayed_newlines(
        self, capsys: CaptureFixture[str], wait: str
    ) -> None:
        exit_code = main.run(f"sh -c 'echo -n hi; sleep {wait}; echo bye'", "-n")
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        assert captured.out == "".join(
            [
                "Running commands...\n",
                "\n",
                "[sh] running... \n",
                "    hibye\n",
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
            f"sh -c 'echo -n hi; sleep {wait}; echo bye'",
            f"sh -c 'echo -n hi; sleep {wait}; echo bye'",
            "-n",
        )
        captured = capsys.readouterr()
        assert exit_code == 0, prettify_error(captured.out)
        assert captured.out == "".join(
            [
                "Running commands...\n",
                "\n",
                "[sh] running... \n",
                "    hibye\n",
                "[sh] done ✓\n",
                "\n",
                "[sh] running... \n",
                "    hibye\n",
                "[sh] done ✓\n",
                "\n",
                "Success!\n",
            ]
        )

    def test_handles_invalid_executable(self, capsys: CaptureFixture[str]) -> None:
        exit_code = main.run("invalid_exe", "-n")
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)
        assert captured.out == "Error: executables [invalid_exe] were not found\n"

    def test_handles_many_invalid_executables(
        self, capsys: CaptureFixture[str]
    ) -> None:
        exit_code = main.run("invalid_exe", "other_invalid_exe", "-n")
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)
        assert (
            captured.out
            == "Error: executables [invalid_exe, other_invalid_exe] were not found\n"
        )

    def test_does_not_run_executables_on_parsing_error(
        self, capsys: CaptureFixture[str]
    ) -> None:
        exit_code = main.run("invalid_exe", "other_invalid_exe", "sleep 10", "-n")
        captured = capsys.readouterr()
        assert exit_code == 1, prettify_error(captured.out)
        assert (
            captured.out
            == "Error: executables [invalid_exe, other_invalid_exe] were not found\n"
        )
        status = subprocess.run(["pgrep", "-f", "^sleep 10$"])
        assert status.returncode == 1, "sleep shouldn't be running!"
