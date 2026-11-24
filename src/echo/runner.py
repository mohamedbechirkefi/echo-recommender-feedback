# SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
"""Experiment runner: config expansion, freeze guard, execution, serialization.

Experiment config (``experiments/EXP-NNN/config.json``)::

    {
      "experiment_id": "EXP-001",
      "label": "exploratory" | "confirmatory",
      "protocol_path": "research/experiments/EXP-001/protocol.md",
      "blocks": [
        {"name": "smoke", "base": {...SimConfig fields except seed...},
         "factors": {"policy": ["RAND", "SIM"],
                     "preference": [{"preference_model": "fixed", "eta": 0.0}, ...]},
         "seeds": [900000, 900001]}
      ]
    }

A factor level is either a scalar (sets the field of the factor's name) or
an object of field overrides. Runs are the Cartesian product of all factor
levels and seeds, in the order written.

Guards (fail closed):

- A confirmatory config runs only if its protocol is frozen: the registry
  row has status containing "frozen" and a SHA-256 hash that equals the
  hash of the protocol file. Freezing is the owner's decision (G-FREEZE).
- An exploratory config may not use confirmatory seeds and writes only
  under ``results/exploratory/``.
"""

from __future__ import annotations

import csv
import hashlib
import itertools
import json
import time
import tracemalloc
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import CONFIRMATORY_SEEDS, ConfigError, SimConfig
from .manifest import REPO_ROOT, build_manifest, environment, git_state, utc_now
from .metrics import compute_metrics
from .schema import build_result, dumps_result, validate_result
from .simulate import Trace, simulate

REGISTRY = REPO_ROOT / "research" / "experiment_registry.csv"
MAX_FAIL_FRACTION = 0.10


class RefusedError(RuntimeError):
    """Raised when a run is refused by a guard (freeze, seeds, output path)."""


class StopRuleError(RuntimeError):
    """Raised when more than 10 % of the runs in an arm fail (protocol section 5)."""


@dataclass(frozen=True)
class PlannedRun:
    block: str
    arm: str
    run_id: str
    config: SimConfig


