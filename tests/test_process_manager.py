from __future__ import annotations


import pytest
from pyallel.process import Process
from pyallel.process_group import ProcessGroup
from pyallel.process_group_manager import ProcessGroupManager


def test_from_args() -> None:
    expected_process_group_manager = ProcessGroupManager(
        process_groups=[
            ProcessGroup(
                processes=[
                    Process(id=1, command="sleep 0.1"),
                    Process(id=2, command="sleep 0.2"),
                ]
            )
        ]
    )
    process_group_manager = ProcessGroupManager.from_args("sleep 0.1", "sleep 0.2")
    assert process_group_manager == expected_process_group_manager


@pytest.mark.parametrize(
    "args, expected_process_group_manager",
    (
        (
            ["sleep 0.1", ":::", "sleep 0.2", "sleep 0.3", ":::", "sleep 0.4"],
            ProcessGroupManager(
                process_groups=[
                    ProcessGroup(
                        processes=[
                            Process(id=1, command="sleep 0.1"),
                        ],
                    ),
                    ProcessGroup(
                        processes=[
                            Process(id=1, command="sleep 0.2"),
                            Process(id=2, command="sleep 0.3"),
                        ]
                    ),
                    ProcessGroup(
                        processes=[
                            Process(id=1, command="sleep 0.4"),
                        ]
                    ),
                ]
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
                        processes=[
                            Process(id=1, command="sleep 0.1"),
                            Process(id=2, command="sleep 0.2"),
                        ],
                    ),
                    ProcessGroup(
                        processes=[
                            Process(id=1, command="sleep 0.3"),
                            Process(id=2, command="sleep 0.4"),
                        ],
                    ),
                    ProcessGroup(
                        processes=[
                            Process(id=1, command="sleep 0.5"),
                            Process(id=2, command="sleep 0.6"),
                        ],
                    ),
                ]
            ),
        ),
    ),
)
def test_from_args_with_separators(
    args: list[str], expected_process_group_manager: ProcessGroupManager
) -> None:
    process_group_manager = ProcessGroupManager.from_args(*args)
    assert process_group_manager == expected_process_group_manager
