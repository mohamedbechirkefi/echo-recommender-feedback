# SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
"""Outcome metrics (protocol section 4). Pure functions of a Trace.

Per-listener averages over consumed tracks (novelty, relevance, drift per
accepted item) are taken over listeners with at least one accepted track;
the number of listeners without any acceptance is reported as a diagnostic.
"""

from __future__ import annotations

import math

import numpy as np

from .simulate import Trace
from .vectors import angle, mean_pairwise_cosine

METRIC_NAMES = (
    "drift_rad",
    "homogenisation",
    "discovery",
    "novelty_bits",
    "diversity_ild",
    "relevance_initial",
    "relevance_current",
    "exposure_gini",
    "skip_rate",
    "drift_per_accept_rad",
)

# Closed bounds used by verification check V5. novelty_bits is bounded by the
# largest self-information in the catalogue, checked separately.
METRIC_BOUNDS = {
    "drift_rad": (0.0, math.pi),
    "homogenisation": (-2.0, 2.0),
    "discovery": (0.0, 1.0),
    "novelty_bits": (0.0, math.inf),
    "diversity_ild": (0.0, 2.0),
    "relevance_initial": (-1.0, 1.0),
    "relevance_current": (-1.0, 1.0),
    "exposure_gini": (0.0, 1.0),
    "skip_rate": (0.0, 1.0),
    "drift_per_accept_rad": (0.0, math.pi),
}


BOUND_TOL = 1e-12  # round-off slack for cosine-valued averages


def gini(values: np.ndarray) -> float:
    """Gini coefficient of non-negative values: sum_ij |x_i - x_j| / (2 n^2 mean)."""
    x = np.sort(np.asarray(values, dtype=np.float64).ravel())
    if x.size == 0:
        raise ValueError("gini of an empty array is undefined")
    if np.any(x < 0) or not np.all(np.isfinite(x)):
        raise ValueError("gini needs finite non-negative values")
    total = x.sum()
    if total == 0:
        raise ValueError("gini of an all-zero array is undefined")
    n = x.size
    i = np.arange(1, n + 1)
    return float(2.0 * np.sum(i * x) / (n * total) - (n + 1.0) / n)


def per_user_drift(trace: Trace) -> np.ndarray:
    return angle(trace.listeners.initial, trace.final_prefs)


def compute_metrics(trace: Trace) -> tuple[dict, dict, dict]:
    """Return (metrics, diagnostics, per_user)."""
    cfg = trace.config
    theta = per_user_drift(trace)
    acc = trace.accepted
    has = acc > 0
    n_has = int(has.sum())

    def over_accepting(num: np.ndarray) -> float:
        if n_has == 0:
            return float("nan")
        return float(np.mean(num[has] / acc[has]))

    metrics = {
        "drift_rad": float(theta.mean()),
        "homogenisation": mean_pairwise_cosine(trace.final_prefs) - mean_pairwise_cosine(trace.listeners.initial),
        "discovery": float(trace.clusters_seen.sum(axis=1).mean() / cfg.n_clusters),
        "novelty_bits": over_accepting(trace.novelty_sum),
        "diversity_ild": trace.ild_sum / (cfg.n_users * cfg.n_steps),
        "relevance_initial": over_accepting(trace.rel_initial_sum),
        "relevance_current": over_accepting(trace.rel_current_sum),
        "exposure_gini": gini(trace.impressions),
        "skip_rate": float(trace.skips.mean() / cfg.n_steps),
        "drift_per_accept_rad": over_accepting(theta),
    }
    emb_err = float(np.max(np.abs(np.linalg.norm(trace.catalogue.embeddings, axis=1) - 1.0)))
    diagnostics = {
        "users_without_accept": int(cfg.n_users - n_has),
        "accepted_total": int(acc.sum()),
        "exclusion_violations": int(trace.exclusion_violations),
        "max_pref_norm_error": float(trace.max_pref_norm_error),
        "max_embedding_norm_error": emb_err,
        "max_self_information_bits": float(np.max(-np.log2(trace.catalogue.base_pop / trace.catalogue.base_pop.sum()))),
        "users_with_zero_drift": int(np.sum(theta == 0.0)),
    }
    per_user = {
        "drift_rad": [float(v) for v in theta],
        "accepted": [int(v) for v in acc],
        "skips": [int(v) for v in trace.skips],
    }
    return metrics, diagnostics, per_user


def check_bounds(metrics: dict, diagnostics: dict) -> list[str]:
    """Return a list of bound violations (empty when all metrics are in bounds)."""
    problems = []
    for name in METRIC_NAMES:
        v = metrics.get(name)
        lo, hi = METRIC_BOUNDS[name]
        if v is None or not math.isfinite(v):
            problems.append(f"{name} is not finite: {v}")
        elif not lo - BOUND_TOL <= v <= hi + BOUND_TOL:
            problems.append(f"{name}={v} outside [{lo}, {hi}]")
    nov = metrics.get("novelty_bits")
    cap = diagnostics.get("max_self_information_bits")
    if nov is not None and cap is not None and math.isfinite(nov) and nov > cap + 1e-12:
        problems.append(f"novelty_bits={nov} above the catalogue maximum {cap}")
    return problems
