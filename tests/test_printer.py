from __future__ import annotations

import pytest

from pyallel import constants
from pyallel.colours import Colours
from pyallel.errors import PyallelError
from pyallel.printer import InteractiveConsolePrinter, NonInteractiveConsolePrinter, generate_summary
from pyallel.process import ProcessOutput
from pyallel.process_group import ProcessGroupOutput


class TestInteractiveConsolePrinter:
    def test_generate_process_group_output(self) -> None:
        printer = InteractiveConsolePrinter(colours=Colours.from_colour("no"))

        output = printer.generate_process_group_output(
            ProcessGroupOutput(
                id=1,
                processes=[
                    ProcessOutput(id=1, command="echo first; echo second", poll=0, data="first\nsecond\n"),
                    ProcessOutput(id=2, command="echo third; echo fourth", poll=0, data="third\nfourth\n"),
                ],
            ),
        )

        assert output == [
            (False, "[echo first; echo second] done ✔", "\n"),
            (True, "first", "\n"),
            (True, "second", "\n"),
            (False, "[echo third; echo fourth] done ✔", "\n"),
            (True, "third", "\n"),
            (True, "fourth", "\n"),
        ]

    def test_generate_process_output(self) -> None:
        printer = InteractiveConsolePrinter(colours=Colours.from_colour("no"))

        output = printer.generate_process_output(
            ProcessOutput(id=1, command="echo first; echo second", poll=0, data="first\nsecond\n"),
        )

        assert output == [
            (False, "[echo first; echo second] done ✔", "\n"),
            (True, "first", "\n"),
            (True, "second", "\n"),
        ]

    def test_generate_process_output_status(self) -> None:
        printer = InteractiveConsolePrinter(colours=Colours.from_colour("no"))

        output = printer.generate_process_output_status(
            ProcessOutput(id=1, command="echo first; echo second", poll=0, data="first\nsecond\n"),
        )

        assert output == "[echo first; echo second] done ✔"

    def test_printer_generate_process_output_status_handles_long_command(self) -> None:
        printer = InteractiveConsolePrinter(colours=Colours.from_colour("no"))

        output = printer.generate_process_output_status(
            ProcessOutput(id=1, command="echo first; echo second", poll=0, data="first\nsecond\n"), columns=5
        )

        assert output == "[echo first; ech...] done ✔"

    def test_set_process_lines(self) -> None:
        output = ProcessGroupOutput(id=1, processes=[ProcessOutput(id=1, data="first\nsecond\n")])
        assert output.processes[0].allocated_lines == 0

        InteractiveConsolePrinter().set_process_lines(output, lines=58)

        assert output.processes[0].allocated_lines == 58

    def test_set_process_lines_shares_lines_across_processes(self) -> None:
        output = ProcessGroupOutput(
            id=1,
            processes=[
                ProcessOutput(id=1, data="first\nsecond\n"),
                ProcessOutput(id=2, data="first\nsecond\n"),
                ProcessOutput(id=3, data="first\nsecond\n"),
            ],
        )

        InteractiveConsolePrinter().set_process_lines(output, lines=59)

        assert output.processes[0].allocated_lines == 53
        assert output.processes[1].allocated_lines == 3
        assert output.processes[2].allocated_lines == 3

    def test_set_process_lines_shares_lines_across_many_more_processes(self) -> None:
        output = ProcessGroupOutput(
            id=1,
            processes=[ProcessOutput(id=i, data="first\nsecond\n") for i in range(1, 60)],
        )

        InteractiveConsolePrinter().set_process_lines(output, lines=59)

        for i in range(59):
            assert output.processes[i].allocated_lines == 1, f"process index {i}"

    @pytest.mark.parametrize(
        ("lines", "lines1", "lines2", "lines3", "expected_lines1", "expected_lines2", "expected_lines3"),
        [
            pytest.param(
                59,
                0.4,
                0.2,
                0.2,
                37,
                11,
                11,
                id="59 lines shared between 3 processes with the remainder going to the process with the most output",
            ),
            pytest.param(59, 1.0, 0.0, 0.0, 59, 0, 0, id="All lines given to first process"),
            pytest.param(59, 0.5, 0.0, 0.0, 53, 3, 3, id="29 lines given to first process"),
        ],
    )
    def test_set_process_lines_with_fixed_and_dynamic_lines(
        self,
        lines: int,
        lines1: float,
        lines2: float,
        lines3: float,
        expected_lines1: int,
        expected_lines2: int,
        expected_lines3: int,
    ) -> None:
        output = ProcessGroupOutput(
            id=1,
            processes=[
                ProcessOutput(id=1, data="first\nsecond\n", allocated_percentage_lines=lines1),
                ProcessOutput(id=2, data="first\nsecond\n", allocated_percentage_lines=lines2),
                ProcessOutput(id=3, data="first\nsecond\n", allocated_percentage_lines=lines3),
            ],
        )

        InteractiveConsolePrinter().set_process_lines(output, lines=lines)

        assert output.processes[0].allocated_lines == expected_lines1
        assert output.processes[1].allocated_lines == expected_lines2
        assert output.processes[2].allocated_lines == expected_lines3


