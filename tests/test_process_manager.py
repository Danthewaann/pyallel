from __future__ import annotations
import time


import pytest
from pyallel.process import Process, ProcessOutput
from pyallel.process_group import ProcessGroupOutput, ProcessGroup
from pyallel.process_group_manager import ProcessGroupManager, ProcessGroupManagerOutput


def test_stream() -> None:
    pg_manager = ProcessGroupManager(
        process_groups=[
            ProcessGroup(
                id=1,
                processes=[
                    Process(id=1, command="echo first"),
                    Process(id=2, command="echo second"),
                ],
            ),
            ProcessGroup(
                id=2,
                processes=[
                    Process(id=3, command="echo third"),
                    Process(id=4, command="echo fourth"),
                ],
            ),
        ],
    )
    pg_manager.run()
    assert pg_manager.cur_process_group is not None
    time.sleep(0.1)
    assert pg_manager.stream() == ProcessGroupManagerOutput(
        cur_process_group_id=1,
        process_group_outputs={
            1: ProcessGroupOutput(
                id=1,
                processes=[
                    ProcessOutput(
                        id=1,
                        process=pg_manager.cur_process_group.processes[0],
                        data="first\n",
                    ),
                    ProcessOutput(
                        id=2,
                        process=pg_manager.cur_process_group.processes[1],
                        data="second\n",
                    ),
                ],
            )
        },
    )
    assert pg_manager.poll() == 0
    pg_manager.run()
    assert pg_manager.cur_process_group is not None
    time.sleep(0.1)
    assert pg_manager.stream() == ProcessGroupManagerOutput(
        cur_process_group_id=2,
        process_group_outputs={
            2: ProcessGroupOutput(
                id=2,
                processes=[
                    ProcessOutput(
                        id=3,
                        process=pg_manager.cur_process_group.processes[0],
                        data="third\n",
                    ),
                    ProcessOutput(
                        id=4,
                        process=pg_manager.cur_process_group.processes[1],
                        data="fourth\n",
                    ),
                ],
            )
        },
    )
    assert pg_manager.poll() == 0


def test_from_args() -> None:
    expected_process_group_manager = ProcessGroupManager(
        process_groups=[
            ProcessGroup(
                id=1,
                processes=[
                    Process(id=1, command="sleep 0.1"),
                    Process(id=2, command="sleep 0.2"),
                ],
            )
        ]
    )
    process_group_manager = ProcessGroupManager.from_args("sleep 0.1", "sleep 0.2")
    assert len(process_group_manager.process_groups) == len(
        expected_process_group_manager.process_groups
    )


@pytest.mark.parametrize(
    "args, expected_process_group_manager",
    (
        (
            ["sleep 0.1", ":::", "sleep 0.2", "sleep 0.3", ":::", "sleep 0.4"],
            ProcessGroupManager(
                process_groups=[
                    ProcessGroup(
                        id=1,
                        processes=[
                            Process(id=1, command="sleep 0.1"),
                        ],
                    ),
                    ProcessGroup(
                        id=2,
                        processes=[
                            Process(id=2, command="sleep 0.2"),
                            Process(id=3, command="sleep 0.3"),
                        ],
                    ),
                    ProcessGroup(
                        id=3,
                        processes=[
                            Process(id=4, command="sleep 0.4"),
                        ],
                    ),
                ],
            ),
        ),
        (
            [
                "sleep 0.1",
                "sleep 0.2",
                ":::",
                "sleep 0.3",
                "sleep 0.4",
                ":::",
                "sleep 0.5",
                "sleep 0.6",
            ],
            ProcessGroupManager(
                process_groups=[
                    ProcessGroup(
                        id=1,
                        processes=[
                            Process(id=1, command="sleep 0.1"),
                            Process(id=2, command="sleep 0.2"),
                        ],
                    ),
                    ProcessGroup(
                        id=2,
                        processes=[
                            Process(id=3, command="sleep 0.3"),
                            Process(id=4, command="sleep 0.4"),
                        ],
                    ),
                    ProcessGroup(
                        id=3,
                        processes=[
                            Process(id=5, command="sleep 0.5"),
                            Process(id=6, command="sleep 0.6"),
                        ],
                    ),
                ],
            ),
        ),
    ),
)
def test_from_args_with_separators(
    args: list[str], expected_process_group_manager: ProcessGroupManager
) -> None:
    process_group_manager = ProcessGroupManager.from_args(*args)
    assert len(process_group_manager.process_groups) == len(
        expected_process_group_manager.process_groups
    )
