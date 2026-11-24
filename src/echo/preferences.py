# SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
"""Preference update rules (protocol section 3; EXP-003 alternatives).

- consumed: p <- normalise((1 - eta) p + eta x_chosen), no update on skip.
- exposure: p <- normalise((1 - eta) p + eta mean(slate)), every step.
- bounded: as consumed, but only if cos(p, x_chosen) > threshold.

eta == 0 is the fixed preference model: the input is returned unchanged
(a copy), so drift is exactly zero rather than round-off from re-normalising.
"""

from __future__ import annotations

import numpy as np

from .config import UPDATE_RULES
from .vectors import normalise


def update_preferences(
    prefs: np.ndarray,
    rule: str,
    eta: float,
    chosen: np.ndarray,
    accepted: np.ndarray,
    slate_mean: np.ndarray,
    threshold: float,
) -> np.ndarray:
    """Return updated (U, d) preferences. Inputs are not mutated."""
    if rule not in UPDATE_RULES:
        raise ValueError(f"unknown update rule {rule!r}")
    if not 0.0 <= eta <= 1.0:
        raise ValueError("eta must lie in [0, 1]")
    p = np.asarray(prefs, dtype=np.float64)
    out = p.copy()
    if eta == 0.0:
        return out
    acc = np.asarray(accepted, dtype=bool)
    if rule == "consumed":
        mask, target = acc, chosen
    elif rule == "exposure":
        mask, target = np.ones(p.shape[0], dtype=bool), slate_mean
    else:  # bounded
        mask = acc & (np.sum(p * chosen, axis=1) > threshold)
        target = chosen
    if np.any(mask):
        out[mask] = normalise((1.0 - eta) * p[mask] + eta * np.asarray(target)[mask])
    return out


def update_one(p: np.ndarray, x: np.ndarray, eta: float) -> np.ndarray:
    """Single-listener consumed-item update (for tests and the demo)."""
    if not 0.0 <= eta <= 1.0:
        raise ValueError("eta must lie in [0, 1]")
    p = np.asarray(p, dtype=np.float64)
    if eta == 0.0:
        return p.copy()
    return normalise((1.0 - eta) * p + eta * np.asarray(x, dtype=np.float64))
