from __future__ import annotations

import selectors
import signal
from typing import TYPE_CHECKING, Any

from pyallel.errors import NoCommandsForProcessGroupError, PyallelError
from pyallel.process_group import ProcessGroup, ProcessGroupOutput

if TYPE_CHECKING:
    from pyallel.process import Process


class ProcessGroupManager:
    def __init__(self, process_groups: list[ProcessGroup]) -> None:
        self._exit_code = 0
        self._interrupt_count = 0
        self._cur_pg_index = -1
        self._process_groups = process_groups
        self._selector = selectors.DefaultSelector()

    @property
    def interrupt_count(self) -> int:
        return self._interrupt_count

    @property
    def cur_process_group(self) -> ProcessGroup | None:
        if self._cur_pg_index == -1:
            return None
        try:
            return self._process_groups[self._cur_pg_index]
        except IndexError:
            return None

    def run(self) -> None:
        if self.next():
            self._cur_pg_index += 1
            process_group = self._process_groups[self._cur_pg_index]
            process_group.run()
            for process in process_group.processes:
                self._selector.register(process.fileno(), selectors.EVENT_READ, data=process)

    def next(self) -> bool:
        try:
            return bool(self._process_groups[self._cur_pg_index + 1])
        except IndexError:
            return False

    def wait_for_update(self, timeout: float) -> None:
        # Block until either process output is ready to read or the timeout elapses
        for key, _ in self._selector.select(timeout):
            process: Process = key.data
            if not process.fetch_stdout():
                self._selector.unregister(key.fileobj)

    def stream(self) -> ProcessGroupOutput:
        cur_process_group = self.cur_process_group
        if cur_process_group is None:
            raise PyallelError("Current process group not set, did you forget to call run()?")

        return cur_process_group.stream()

    def get_processes(self) -> list[Process]:
        return [p for pg in self._process_groups for p in pg.processes]

    def poll(self) -> int | None:
        if self.cur_process_group is None:
            return 0

        poll = self.cur_process_group.poll()

        if poll is not None and self._exit_code:
            return self._exit_code

        if self._interrupt_count > 1:
            return self._exit_code

        return poll

    def handle_signal(self, signum: int, _frame: Any) -> None:
        if self.cur_process_group is not None:
            self.cur_process_group.handle_signal(signum)

        self._exit_code = 128 + signum
        self._interrupt_count += 1

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
