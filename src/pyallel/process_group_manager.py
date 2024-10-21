from __future__ import annotations

import signal
from dataclasses import dataclass, field
from typing import Any

from pyallel.process_group import Output, ProcessGroup


@dataclass
class ProcessGroupManager:
    process_groups: list[ProcessGroup]
    cur_process_group: ProcessGroup | None = field(init=False, default=None)
    exit_code: int = field(init=False, default=0)
    interrupt_count: int = field(init=False, default=0)

    def run(self) -> None:
        if self.process_groups:
            self.cur_process_group = self.process_groups.pop(0)
            self.cur_process_group.run()
        else:
            self.cur_process_group = None

    def stream(self) -> list[Output]:
        if self.cur_process_group is None:
            return []

        return self.cur_process_group.stream()

    def poll(self) -> int | None:
        if self.cur_process_group is None:
            return 0

        if self.exit_code:
            return self.exit_code

        return self.cur_process_group.poll()

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

        for i, arg in enumerate(args):
            if arg == ":::":
                if i - 1 == 0:
                    process_groups.append(
                        ProcessGroup.from_commands(progress_group_id, args[0])
                    )
                else:
                    process_groups.append(
                        ProcessGroup.from_commands(
                            progress_group_id, *commands[last_separator_index:]
                        )
                    )

                last_separator_index = i
                progress_group_id += 1
                continue

            commands.append(arg)

        if len(process_groups) > 1:
            last_separator_index -= 1

        process_groups.append(
            ProcessGroup.from_commands(
                progress_group_id, *commands[last_separator_index:]
            )
        )

        process_group_manager = cls(process_groups=process_groups)

        signal.signal(signal.SIGINT, process_group_manager.handle_signal)
        signal.signal(signal.SIGTERM, process_group_manager.handle_signal)

        return process_group_manager
