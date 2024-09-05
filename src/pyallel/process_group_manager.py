from __future__ import annotations

import signal
from dataclasses import dataclass, field
from typing import Any

from pyallel.printer import Printer
from pyallel.process_group import ProcessGroup


@dataclass
class ProcessGroupManager:
    process_groups: list[ProcessGroup]
    interactive: bool = False
    printer: Printer = field(default_factory=Printer)

    def stream(self) -> int:
        exit_code = 0

        if not self.interactive:
            self.printer.info("Running commands...")
            self.printer.info("")

        for process_group in self.process_groups:
            exit_code = process_group.stream()
            if exit_code > 0:
                break

        return exit_code

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
                            interactive=interactive,
                            timer=timer,
                        )
                    )
                else:
                    process_groups.append(
                        ProcessGroup.from_commands(
                            *commands[last_separator_index:],
                            printer=printer,
                            interactive=interactive,
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
                interactive=interactive,
                timer=timer,
            )
        )

        process_group_manager = cls(
            process_groups=process_groups, interactive=interactive, printer=printer
        )

        signal.signal(signal.SIGINT, process_group_manager.handle_signal)
        signal.signal(signal.SIGTERM, process_group_manager.handle_signal)

        return process_group_manager