class TestNonInteractiveConsolePrinter:
    def test_generate_process_header(self) -> None:
        printer = NonInteractiveConsolePrinter(colours=Colours.from_colour("no"))

        output = printer.generate_process_header(command="echo first; echo second")

        assert output == "[echo first; echo second] running..."

    def test_generate_process_footer(self) -> None:
        printer = NonInteractiveConsolePrinter(colours=Colours.from_colour("no"))

        output = printer.generate_process_footer(
            ProcessOutput(id=1, command="echo first; echo second", poll=0, data="first\nsecond\n"),
        )

        assert output == "[echo first; echo second] done ✔"

    def test_generate_process_output(self) -> None:
        printer = NonInteractiveConsolePrinter(colours=Colours.from_colour("no"))

        output = printer.generate_process_output(
            ProcessOutput(id=1, command="echo first; echo second", poll=0, data="first\nsecond\n"),
        )

        assert output == [
            (True, "first", "\n"),
            (True, "second", "\n"),
        ]


def test_generate_summary_ok_command() -> None:
    summary = generate_summary(
        process_group_outputs=[
            ProcessGroupOutput(
                id=1,
                processes=[ProcessOutput(id=1, command="echo hi", poll=0)],
            )
        ],
        colours=Colours.from_colour("no"),
        include_timer=True,
    )

    assert summary == [
        "Results Summary",
        "=====================",
        f"done {constants.TICK} 0.0s [echo hi]",
    ]


def test_generate_summary_failed_command() -> None:
    summary = generate_summary(
        process_group_outputs=[
            ProcessGroupOutput(
                id=1,
                processes=[ProcessOutput(id=1, command="echo hi", poll=1)],
            )
        ],
        colours=Colours.from_colour("no"),
        include_timer=True,
    )

    assert summary == [
        "Results Summary",
        "=======================",
        f"failed {constants.X} 0.0s [echo hi]",
    ]


def test_generate_summary_not_started_command() -> None:
    summary = generate_summary(
        process_group_outputs=[
            ProcessGroupOutput(
                id=1,
                processes=[ProcessOutput(id=1, command="echo hi", poll=-1)],
            )
        ],
        colours=Colours.from_colour("no"),
        include_timer=True,
    )

    assert summary == [
        "Results Summary",
        "=====================",
        "not started [echo hi]",
    ]


def test_generate_summary_multiple_groups() -> None:
    summary = generate_summary(
        process_group_outputs=[
            ProcessGroupOutput(
                id=1,
                processes=[ProcessOutput(id=1, command="echo hi", poll=0)],
            ),
            ProcessGroupOutput(
                id=2,
                processes=[ProcessOutput(id=2, command="echo bye", poll=0)],
            ),
        ],
        colours=Colours.from_colour("no"),
        include_timer=True,
    )

    assert summary == [
        "Results Summary",
        "=================================",
        f"done {constants.TICK} 0.0s (group: 1) [echo hi]",
        f"done {constants.TICK} 0.0s (group: 2) [echo bye]",
    ]


def test_generate_summary_skips_running_command() -> None:
    with pytest.raises(PyallelError, match="no commands provided or no commands have completed"):
        generate_summary(
            process_group_outputs=[
                ProcessGroupOutput(
                    id=1,
                    processes=[ProcessOutput(id=1, command="echo hi", poll=None)],
                )
            ],
            colours=Colours.from_colour("no"),
            include_timer=False,
        )


def test_generate_summary_no_timer() -> None:
    summary = generate_summary(
        process_group_outputs=[
            ProcessGroupOutput(
                id=1,
                processes=[ProcessOutput(id=1, command="echo hi", poll=0)],
            )
        ],
        colours=Colours.from_colour("no"),
        include_timer=False,
    )

    assert summary == [
        "Results Summary",
        "================",
        f"done {constants.TICK} [echo hi]",
    ]
