# SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
"""EXP-001 verification checks V1 to V6 (exploratory; never a finding).

V1 identical config and seed give byte-identical result JSON.
V2 with eta = 0 (fixed model), theta_u = 0 exactly for every user and policy.
V3 no consumed track reappears in a later slate (from the per-step log).
V4 embeddings and preferences have unit norm within 1e-12.
V5 every metric lies inside its stated bounds.
V6 every written result file validates against echo.result.v1 on re-read.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from .metrics import check_bounds
from .runner import execute
from .schema import SchemaError, dumps_result, read_result

NORM_TOL = 1e-12


def exclusion_violations_from_log(slates: np.ndarray, choices: np.ndarray, n_tracks: int) -> int:
    """Independent re-check of candidate exclusion from the logged slates and choices."""
    T, U, _ = slates.shape
    consumed = np.zeros((U, n_tracks), dtype=bool)
    bad = 0
    for t in range(T):
        for u in range(U):
            bad += int(consumed[u, slates[t, u]].sum())
            if len(set(slates[t, u].tolist())) != slates.shape[2]:
                bad += 1  # duplicate inside a slate
            c = choices[t, u]
            if c >= 0:
                consumed[u, c] = True
    return bad


def run_checks(summaries: list[dict[str, Any]], out_dir: Path, experiment_id: str, label: str) -> dict[str, Any]:
    checks: dict[str, Any] = {}

    # V1: re-execute the smoke block in-process and compare bytes.
    smoke = [s for s in summaries if s["run"].block == "smoke"]
    mismatches = []
    for s in smoke:
        again, _, _ = execute(s["run"], experiment_id, label)
        if dumps_result(again) != s["text"]:
            mismatches.append(s["run"].run_id)
    checks["V1_determinism"] = {"pass": not mismatches and bool(smoke), "runs_compared": len(smoke), "mismatches": mismatches}

    # V2: fixed preference model gives exactly zero drift.
    fixed = [s for s in summaries if s["run"].config.preference_model == "fixed" and s["result"]["status"] == "ok"]
    nonzero = [s["run"].run_id for s in fixed if any(v != 0.0 for v in s["result"]["per_user"]["drift_rad"])]
    checks["V2_zero_drift_fixed"] = {"pass": not nonzero and bool(fixed), "runs_checked": len(fixed), "failing_runs": nonzero}

    # V3: candidate exclusion from the log (runs executed with record=True).
    logged = [s for s in summaries if s["trace"] is not None and s["trace"].slates is not None]
    v3 = {s["run"].run_id: exclusion_violations_from_log(s["trace"].slates, s["trace"].choices, s["run"].config.n_tracks) for s in logged}
    in_sim = sum(s["result"]["diagnostics"]["exclusion_violations"] for s in summaries if s["result"]["status"] == "ok")
    checks["V3_candidate_exclusion"] = {
        "pass": bool(logged) and all(v == 0 for v in v3.values()) and in_sim == 0,
        "runs_checked_from_log": len(logged),
        "log_violations": sum(v3.values()),
        "in_simulation_counter_all_runs": in_sim,
    }

    # V4: unit norms.
    worst = 0.0
    for s in summaries:
        tr = s["trace"]
        if tr is None:
            continue
        for arr in (tr.catalogue.embeddings, tr.catalogue.centres, tr.listeners.initial, tr.final_prefs):
            worst = max(worst, float(np.max(np.abs(np.linalg.norm(arr, axis=1) - 1.0))))
        worst = max(worst, tr.max_pref_norm_error)
    checks["V4_unit_norm"] = {"pass": worst <= NORM_TOL, "max_abs_norm_error": worst, "tolerance": NORM_TOL}

    # V5: metric bounds.
    oob = {}
    for s in summaries:
        if s["result"]["status"] == "ok":
            probs = check_bounds(s["result"]["metrics"], s["result"]["diagnostics"])
            if probs:
                oob[s["run"].run_id] = probs
    n_failed = sum(1 for s in summaries if s["result"]["status"] != "ok")
    checks["V5_metric_bounds"] = {"pass": not oob and n_failed == 0, "violations": oob, "failed_runs": n_failed}

    # V6: re-read every written result file through the validator.
    bad_files = []
    files = sorted((out_dir / "runs").glob("*.json"))
    for f in files:
        try:
            read_result(f)
        except SchemaError as exc:
            bad_files.append(str(exc))
    checks["V6_schema"] = {"pass": bool(files) and not bad_files, "files_validated": len(files), "invalid": bad_files}

    checks["all_pass"] = all(v["pass"] for k, v in checks.items() if k.startswith("V"))
    path = out_dir / "checks.json"
    path.write_text(json.dumps(checks, sort_keys=True, indent=1) + "\n", encoding="utf-8")
    return checks
