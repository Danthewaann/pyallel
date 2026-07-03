"""
Ad-hoc benchmark comparing Process's stdout reading approach against two
scenarios:

1. A chatty command that produces a lot of output while it's running.
2. A quick command that exits almost immediately, followed by a period of
   idle polling (simulating other still-running commands in the same group).
"""

from __future__ import annotations

import resource
import sys
import time

sys.path.insert(0, "src")

from pyallel.process import Process

CHATTY_CMD = "python3 -c \"[print('line', i) for i in range(200000)]\""
QUICK_CMD = "echo hi"


def cpu_time() -> float:
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_utime + usage.ru_stime


def run_scenario(
    name: str, command: str, poll_seconds: float, extra_idle_seconds: float
) -> None:
    process = Process(1, command)

    start_wall = time.perf_counter()
    start_cpu = cpu_time()

    process.run()

    total_bytes = 0
    while process.poll() is None:
        time.sleep(poll_seconds)
        total_bytes += len(process.read())

    idle_deadline = time.perf_counter() + extra_idle_seconds
    while time.perf_counter() < idle_deadline:
        time.sleep(poll_seconds)
        total_bytes += len(process.read())

    end_wall = time.perf_counter()
    end_cpu = cpu_time()

    print(
        f"{name:12} wall={end_wall - start_wall:6.3f}s  "
        f"cpu={end_cpu - start_cpu:6.3f}s  bytes={total_bytes}"
    )


def main() -> None:
    print("--- scenario: chatty command, output while it's still running ---")
    run_scenario("chatty", CHATTY_CMD, poll_seconds=0.1, extra_idle_seconds=0.0)

    print()
    print("--- scenario: quick command, then 2s of idle polling ---")
    run_scenario("quick+idle", QUICK_CMD, poll_seconds=0.1, extra_idle_seconds=2.0)


if __name__ == "__main__":
    main()
