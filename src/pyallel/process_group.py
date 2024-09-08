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
    data: str

@dataclass
class ProcessGroup:
    processes: list[Process]
    timer: bool = False
    output: dict[int, list[str]] = field(init=False)
    process_lines: list[int] = field(init=False)
    completed_processes: set[int] = field(default_factory=set)
    num_processes: int = field(init=False)
    exit_code: int = 0
    interrupt_count: int = 0
    passed: bool = True
    icon: int = 0

    def __post_init__(self) -> None:
        self.num_processes = len(self.processes)
        self.process_lines = [0 for _ in self.processes]
        self.output = {i: [None, ""] for i, _ in enumerate(self.processes, start=1)}  # type: ignore

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
        output: list[Output] = []
        for process in self.processes:
            data = process.read().decode()
            output.append(Output(process, data))
        return output

    def handle_signal(self, signum: int) -> None:
        for process in self.processes:
            if self.interrupt_count == 0:
                process.interrupt()
            else:
                process.kill()

        self.exit_code = 128 + signum
        self.interrupt_count += 1

    @classmethod
    def from_commands(
        cls,
        *commands: str,
        timer: bool = False,
    ) -> ProcessGroup:
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
            timer=timer,
        )

        return process_group
