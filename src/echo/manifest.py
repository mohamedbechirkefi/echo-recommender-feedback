# SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
"""Per-run reproducibility manifest: environment, revision, timing, memory.

Paths and user names are never recorded (no personal identifiers).
"""

from __future__ import annotations

import os
import platform
import resource
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from . import __version__

MANIFEST_VERSION = "echo.manifest.v1"
REPO_ROOT = Path(__file__).resolve().parents[2]


def _run(cmd: list[str]) -> str | None:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=10, cwd=REPO_ROOT)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def git_state() -> dict[str, Any]:
    rev = _run(["git", "rev-parse", "HEAD"])
    status = _run(["git", "status", "--porcelain", "--", "src", "tests", "experiments", "pyproject.toml", "uv.lock"])
    return {"revision": rev, "code_dirty": None if status is None else bool(status)}


def cpu_name() -> str:
    if sys.platform == "darwin":
        name = _run(["sysctl", "-n", "machdep.cpu.brand_string"])
        if name:
            return name
    return platform.processor() or platform.machine()


def environment() -> dict[str, Any]:
    return {
        "echo_version": __version__,
        "python": platform.python_version(),
        "numpy": np.__version__,
        "os": f"{platform.system()} {platform.release()}",
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu": cpu_name(),
        "cpu_count": os.cpu_count(),
    }


def max_rss_bytes() -> int:
    """Process peak resident set size (high-water mark since process start)."""
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(rss if sys.platform == "darwin" else rss * 1024)


def data_provenance() -> dict[str, Any]:
    """SHA-256 of the committed data manifest and calibration record at run time (None if absent)."""
    import hashlib

    out: dict[str, Any] = {}
    for rel in ("data/manifest.json", "data/fma_calibration_v1.json"):
        f = REPO_ROOT / rel
        out[rel] = hashlib.sha256(f.read_bytes()).hexdigest() if f.exists() else None
    return out


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def build_manifest(
    *, run_id: str, experiment_id: str, label: str, config_hash: str, seed: int, status: str,
    started_utc: str, finished_utc: str, runtime_s: float, peak_traced_bytes: int | None,
    env: dict[str, Any], git: dict[str, Any], result_path: str, data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out = {
        "manifest_version": MANIFEST_VERSION,
        "run_id": run_id,
        "experiment_id": experiment_id,
        "label": label,
        "config_hash": config_hash,
        "seed": seed,
        "status": status,
        "result_path": result_path,
        "started_utc": started_utc,
        "finished_utc": finished_utc,
        "runtime_s": runtime_s,
        "peak_traced_bytes": peak_traced_bytes,
        "process_max_rss_bytes": max_rss_bytes(),
        "memory_note": "peak_traced_bytes is the tracemalloc peak for this run (null unless --trace-memory); process_max_rss_bytes is the process high-water mark so far",
        "git": git,
        "environment": env,
    }
    if data is not None:
        out["data_sha256"] = data
    return out
