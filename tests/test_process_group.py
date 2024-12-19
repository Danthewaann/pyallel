from __future__ import annotations
import time


from pyallel.process import Process, ProcessOutput
from pyallel.process_group import ProcessGroupOutput, ProcessGroup


def test_from_command() -> None:
    expected_process = Process(id=1, command="sleep 0.1")
    process = Process(1, "sleep 0.1")
    assert process == expected_process


def test_from_commands() -> None:
    expected_process_group = ProcessGroup(
        id=1,
        processes=[
            Process(id=1, command="sleep 0.1"),
            Process(id=2, command="sleep 0.2"),
            Process(id=3, command="sleep 0.3"),
        ],
    )
    process_group = ProcessGroup.from_commands(
        1, 1, "sleep 0.1", "sleep 0.2", "sleep 0.3"
    )
    assert process_group == expected_process_group


def test_stream() -> None:
    process_group = ProcessGroup(
        id=1,
        processes=[
            Process(id=1, command="echo first; echo hi"),
            Process(id=2, command="echo second"),
            Process(id=3, command="echo third"),
        ],
    )
    process_group.run()
    time.sleep(0.1)
    assert process_group.stream() == ProcessGroupOutput(
        id=1,
        processes=[
            ProcessOutput(id=1, process=process_group.processes[0], data="first\nhi\n"),
            ProcessOutput(id=2, process=process_group.processes[1], data="second\n"),
            ProcessOutput(id=3, process=process_group.processes[2], data="third\n"),
        ],
    )


def test_output_merge() -> None:
    output = ProcessGroupOutput(
        id=1,
        processes=[
            ProcessOutput(
                id=1,
                process=Process(id=1, command="echo first; echo hi"),
                data="first\nhi\n",
            ),
            ProcessOutput(
                id=1, process=Process(id=2, command="echo second"), data="second\n"
            ),
            ProcessOutput(
                id=3, process=Process(id=3, command="echo third"), data="third\n"
            ),
        ],
    )

    output.merge(
        ProcessGroupOutput(
            id=1,
            processes=[
                ProcessOutput(
                    id=1,
                    process=Process(id=1, command="echo first; echo hi"),
                    data="bye\n",
                ),
                ProcessOutput(
                    id=1, process=Process(id=2, command="echo second"), data="hi\n"
                ),
                ProcessOutput(
                    id=3, process=Process(id=3, command="echo third"), data="five\n"
                ),
            ],
        )
    )

    assert output == ProcessGroupOutput(
        id=1,
        processes=[
            ProcessOutput(
                id=1,
                process=Process(id=1, command="echo first; echo hi"),
                data="first\nhi\nbye\n",
            ),
            ProcessOutput(
                id=1, process=Process(id=2, command="echo second"), data="second\nhi\n"
            ),
            ProcessOutput(
                id=3, process=Process(id=3, command="echo third"), data="third\nfive\n"
            ),
        ],
    )
