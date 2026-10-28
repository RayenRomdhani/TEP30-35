"""Run a command and record the peak memory (RSS) of its whole process tree.

Snakemake cannot measure memory on Windows, so this samples it every 0.5 s.
Run:  python scripts/dev/peak_ram.py <log_file> <command...>
"""

import subprocess
import sys
import time

import psutil


def main() -> None:
    log_file, cmd = sys.argv[1], sys.argv[2:]
    start = time.time()
    peak = 0
    with open(log_file, "w") as log:
        proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
        root = psutil.Process(proc.pid)
        while proc.poll() is None:
            total = 0
            for p in [root] + root.children(recursive=True):  # snakemake starts the solver as a child process
                try:
                    total += p.memory_info().rss
                except psutil.Error:  # a child process ended while we were reading it
                    pass
            peak = max(peak, total)
            time.sleep(0.5)
    print(f"exit {proc.returncode} | wall {time.time() - start:.0f} s | peak RSS {peak / 2**30:.2f} GiB")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit("usage: python scripts/dev/peak_ram.py <log_file> <command...>")
    main()
