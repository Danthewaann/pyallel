from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from pyallel import constants
from pyallel.errors import InvalidExecutableError, InvalidExecutableErrors
from pyallel.process import Process, ProcessOutput


def get_num_lines(output: str, columns: int | None = None) -> int:
    lines = 0
    columns = columns or constants.COLUMNS()
    for line in output.splitlines():
        line = constants.ANSI_ESCAPE.sub("", line)
        length = len(line)
        line_lines = 1
        if length > columns:
            line_lines = length // columns
            remainder = length % columns
            if remainder:
                line_lines += 1
        lines += 1 * line_lines
    return lines


@dataclass
class ProcessGroupOutput:
    id: int = 0
    processes: Sequence[ProcessOutput] = field(default_factory=list)

    def merge(self, other: ProcessGroupOutput) -> None:
        for i, _ in enumerate(self.processes):
            self.processes[i].merge(other.processes[i])


@dataclass
class ProcessGroup:
    id: int
    processes: list[Process]
    _exit_code: int = field(init=False, default=0)
    _interrupt_count: int = field(init=False, default=0)

    def run(self) -> None:
        for process in self.processes:
            process.run()

    def poll(self) -> int | None:
        polls: list[int | None] = [process.poll() for process in self.processes]

        running = [p for p in polls if p is None]
        failed = [p for p in polls if p is not None and p > 0]

        if running:
            return None
        elif failed:
            return 1
        else:
            return 0

    def stream(self) -> ProcessGroupOutput:
        return ProcessGroupOutput(
            id=self.id,
            processes=[
                ProcessOutput(
                    id=process.id, process=process, data=process.read().decode()
                )
                for process in self.processes
            ],
        )

    def handle_signal(self, signum: int) -> None:
        for process in self.processes:
            if self._interrupt_count == 0:
                process.interrupt()
            else:
                process.kill()

        self._exit_code = 128 + signum
        self._interrupt_count += 1

    @classmethod
    def from_commands(cls, id: int, process_id: int, *commands: str) -> ProcessGroup:
        processes: list[Process] = []
        errors: list[InvalidExecutableError] = []

        for i, command in enumerate(commands):
            try:
                processes.append(Process(i + process_id, command))
            except InvalidExecutableError as e:
                errors.append(e)

        if errors:
            raise InvalidExecutableErrors(*errors)

        process_group = cls(id=id, processes=processes)

        return process_group
