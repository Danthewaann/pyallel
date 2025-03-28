from __future__ import annotations

import time
import pytest

from pyallel.errors import InvalidLinesModifierError
from pyallel.process import Process, ProcessOutput
from pyallel.process_group import ProcessGroupOutput, ProcessGroup


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
        1, 1, "sleep 0.1", "::", "sleep 0.2", "::", "sleep 0.3"
    )
    assert process_group.id == expected_process_group.id
    assert len(process_group.processes) == len(expected_process_group.processes)


def test_from_commands_with_lines_modifier() -> None:
    expected_process_group = ProcessGroup(
        id=1,
        processes=[
            Process(id=1, command="sleep 0.1"),
            Process(id=2, command="sleep 0.2"),
            Process(id=3, command="sleep 0.3"),
        ],
    )
    process_group = ProcessGroup.from_commands(
        1,
        1,
        "lines=20 :::: sleep 0.1",
        "::",
        "lines=20 :::: sleep 0.2",
        "::",
        "lines=20 :::: sleep 0.3",
    )
    assert process_group.id == expected_process_group.id
    assert len(process_group.processes) == len(expected_process_group.processes)
    assert process_group.processes[0].percentage_lines == 0.2
    assert process_group.processes[1].percentage_lines == 0.2
    assert process_group.processes[2].percentage_lines == 0.2


def test_from_commands_with_lines_modifier_exceeds_100() -> None:
    with pytest.raises(
        InvalidLinesModifierError,
        match="lines modifier must not exceed 100 across all processes within each process group",
    ):
        ProcessGroup.from_commands(
            1,
            1,
            "lines=40 :::: sleep 0.1",
            "::",
            "lines=40 :::: sleep 0.2",
            "::",
            "lines=30 :::: sleep 0.3",
        )


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
    output = process_group.stream()
    assert len(output.processes) == 3


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

    assert len(output.processes) == 3
