import pytest
from pyallel.printer import get_num_lines


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


# def test_get_process_lines() -> None:
#     printer = Printer(colours=Colours.from_colour("no"))
#
#     process_lines = printer.get_process_lines(
#         ProcessGroupManagerOutput(
#             process_group_outputs={
#                 1: ProcessGroupOutput(
#                     id=1,
#                     processes=[
#                         ProcessOutput(
#                             id=1,
#                             process=Process(1, "echo first; echo second"),
#                             data="first\nsecond\n",
#                         )
#                     ],
#                 )
#             }
#         ),
#         lines=58,
#     )
#
#     assert process_lines == [58]
#
#
# def test_printer_generate_output() -> None:
#     printer = Printer(colours=Colours.from_colour("no"))
#
#     output = printer.generate_output(
#         ProcessGroupManagerOutput(
#             process_group_outputs={
#                 1: ProcessGroupOutput(
#                     id=1,
#                     processes=[
#                         ProcessOutput(
#                             id=1,
#                             process=Process(1, "echo first; echo second"),
#                             data="first\nsecond\n",
#                         )
#                     ],
#                 ),
#                 2: ProcessGroupOutput(
#                     id=2,
#                     processes=[
#                         ProcessOutput(
#                             id=2,
#                             process=Process(2, "echo first; echo second"),
#                             data="first\nsecond\n",
#                         )
#                     ],
#                 ),
#             }
#         ),
#     )
#
#     assert output == ["[echo first; echo second] running /", "first", "second", ""]
