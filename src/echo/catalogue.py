# SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
"""Synthetic catalogue and listener generation (the ingestion layer).

There is no external data (DEC-002). Every quantity below is derived from
the seed and the configuration only.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import SimConfig
from .vectors import normalise


@dataclass(frozen=True)
class Catalogue:
    embeddings: np.ndarray  # (N, d) unit rows
    cluster: np.ndarray  # (N,) int cluster label in [0, K)
    centres: np.ndarray  # (K, d) unit rows
    base_pop: np.ndarray  # (N,) positive Zipf weights, scaled to sum to N


@dataclass(frozen=True)
class Listeners:
    initial: np.ndarray  # (U, d) unit rows, p_u,0
    home_cluster: np.ndarray  # (U,) cluster whose centre seeded p_u,0


def zipf_weights(n: int, s: float, ranks: np.ndarray) -> np.ndarray:
    """Weights proportional to rank**(-s), scaled to sum to n (mean 1)."""
    if n < 1:
        raise ValueError("n must be >= 1")
    r = np.asarray(ranks, dtype=np.float64)
    if r.shape != (n,) or np.any(r < 1):
        raise ValueError("ranks must be a length-n array of values >= 1")
    w = r ** (-float(s))
    return w * (n / w.sum())


def generate_catalogue(cfg: SimConfig, rng: np.random.Generator) -> Catalogue:
    k, d, n = cfg.n_clusters, cfg.dim, cfg.n_tracks
    centres = normalise(rng.standard_normal((k, d)))
    cluster = rng.integers(0, k, size=n)
    x = normalise(centres[cluster] + cfg.track_spread * rng.standard_normal((n, d)))
    ranks = rng.permutation(n) + 1  # popularity independent of cluster
    return Catalogue(embeddings=x, cluster=cluster, centres=centres, base_pop=zipf_weights(n, cfg.zipf_s, ranks))


def generate_listeners(cfg: SimConfig, centres: np.ndarray, rng: np.random.Generator) -> Listeners:
    home = rng.integers(0, centres.shape[0], size=cfg.n_users)
    p0 = normalise(centres[home] + cfg.listener_spread * rng.standard_normal((cfg.n_users, cfg.dim)))
    return Listeners(initial=p0, home_cluster=home)
