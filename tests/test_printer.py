import pytest
from pyallel.colours import Colours
from pyallel.printer import Printer, get_num_lines, set_process_lines
from pyallel.process import Process, ProcessOutput
from pyallel.process_group import ProcessGroupOutput


@pytest.mark.parametrize(
    "output,columns,expected",
    (
        (
            "Hello Mr Anderson",
            20,
            1,
        ),
        (
            "Hello Mr Anderson\nIt is inevitable",
            20,
            2,
        ),
        (
            "Hello Mr Anderson\nIt is inevitable\nHAHAHAHAH",
            20,
            3,
        ),
    ),
)
def test_get_num_lines(output: str, columns: int, expected: int) -> None:
    assert get_num_lines(output, columns) == expected


@pytest.mark.parametrize("columns,lines", ((8, 3), (5, 4)))
def test_get_num_lines_with_columns(columns: int, lines: int) -> None:
    assert get_num_lines("Hello Mr Anderson", columns=columns) == lines


def test_get_num_lines_with_long_command() -> None:
    # First line is a 800 length string, which divides evenly into `200`
    line = "long" * 200
    assert get_num_lines(f"{line}\nLong output", columns=200) == 5


def test_get_num_lines_with_long_line() -> None:
    assert get_num_lines(" " * 250, columns=200) == 2


@pytest.mark.parametrize("chars", ["\x1B[0m", "\x1B(B"])
def test_get_num_lines_ignores_ansi_chars(chars: str) -> None:
    assert get_num_lines(chars * 100, columns=10) == 1


def test_set_process_lines() -> None:
    output = ProcessGroupOutput(
        id=1,
        processes=[
            ProcessOutput(
                id=1,
                process=Process(1, "echo first; echo second"),
                data="first\nsecond\n",
            )
        ],
    )

    set_process_lines(output, lines=58)

    assert output.processes[0].lines == 58


def test_printer_generate_process_output() -> None:
    printer = Printer(colours=Colours.from_colour("no"))
    process = Process(1, "echo first; echo second")
    process.run()
    process.wait()

    output = printer.generate_process_output(
        ProcessOutput(
            id=1,
            process=process,
            data="first\nsecond\n",
        )
    )

    assert output == [
        (False, "[echo first; echo second] done ✔", "\n"),
        (True, "first", "\n"),
        (True, "second", "\n"),
    ]


def test_printer_generate_process_output_status() -> None:
    printer = Printer(colours=Colours.from_colour("no"))
    process = Process(1, "echo first; echo second")
    process.run()
    process.wait()

    output = printer.generate_process_output_status(
        ProcessOutput(
            id=1,
            process=process,
            data="first\nsecond\n",
        )
    )

    assert output == "[echo first; echo second] done ✔"


def test_printer_generate_process_group_output() -> None:
    printer = Printer(colours=Colours.from_colour("no"))
    process1 = Process(1, "echo first; echo second")
    process2 = Process(1, "echo third; echo fourth")
    process1.run()
    process2.run()
    process1.wait()
    process2.wait()

    output = printer.generate_process_group_output(
        ProcessGroupOutput(
            id=1,
            processes=[
                ProcessOutput(
                    id=1,
                    process=process1,
                    data="first\nsecond\n",
                ),
                ProcessOutput(
                    id=2,
                    process=process2,
                    data="third\nfourth\n",
                ),
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
