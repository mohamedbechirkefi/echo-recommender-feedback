# SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
"""Versioned JSON result schema ``echo.result.v1``, validated at export and import.

A result file holds only deterministic content: the same configuration and
seed give a byte-identical file (check V1). Timing, memory and host data go
to the separate run manifest (``manifest.py``).

Top-level object (all keys required):

- schema_version: "echo.result.v1"
- experiment_id: "EXP-NNN"
- run_id: non-empty string
- label: "exploratory" | "confirmatory"
- block: non-empty string (matrix block inside the experiment config)
- config: SimConfig as a JSON object (validated by SimConfig.from_dict)
- config_hash: SHA-256 hex of the canonical config JSON (recomputed)
- seed: int, equal to config.seed
- status: "ok" | "failed"
- metrics: object with exactly the METRIC_NAMES keys, finite numbers (null if failed)
- diagnostics: object (null if failed)
- per_user: {drift_rad: [float], accepted: [int], skips: [int]}, each of length
  config.n_users (null if failed)
- error: null if ok, non-empty string if failed
- units: object mapping metric name to unit string
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

from .config import ConfigError, SimConfig, config_hash
from .metrics import METRIC_NAMES

SCHEMA_VERSION = "echo.result.v1"
UNITS = {
    "drift_rad": "rad",
    "homogenisation": "cosine difference (unitless)",
    "discovery": "fraction of clusters",
    "novelty_bits": "bits",
    "diversity_ild": "unitless, [0, 2]",
    "relevance_initial": "cosine",
    "relevance_current": "cosine",
    "exposure_gini": "unitless, [0, 1]",
    "skip_rate": "fraction of steps",
    "drift_per_accept_rad": "rad per accepted track",
}
_REQUIRED = (
    "schema_version", "experiment_id", "run_id", "label", "block", "config", "config_hash",
    "seed", "status", "metrics", "diagnostics", "per_user", "error", "units",
)
_EXP_RE = re.compile(r"^EXP-\d{3}$")
_HEX_RE = re.compile(r"^[0-9a-f]{64}$")


class SchemaError(ValueError):
    """Raised when a result object does not conform to echo.result.v1."""


def build_result(
    *, experiment_id: str, run_id: str, label: str, block: str, cfg: SimConfig,
    metrics: dict | None, diagnostics: dict | None, per_user: dict | None, error: str | None,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "experiment_id": experiment_id,
        "run_id": run_id,
        "label": label,
        "block": block,
        "config": cfg.to_dict(),
        "config_hash": cfg.hash(),
        "seed": cfg.seed,
        "status": "ok" if error is None else "failed",
        "metrics": metrics,
        "diagnostics": diagnostics,
        "per_user": per_user,
        "error": error,
        "units": dict(UNITS),
    }


def _finite_number(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def validate_result(obj: Any) -> dict[str, Any]:
    """Raise SchemaError listing every problem; return obj when valid."""
    errs: list[str] = []
    if not isinstance(obj, dict):
        raise SchemaError("result must be a JSON object")
    missing = [k for k in _REQUIRED if k not in obj]
    extra = sorted(set(obj) - set(_REQUIRED))
    if missing:
        errs.append(f"missing keys: {missing}")
    if extra:
        errs.append(f"unexpected keys: {extra}")
    if errs:
        raise SchemaError("; ".join(errs))
    if obj["schema_version"] != SCHEMA_VERSION:
        errs.append(f"schema_version must be {SCHEMA_VERSION!r}, got {obj['schema_version']!r}")
    if not isinstance(obj["experiment_id"], str) or not _EXP_RE.match(obj["experiment_id"]):
        errs.append("experiment_id must match EXP-NNN")
    for key in ("run_id", "block"):
        if not isinstance(obj[key], str) or not obj[key]:
            errs.append(f"{key} must be a non-empty string")
    if obj["label"] not in ("exploratory", "confirmatory"):
        errs.append("label must be 'exploratory' or 'confirmatory'")
    cfg = None
    try:
        cfg = SimConfig.from_dict(obj["config"])
    except (ConfigError, TypeError) as exc:
        errs.append(f"config invalid: {exc}")
    if not isinstance(obj["config_hash"], str) or not _HEX_RE.match(obj["config_hash"]):
        errs.append("config_hash must be 64 lowercase hex characters")
    elif cfg is not None and obj["config_hash"] != config_hash(obj["config"]):
        errs.append("config_hash does not match the config")
    if cfg is not None and obj["seed"] != cfg.seed:
        errs.append("seed does not equal config.seed")
    if obj["units"] != UNITS:
        errs.append("units do not match the v1 unit table")
    status = obj["status"]
    if status == "ok":
        if obj["error"] is not None:
            errs.append("error must be null when status is ok")
        m = obj["metrics"]
        if not isinstance(m, dict) or set(m) != set(METRIC_NAMES):
            errs.append(f"metrics must have exactly the keys {list(METRIC_NAMES)}")
        else:
            bad = [k for k, v in m.items() if not _finite_number(v)]
            if bad:
                errs.append(f"non-finite or non-numeric metrics: {bad}")
        if not isinstance(obj["diagnostics"], dict):
            errs.append("diagnostics must be an object when status is ok")
        pu = obj["per_user"]
        if not isinstance(pu, dict) or set(pu) != {"drift_rad", "accepted", "skips"}:
            errs.append("per_user must have keys drift_rad, accepted, skips")
        elif cfg is not None:
            for key, kind in (("drift_rad", float), ("accepted", int), ("skips", int)):
                arr = pu[key]
                if not isinstance(arr, list) or len(arr) != cfg.n_users:
                    errs.append(f"per_user.{key} must be a list of length n_users")
                elif kind is int and not all(isinstance(v, int) and not isinstance(v, bool) and v >= 0 for v in arr):
                    errs.append(f"per_user.{key} must hold non-negative ints")
                elif kind is float and not all(_finite_number(v) for v in arr):
                    errs.append(f"per_user.{key} must hold finite numbers")
            if not errs and any(a + s != cfg.n_steps for a, s in zip(pu["accepted"], pu["skips"])):
                errs.append("per_user accepted + skips must equal n_steps for every listener")
    elif status == "failed":
        if not isinstance(obj["error"], str) or not obj["error"]:
            errs.append("a failed result needs a non-empty error string")
        for key in ("metrics", "diagnostics", "per_user"):
            if obj[key] is not None:
                errs.append(f"{key} must be null when status is failed")
    else:
        errs.append("status must be 'ok' or 'failed'")
    if errs:
        raise SchemaError("; ".join(errs))
    return obj


def dumps_result(obj: dict[str, Any]) -> str:
    """Validate, then serialise deterministically (sorted keys, fixed indent)."""
    validate_result(obj)
    return json.dumps(obj, sort_keys=True, indent=1, allow_nan=False) + "\n"


def write_result(obj: dict[str, Any], path: Path) -> None:
    text = dumps_result(obj)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read_result(path: Path) -> dict[str, Any]:
    """Read and validate; fail closed on malformed files."""
    try:
        obj = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SchemaError(f"{path}: not valid JSON ({exc})") from exc
    try:
        return validate_result(obj)
    except SchemaError as exc:
        raise SchemaError(f"{path}: {exc}") from exc
