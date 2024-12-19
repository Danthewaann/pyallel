from __future__ import annotations

import signal
from typing import Any

from pyallel.process import ProcessOutput
from pyallel.process_group import ProcessGroupOutput, ProcessGroup


class ProcessGroupManagerOutput:
    def __init__(
        self,
        process_group_outputs: dict[int, ProcessGroupOutput] | None = None,
        cur_process_group_id: int = 1,
    ) -> None:
        self.process_group_outputs = process_group_outputs or {}
        self.cur_process_group_id = cur_process_group_id

    def merge(self, other: ProcessGroupManagerOutput) -> None:
        self.cur_process_group_id = other.cur_process_group_id
        for key, value in other.process_group_outputs.items():
            if key in self.process_group_outputs:
                self.process_group_outputs[key].merge(value)
            else:
                self.process_group_outputs[key] = value


class ProcessGroupManager:
    def __init__(self, process_groups: list[ProcessGroup]) -> None:
        self._exit_code = 0
        self._interrupt_count = 0
        self._cur_process_group: ProcessGroup | None = None
        self._process_groups = process_groups
        self._output = ProcessGroupManagerOutput(
            process_group_outputs={
                pg.id: ProcessGroupOutput(
                    id=pg.id,
                    processes=[ProcessOutput(id=p.id, process=p) for p in pg.processes],
                )
                for pg in self._process_groups
            }
        )

    def run(self) -> None:
        if self._process_groups:
            self._cur_process_group = self._process_groups.pop(0)
            self._cur_process_group.run()
        else:
            self._cur_process_group = None

    def next(self) -> bool:
        return True if self._cur_process_group or self._process_groups else False

    def stream(self) -> ProcessGroupManagerOutput:
        if self._cur_process_group is None:
            return ProcessGroupManagerOutput()

        output = ProcessGroupManagerOutput(
            cur_process_group_id=self._cur_process_group.id,
            process_group_outputs={
                self._cur_process_group.id: self._cur_process_group.stream()
            },
        )

        self._output.merge(output)

        return output

    def get_cur_process_group_output(self) -> ProcessGroupOutput:
        if self._cur_process_group:
            return self._output.process_group_outputs[self._cur_process_group.id]

        raise KeyError("no current process group output")

    def get_process(self, id: int) -> ProcessOutput:
        for pg in self._output.process_group_outputs.values():
            for process in pg.processes:
                if process.id == id:
                    return process

        raise KeyError(f"process with id '{id}' not found")

    def poll(self) -> int | None:
        if self._cur_process_group is None:
            return 0

        poll = self._cur_process_group.poll()

        if poll is not None and self._exit_code:
            return self._exit_code

        if self._interrupt_count > 1:
            return self._exit_code

        return poll

    def handle_signal(self, signum: int, _frame: Any) -> None:
        for process_group in self._process_groups:
            process_group.handle_signal(signum)

        self._exit_code = 128 + signum
        self._interrupt_count += 1

    @classmethod
    def from_args(cls, *args: str) -> ProcessGroupManager:
        last_separator_index = 0
        commands: list[str] = []
        process_groups: list[ProcessGroup] = []
        progress_group_id = 1
        process_id = 1

        for i, arg in enumerate(args):
            if arg == ":::":
                if i - 1 == 0:
                    pg = ProcessGroup.from_commands(
                        progress_group_id, process_id, args[0]
                    )
                else:
                    pg = ProcessGroup.from_commands(
                        progress_group_id, process_id, *commands[last_separator_index:]
                    )

                process_groups.append(pg)
                process_id += len(pg.processes)
                last_separator_index = i
                progress_group_id += 1
                continue

            commands.append(arg)

        if len(process_groups) > 1:
            last_separator_index -= 1

        process_groups.append(
            ProcessGroup.from_commands(
                progress_group_id, process_id, *commands[last_separator_index:]
            )
        )

        process_group_manager = cls(process_groups=process_groups)

        signal.signal(signal.SIGINT, process_group_manager.handle_signal)
        signal.signal(signal.SIGTERM, process_group_manager.handle_signal)

        return process_group_manager
