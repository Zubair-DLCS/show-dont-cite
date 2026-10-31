"""Run a PoC script in a separate, resource-limited Python process.

This is isolation for *reliability*, not a security boundary: generated code
runs with your user's permissions. Run untrusted model output in a container
or a throwaway VM (Colab is fine).
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, asdict

PASS, FAIL = "pass", "fail"
ERROR, TIMEOUT, NO_RESULT = "error", "timeout", "no_result"

_TAIL = 2000


@dataclass
class ExecResult:
    status: str          # pass | fail | error | timeout | no_result
    stdout: str
    stderr: str
    returncode: int | None
    seconds: float

    def to_dict(self) -> dict:
        return asdict(self)


def parse_result(stdout: str) -> str:
    """Read the verdict from the last non-empty stdout line."""
    lines = [ln.strip() for ln in stdout.strip().splitlines() if ln.strip()]
    if not lines:
        return NO_RESULT
    last = lines[-1]
    if last == "RESULT: PASS":
        return PASS
    if last == "RESULT: FAIL":
        return FAIL
    return NO_RESULT


def _limits(memory_mb: int, cpu_seconds: int):
    def apply():  # runs in the child before exec (POSIX only)
        try:
            import resource
            mem = memory_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (mem, mem))
            resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds))
        except Exception:
            pass
    return apply if os.name == "posix" else None


def run_script(code: str, timeout: int = 30, memory_mb: int = 2048) -> ExecResult:
    with tempfile.TemporaryDirectory(prefix="sdc_") as tmp:
        path = os.path.join(tmp, "poc.py")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(code)
        env = {"PATH": os.environ.get("PATH", ""), "HOME": tmp,
               "PYTHONIOENCODING": "utf-8", "OPENBLAS_NUM_THREADS": "1",
               "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}
        start = time.time()
        try:
            proc = subprocess.run(
                [sys.executable, "-I", path], cwd=tmp, env=env,
                capture_output=True, text=True, timeout=timeout,
                preexec_fn=_limits(memory_mb, timeout + 5),
            )
        except subprocess.TimeoutExpired as exc:
            out = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            err = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
            return ExecResult(TIMEOUT, out[-_TAIL:], err[-_TAIL:], None, time.time() - start)
        elapsed = time.time() - start
        if proc.returncode != 0:
            status = ERROR
        else:
            status = parse_result(proc.stdout)
        return ExecResult(status, proc.stdout[-_TAIL:], proc.stderr[-_TAIL:],
                          proc.returncode, elapsed)
