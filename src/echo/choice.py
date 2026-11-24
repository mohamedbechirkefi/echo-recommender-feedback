# SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
"""Listener choice: softmax over slate items plus a skip option."""

from __future__ import annotations

import numpy as np


def choice_probabilities(slate_cos: np.ndarray, tau: float, skip_utility: float) -> np.ndarray:
    """Return (U, k + 1) probabilities; the last column is the skip option.

    Logit of slate item j is cos_j / tau; logit of skip is skip_utility / tau.
    """
    c = np.asarray(slate_cos, dtype=np.float64)
    if c.ndim != 2:
        raise ValueError("slate_cos must be a 2-D array (users, slate)")
    if not tau > 0:
        raise ValueError("tau must be > 0")
    if not np.all(np.isfinite(c)):
        raise ValueError("slate cosines must be finite")
    logits = np.concatenate([c / tau, np.full((c.shape[0], 1), skip_utility / tau)], axis=1)
    logits -= logits.max(axis=1, keepdims=True)
    e = np.exp(logits)
    return e / e.sum(axis=1, keepdims=True)


def sample_choice(probs: np.ndarray, u: np.ndarray) -> np.ndarray:
    """Inverse-CDF sampling with pre-drawn uniforms ``u`` in [0, 1).

    Returns the chosen column per row; the value k (last column) means skip.
    Using pre-drawn uniforms gives common random numbers across policies.
    """
    p = np.asarray(probs, dtype=np.float64)
    uu = np.asarray(u, dtype=np.float64)
    if p.ndim != 2 or uu.shape != (p.shape[0],):
        raise ValueError("probs must be (U, m) and u must be (U,)")
    if np.any(uu < 0.0) or np.any(uu >= 1.0):
        raise ValueError("uniforms must lie in [0, 1)")
    cum = np.cumsum(p, axis=1)
    cum[:, -1] = 1.0  # guard against round-off in the last cumulative value
    return (cum <= uu[:, None]).sum(axis=1)
