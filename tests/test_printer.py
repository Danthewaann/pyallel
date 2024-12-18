from pyallel.colours import Colours
from pyallel.printer import Printer
from pyallel.process import Process, ProcessOutput
from pyallel.process_group import ProcessGroupOutput
from pyallel.process_group_manager import ProcessGroupManagerOutput


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
