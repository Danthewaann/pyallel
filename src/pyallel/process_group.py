from __future__ import annotations

from dataclasses import dataclass, field

from pyallel import constants
from pyallel.errors import InvalidExecutableError, InvalidExecutableErrors
from pyallel.process import Process


def get_num_lines(output: list[str], columns: int | None = None) -> int:
    lines = 0
    columns = columns or constants.COLUMNS()
    for line in output:
        for line in line.splitlines():
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


def format_time_taken(time_taken: float) -> str:
    time_taken = round(time_taken, 1)
    seconds = time_taken % (24 * 3600)

    return f"{seconds}s"


@dataclass
class Output:
    process: Process
    data: str = ""


@dataclass
class ProcessGroup:
    processes: list[Process]
    _output: list[Output] = field(init=False)
    _exit_code: int = field(init=False, default=0)
    _interrupt_count: int = field(init=False, default=0)

    def __post_init__(self) -> None:
        self._output = [Output(process=process) for process in self.processes]

    def run(self) -> None:
        for process in self.processes:
            process.run()

    def poll(self) -> int | None:
        for process in self.processes:
            poll = process.poll()
            if poll is None:
                return None
            elif poll > 0:
                return poll

        return 0

    def stream(self) -> list[Output]:
        for i, process in enumerate(self.processes):
            self._output[i].data = process.read().decode()
        return self._output

    def handle_signal(self, signum: int) -> None:
        for process in self.processes:
            if self._interrupt_count == 0:
                process.interrupt()
            else:
                process.kill()

        self._exit_code = 128 + signum
        self._interrupt_count += 1

    @classmethod
    def from_commands(cls, *commands: str) -> ProcessGroup:
        processes: list[Process] = []
        errors: list[InvalidExecutableError] = []

        for i, command in enumerate(commands):
            try:
                processes.append(Process(i + 1, command))
            except InvalidExecutableError as e:
                errors.append(e)

        if errors:
            raise InvalidExecutableErrors(*errors)

        process_group = cls(
            processes=processes,
        )

        return process_group
