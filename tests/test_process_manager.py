from __future__ import annotations
import time


import pytest
from pyallel.errors import NoCommandsForProcessGroupError
from pyallel.process import Process
from pyallel.process_group import ProcessGroup
from pyallel.process_group_manager import ProcessGroupManager


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
    pg_manager.get_cur_process_group_output()
    time.sleep(0.1)
    output = pg_manager.stream()
    assert len(output.process_group_outputs) == 1
    assert output.process_group_outputs[1].id == 1
    assert len(output.process_group_outputs[1].processes) == 2
    assert pg_manager.poll() == 0
    pg_manager.run()
    pg_manager.get_cur_process_group_output()
    time.sleep(0.1)
    output = pg_manager.stream()
    assert len(output.process_group_outputs) == 1
    assert output.process_group_outputs[2].id == 2
    assert len(output.process_group_outputs[2].processes) == 2
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
    process_group_manager = ProcessGroupManager.from_args(
        "sleep 0.1", "::", "sleep 0.2"
    )
    assert len(process_group_manager._process_groups) == len(
        expected_process_group_manager._process_groups
    )

    for pg1, pg2 in zip(
        expected_process_group_manager._process_groups,
        process_group_manager._process_groups,
    ):
        assert len(pg1.processes) == len(pg2.processes)


@pytest.mark.parametrize(
    "args, expected_process_group_manager",
    (
        (
            ["sleep 0.1", ":::", "sleep 0.2", "::", "sleep 0.3", ":::", "sleep 0.4"],
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
            ["sleep 0.1", ":::", "sleep 0.2", ":::", "sleep 0.3", ":::", "sleep 0.4"],
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
                        ],
                    ),
                    ProcessGroup(
                        id=3,
                        processes=[
                            Process(id=3, command="sleep 0.3"),
                        ],
                    ),
                    ProcessGroup(
                        id=4,
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
                "::",
                "sleep 0.2",
                ":::",
                "sleep 0.3",
                "::",
                "sleep 0.4",
                ":::",
                "sleep 0.5",
                "::",
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
    assert len(process_group_manager._process_groups) == len(
        expected_process_group_manager._process_groups
    )

    for pg1, pg2 in zip(
        expected_process_group_manager._process_groups,
        process_group_manager._process_groups,
    ):
        assert len(pg1.processes) == len(pg2.processes)


def test_from_args_with_bad_separator() -> None:
    with pytest.raises(
        NoCommandsForProcessGroupError,
        match="no commands provided for process group 1, did you forgot to provide them before the ::: symbol?",
    ):
        ProcessGroupManager.from_args(":::", "echo hi")