def load_experiment(path: Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    for key in ("experiment_id", "label", "protocol_path", "blocks"):
        if key not in data:
            raise ConfigError(f"experiment config lacks {key!r}")
    if data["label"] not in ("exploratory", "confirmatory"):
        raise ConfigError("label must be 'exploratory' or 'confirmatory'")
    if not isinstance(data["blocks"], list) or not data["blocks"]:
        raise ConfigError("blocks must be a non-empty list")
    return data


def _level_overrides(name: str, level: Any) -> dict[str, Any]:
    if isinstance(level, dict):
        return dict(level)
    return {name: level}


def _level_tag(name: str, level: Any) -> str:
    if isinstance(level, dict):
        return "-".join(f"{v}" for v in level.values())
    return f"{level}"


def expand(exp: dict[str, Any]) -> list[PlannedRun]:
    runs: list[PlannedRun] = []
    seen: set[str] = set()
    for block in exp["blocks"]:
        name = block["name"]
        base = dict(block.get("base", {}))
        if "seed" in base:
            raise ConfigError("put seeds in 'seeds', not in 'base'")
        factors: dict[str, list] = block.get("factors", {})
        seeds = block["seeds"]
        if not seeds or len(set(seeds)) != len(seeds):
            raise ConfigError(f"block {name}: seeds must be a non-empty list without duplicates")
        names = list(factors)
        for combo in itertools.product(*(factors[n] for n in names)):
            overrides: dict[str, Any] = {}
            for n, lvl in zip(names, combo):
                overrides.update(_level_overrides(n, lvl))
            arm = "_".join(_level_tag(n, lvl) for n, lvl in zip(names, combo)) or "default"
            for seed in seeds:
                cfg = SimConfig.from_dict({**base, **overrides, "seed": seed})
                run_id = f"{exp['experiment_id']}_{name}_{arm}_s{seed}"
                if run_id in seen:
                    raise ConfigError(f"duplicate run id {run_id}")
                seen.add(run_id)
                runs.append(PlannedRun(block=name, arm=f"{name}/{arm}", run_id=run_id, config=cfg))
    return runs


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def protocol_frozen(experiment_id: str, protocol_path: Path, registry: Path = REGISTRY) -> tuple[bool, str]:
    """Return (frozen, reason). Frozen requires status 'frozen' and a matching hash."""
    with open(registry, newline="", encoding="utf-8") as fh:
        rows = {r["experiment_id"]: r for r in csv.DictReader(fh)}
    row = rows.get(experiment_id)
    if row is None:
        return False, f"{experiment_id} is not in the registry"
    recorded = (row.get("protocol_hash") or "").strip().lower()
    status = (row.get("status") or "").lower()
    if "frozen" not in status or "awaiting" in status:
        return False, f"registry status is {row.get('status')!r}, not frozen"
    if len(recorded) != 64:
        return False, f"registry protocol hash is {recorded!r}, not a SHA-256"
    actual = sha256_file(protocol_path)
    if actual != recorded:
        return False, f"protocol file hash {actual} differs from the registry hash {recorded}"
    return True, "frozen"


def check_permission(exp: dict[str, Any], runs: list[PlannedRun], out_dir: Path, registry: Path = REGISTRY) -> None:
    if exp["label"] == "confirmatory":
        ok, reason = protocol_frozen(exp["experiment_id"], REPO_ROOT / exp["protocol_path"], registry)
        if not ok:
            raise RefusedError(
                f"refusing confirmatory {exp['experiment_id']}: protocol not frozen ({reason}). "
                "Freezing is the owner's decision (G-FREEZE)."
            )
    else:
        bad = sorted({r.config.seed for r in runs} & set(CONFIRMATORY_SEEDS))
        if bad:
            raise RefusedError(f"exploratory runs may not use confirmatory seeds {bad}")
        exploratory_root = (REPO_ROOT / "results" / "exploratory").resolve()
        target = Path(out_dir).resolve()
        if exploratory_root not in (target, *target.parents):
            raise RefusedError(f"exploratory output must live under {exploratory_root}")


def default_out_dir(exp: dict[str, Any]) -> Path:
    if exp["label"] == "exploratory":
        return REPO_ROOT / "results" / "exploratory" / exp["experiment_id"]
    return REPO_ROOT / "results" / exp["experiment_id"]


def _error_text(exc: BaseException) -> str:
    """Exception type, message and frame function names; no file system paths."""
    frames = traceback.extract_tb(exc.__traceback__)
    where = " <- ".join(f"{Path(f.filename).name}:{f.name}:{f.lineno}" for f in reversed(frames))
    return f"{type(exc).__name__}: {exc} [at {where}]"


def execute(run: PlannedRun, experiment_id: str, label: str, record: bool = False) -> tuple[dict, Trace | None, float]:
    """Simulate one run and build its validated result. Errors give a failed result."""
    t0 = time.perf_counter()
    trace = None
    try:
        trace = simulate(run.config, record=record)
        metrics, diagnostics, per_user = compute_metrics(trace)
        result = build_result(
            experiment_id=experiment_id, run_id=run.run_id, label=label, block=run.block, cfg=run.config,
            metrics=metrics, diagnostics=diagnostics, per_user=per_user, error=None,
        )
        validate_result(result)
    except Exception as exc:  # recorded, never swallowed silently
        result = build_result(
            experiment_id=experiment_id, run_id=run.run_id, label=label, block=run.block, cfg=run.config,
            metrics=None, diagnostics=None, per_user=None, error=_error_text(exc),
        )
    return result, trace, time.perf_counter() - t0


def run_experiment(
    config_path: Path, out_dir: Path | None = None, record: bool | set[str] = False, trace_memory: bool = False,
    registry: Path = REGISTRY, progress=None,
) -> list[dict[str, Any]]:
    """Run every planned run, writing results/ and manifests/. Returns run summaries."""
    exp = load_experiment(config_path)
    runs = expand(exp)
    out = Path(out_dir) if out_dir is not None else default_out_dir(exp)
    check_permission(exp, runs, out, registry)
    env = environment()
    git = git_state()
    planned_per_arm: dict[str, int] = {}
    for r in runs:
        planned_per_arm[r.arm] = planned_per_arm.get(r.arm, 0) + 1
    failed_per_arm: dict[str, int] = {}
    summaries = []
    for i, run in enumerate(runs):
        started = utc_now()
        if trace_memory:
            tracemalloc.start()
        rec = (run.block in record) if isinstance(record, (set, frozenset)) else bool(record)
        result, trace, runtime = execute(run, exp["experiment_id"], exp["label"], record=rec)
        peak = None
        if trace_memory:
            peak = tracemalloc.get_traced_memory()[1]
            tracemalloc.stop()
        finished = utc_now()
        rel = Path("runs") / f"{run.run_id}.json"
        text = dumps_result(result)
        (out / rel).parent.mkdir(parents=True, exist_ok=True)
        (out / rel).write_text(text, encoding="utf-8")
        manifest = build_manifest(
            run_id=run.run_id, experiment_id=exp["experiment_id"], label=exp["label"],
            config_hash=result["config_hash"], seed=run.config.seed, status=result["status"],
            started_utc=started, finished_utc=finished, runtime_s=runtime, peak_traced_bytes=peak,
            env=env, git=git, result_path=str(rel),
        )
        mpath = out / "manifests" / f"{run.run_id}.manifest.json"
        mpath.parent.mkdir(parents=True, exist_ok=True)
        mpath.write_text(json.dumps(manifest, sort_keys=True, indent=1) + "\n", encoding="utf-8")
        summaries.append({"run": run, "result": result, "trace": trace, "runtime_s": runtime, "text": text})
        if progress:
            progress(i + 1, len(runs), run.run_id, result["status"], runtime)
        if result["status"] == "failed":
            failed_per_arm[run.arm] = failed_per_arm.get(run.arm, 0) + 1
            if failed_per_arm[run.arm] > MAX_FAIL_FRACTION * planned_per_arm[run.arm]:
                raise StopRuleError(
                    f"stop rule: {failed_per_arm[run.arm]} of {planned_per_arm[run.arm]} runs failed in arm {run.arm}; "
                    f"last error: {result['error']}"
                )
    return summaries
