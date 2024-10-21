from pyallel.colours import Colours
from pyallel.printer import Printer
from pyallel.process import Process
from pyallel.process_group import Output


def test_generate_outputs() -> None:
    printer = Printer(colours=Colours.from_colour("no"))

    output = printer.generate_outputs(
        [[Output(process=Process(1, "echo first; echo second"), data="first\nsecond")]]
    )

    assert output == ["[echo first; echo second] running /", "first", "second"]


def test_get_process_lines() -> None:
    printer = Printer(colours=Colours.from_colour("no"))

    process_lines = printer.get_process_lines(
        [
            [
                Output(
                    process=Process(1, "echo first; echo second"), data="first\nsecond"
                )
            ],
        ],
        lines=58,
    )

    assert process_lines == [58]
