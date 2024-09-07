from __future__ import annotations

import signal
from dataclasses import dataclass, field
from typing import Any

from pyallel.printer import Printer
from pyallel.process_group import ProcessGroup


@dataclass
class ProcessGroupManager:
    process_groups: list[ProcessGroup]
    cur_process_group: ProcessGroup | None = None
    interactive: bool = False
    printer: Printer = field(default_factory=Printer)

    def run(self) -> None:
        self.cur_process_group = self.process_groups.pop(0)
        self.cur_process_group.run()

    def stream(self) -> list[list[str]]:
        if self.cur_process_group is None:
            return []

        return self.cur_process_group.stream_2()

    def poll(self) -> int | None:
        if self.cur_process_group is None:
            return 0

        return self.cur_process_group.poll()

    def handle_signal(self, signum: int, _frame: Any) -> None:
        for process_group in self.process_groups:
            process_group.handle_signal(signum)

    @classmethod
    def from_args(
        cls,
        *args: str,
        printer: Printer | None = None,
        interactive: bool = False,
        timer: bool = False,
    ) -> ProcessGroupManager:
        printer = printer or Printer()
        last_separator_index = 0
        commands: list[str] = []
        process_groups: list[ProcessGroup] = []

        for i, arg in enumerate(args):
            if arg == ":::":
                if i - 1 == 0:
                    process_groups.append(
                        ProcessGroup.from_commands(
                            args[0],
                            printer=printer,
                            timer=timer,
                        )
                    )
                else:
                    process_groups.append(
                        ProcessGroup.from_commands(
                            *commands[last_separator_index:],
                            printer=printer,
                            timer=timer,
                        )
                    )

                last_separator_index = i
                continue

            commands.append(arg)

        if len(process_groups) > 1:
            last_separator_index -= 1

        process_groups.append(
            ProcessGroup.from_commands(
                *commands[last_separator_index:],
                printer=printer,
                timer=timer,
            )
        )

        process_group_manager = cls(
            process_groups=process_groups, interactive=interactive, printer=printer
        )

        signal.signal(signal.SIGINT, process_group_manager.handle_signal)
        signal.signal(signal.SIGTERM, process_group_manager.handle_signal)

        return process_group_manager
