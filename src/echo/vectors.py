# SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
"""Pure vector functions: normalisation, cosine similarity and angles.

Error paths are explicit: zero-norm or non-finite input raises ValueError
instead of returning NaN.
"""

from __future__ import annotations

import numpy as np

NORM_EPS = 1e-12


def normalise(v: np.ndarray) -> np.ndarray:
    """Return ``v`` scaled to unit L2 norm along the last axis.

    Raises ValueError for non-finite entries or rows with norm < NORM_EPS.
    """
    a = np.asarray(v, dtype=np.float64)
    if a.ndim == 0:
        raise ValueError("cannot normalise a scalar")
    if not np.all(np.isfinite(a)):
        raise ValueError("cannot normalise a vector with non-finite entries")
    norms = np.linalg.norm(a, axis=-1, keepdims=True)
    if np.any(norms < NORM_EPS):
        raise ValueError("cannot normalise a zero-norm vector")
    return a / norms


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity of two 1-D vectors, clipped to [-1, 1]."""
    x = np.asarray(a, dtype=np.float64)
    y = np.asarray(b, dtype=np.float64)
    if x.ndim != 1 or y.ndim != 1 or x.shape != y.shape:
        raise ValueError(f"cosine needs two 1-D vectors of equal length, got {x.shape} and {y.shape}")
    if not (np.all(np.isfinite(x)) and np.all(np.isfinite(y))):
        raise ValueError("cosine of non-finite vectors is undefined")
    nx = float(np.linalg.norm(x))
    ny = float(np.linalg.norm(y))
    if nx < NORM_EPS or ny < NORM_EPS:
        raise ValueError("cosine with a zero-norm vector is undefined")
    return float(np.clip(np.dot(x, y) / (nx * ny), -1.0, 1.0))


def angle(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Angle in radians between rows of ``a`` and ``b`` (after normalisation).

    Uses theta = 2 * arcsin(||a_hat - b_hat|| / 2), which equals
    arccos(clip(<a_hat, b_hat>, -1, 1)) for unit vectors (protocol section 4)
    but is exactly 0 for identical inputs and accurate near 0, where arccos
    loses about half of the significant digits.
    """
    ua = normalise(a)
    ub = normalise(b)
    chord = np.linalg.norm(ua - ub, axis=-1)
    return 2.0 * np.arcsin(np.clip(chord / 2.0, 0.0, 1.0))


def angle_arccos(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Protocol formula arccos(clip(<a_hat, b_hat>, -1, 1)); used as a differential reference."""
    ua = normalise(a)
    ub = normalise(b)
    return np.arccos(np.clip(np.sum(ua * ub, axis=-1), -1.0, 1.0))


def mean_pairwise_cosine(rows: np.ndarray) -> float:
    """Mean cosine over all ordered pairs i != j of the rows."""
    u = normalise(rows)
    n = u.shape[0]
    if n < 2:
        raise ValueError("mean pairwise cosine needs at least two rows")
    g = u @ u.T
    return float((g.sum() - np.trace(g)) / (n * (n - 1)))
