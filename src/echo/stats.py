# SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
"""Seed-level uncertainty (protocol section 5). The seed is the unit."""

from __future__ import annotations

import math

import numpy as np

# Two-sided 95 % Student t quantiles t_{0.975, df}.
_T975 = {
    1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262,
    10: 2.228, 11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131, 16: 2.120, 17: 2.110,
    18: 2.101, 19: 2.093, 20: 2.086, 21: 2.080, 22: 2.074, 23: 2.069, 24: 2.064, 25: 2.060,
    26: 2.056, 27: 2.052, 28: 2.048, 29: 2.045, 30: 2.042, 40: 2.021, 60: 2.000, 120: 1.980,
}


def t975(df: int) -> float:
    if df not in _T975:
        raise ValueError(f"no tabulated t quantile for df={df}")
    return _T975[df]


def _diffs(d) -> np.ndarray:
    a = np.asarray(d, dtype=np.float64).ravel()
    if a.size < 2:
        raise ValueError("need at least two paired differences")
    if not np.all(np.isfinite(a)):
        raise ValueError("differences must be finite")
    return a


def paired_bootstrap_ci(diffs, n_resamples: int = 10_000, seed: int = 7, level: float = 0.95) -> tuple[float, float]:
    """Percentile bootstrap CI of the mean paired difference (resampling seeds)."""
    a = _diffs(diffs)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, a.size, size=(n_resamples, a.size))
    means = a[idx].mean(axis=1)
    lo, hi = np.quantile(means, [(1 - level) / 2, 1 - (1 - level) / 2])
    return float(lo), float(hi)


def paired_t_ci(diffs) -> tuple[float, float]:
    a = _diffs(diffs)
    half = t975(a.size - 1) * a.std(ddof=1) / math.sqrt(a.size)
    m = float(a.mean())
    return m - half, m + half


def cohen_dz(diffs) -> float:
    a = _diffs(diffs)
    sd = a.std(ddof=1)
    if sd == 0:
        raise ValueError("d_z undefined when all differences are equal")
    return float(a.mean() / sd)


def projected_half_width(sd: float, n: int) -> float:
    """Projected 95 % paired t half-width with n seeds, given a pilot SD."""
    return t975(n - 1) * sd / math.sqrt(n)


def decide(ci: tuple[float, float], sesoi: float) -> str:
    """Protocol section 2 decision rule."""
    lo, hi = ci
    if lo > hi:
        raise ValueError("ci lower bound above upper bound")
    excludes_zero = lo > 0 or hi < 0
    inside_band = -sesoi <= lo and hi <= sesoi
    if excludes_zero and inside_band:
        # Protocol section 10.2 item 4 (owner-approved 2026-11-24).
        return "statistically detectable, practically negligible"
    if excludes_zero:
        return "reject H0"
    if inside_band:
        return "practically equivalent"
    return "inconclusive"
