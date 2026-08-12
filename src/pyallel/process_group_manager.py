from __future__ import annotations

import signal
from typing import TYPE_CHECKING, Any

from pyallel.errors import NoCommandsForProcessGroupError, PyallelError
from pyallel.process_group import ProcessGroup, ProcessGroupOutput

if TYPE_CHECKING:
    from collections.abc import Sequence


class ProcessGroupManager:
    def __init__(self, process_groups: list[ProcessGroup]) -> None:
        self._exit_code = 0
        self._interrupt_count = 0
        self._process_groups = process_groups.copy()
        self._cur_process_group: ProcessGroup | None = None
        self.groups: Sequence[ProcessGroup] = process_groups

    @classmethod
    def from_args(cls, *args: str) -> ProcessGroupManager:
        commands: list[str] = []
        process_groups: list[ProcessGroup] = []
        progress_group_id = 1
        process_id = 1

        for arg in args:
            if arg != ":::":
                commands.append(arg)
                continue

            if not commands:
                raise NoCommandsForProcessGroupError(
                    f"no commands provided for process group {progress_group_id}, did you forgot to provide them before the ::: symbol?"
                )

            pg = ProcessGroup.from_commands(progress_group_id, process_id, *commands)
            process_groups.append(pg)
            process_id += len(pg.processes)
            progress_group_id += 1
            commands.clear()

        if commands:
            process_groups.append(ProcessGroup.from_commands(progress_group_id, process_id, *commands))

        process_group_manager = cls(process_groups=process_groups)

        signal.signal(signal.SIGINT, process_group_manager.handle_signal)
        signal.signal(signal.SIGTERM, process_group_manager.handle_signal)

        return process_group_manager

    def run(self) -> None:
        if self._process_groups:
            self._cur_process_group = self._process_groups.pop(0)
            self._cur_process_group.run()
        else:
            self._cur_process_group = None

    def next(self) -> bool:
        return bool(self._cur_process_group or self._process_groups)

    def poll(self) -> int | None:
        poll = self.cur_process_group.poll()

        if poll is not None and self._exit_code:
            return self._exit_code

        if self._interrupt_count > 1:
            return self._exit_code

        return poll

    def stream(self) -> ProcessGroupOutput:
        return self.cur_process_group.stream()

    def handle_signal(self, signum: int, _frame: Any) -> None:
        self.cur_process_group.handle_signal(signum)
        self._exit_code = 128 + signum
        self._interrupt_count += 1

    @property
    def cur_process_group(self) -> ProcessGroup:
        if self._cur_process_group is None:
            raise PyallelError("cur_process_group is not set, did you forget to call run()?")
        return self._cur_process_group
