from __future__ import annotations

import signal
from dataclasses import dataclass, field
from typing import Any

from pyallel.process import ProcessOutput
from pyallel.process_group import ProcessGroupOutput, ProcessGroup


@dataclass
class ProcessGroupManagerOutput:
    process_group_outputs: dict[int, ProcessGroupOutput] = field(default_factory=dict)
    cur_process_group_id: int = 1

    def merge(self, other: ProcessGroupManagerOutput) -> None:
        self.cur_process_group_id = other.cur_process_group_id
        for key, value in other.process_group_outputs.items():
            if key in self.process_group_outputs:
                self.process_group_outputs[key].merge(value)
            else:
                self.process_group_outputs[key] = value


@dataclass
class ProcessGroupManager:
    process_groups: list[ProcessGroup]
    outputs: ProcessGroupManagerOutput = field(
        init=False, default_factory=ProcessGroupManagerOutput
    )
    cur_process_group: ProcessGroup | None = field(init=False, default=None)
    exit_code: int = field(init=False, default=0)
    interrupt_count: int = field(init=False, default=0)

    def __post_init__(self) -> None:
        pg = self.process_groups[0]
        self.outputs = ProcessGroupManagerOutput(
            process_group_outputs={
                pg.id: ProcessGroupOutput(
                    id=pg.id,
                    processes=[ProcessOutput(id=p.id, process=p) for p in pg.processes],
                )
            }
        )

    def run(self) -> None:
        if self.process_groups:
            self.cur_process_group = self.process_groups.pop(0)
            self.cur_process_group.run()
        else:
            self.cur_process_group = None

    def stream(self) -> ProcessGroupManagerOutput:
        if self.cur_process_group is None:
            return ProcessGroupManagerOutput()

        output = ProcessGroupManagerOutput(
            cur_process_group_id=self.cur_process_group.id,
            process_group_outputs={
                self.cur_process_group.id: self.cur_process_group.stream()
            },
        )

        self.outputs.merge(output)

        return output

    def get_process(self, id: int) -> ProcessOutput:
        for pg in self.outputs.process_group_outputs.values():
            for process in pg.processes:
                if process.id == id:
                    return process

        raise KeyError(f"process with id '{id}' not found")

    def poll(self) -> int | None:
        if self.cur_process_group is None:
            return 0

        poll = self.cur_process_group.poll()

        if poll is not None and self.exit_code:
            return self.exit_code

        if self.interrupt_count > 1:
            return self.exit_code

        return poll

    def handle_signal(self, signum: int, _frame: Any) -> None:
        for process_group in self.process_groups:
            process_group.handle_signal(signum)

        self.exit_code = 128 + signum
        self.interrupt_count += 1

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
