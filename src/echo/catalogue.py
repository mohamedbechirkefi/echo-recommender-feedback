# SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
"""Synthetic catalogue and listener generation (the ingestion layer).

The synthetic catalogue is derived from the seed and the configuration only.
Its cluster weights may be fitted on FMA metadata (protocol section 10.1);
the fitted values are part of the configuration. The "fma" catalogue
(EXP-004) samples real FMA tracks from the processed catalogue whose SHA-256
is in the configuration. Listeners are always simulated.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import SimConfig
from .fma import load_catalogue
from .manifest import REPO_ROOT
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


FMA_CATALOGUE_PATH = REPO_ROOT / "data" / "processed" / "fma_catalogue_v1.npz"


class CatalogueError(ValueError):
    """Raised when the configuration does not match the real catalogue."""


def real_catalogue(cfg: SimConfig, rng: np.random.Generator, path=None) -> Catalogue:
    """N real FMA tracks drawn uniformly without replacement (protocol 10.1).

    Base popularity is listens + 1, scaled to sum to N.
    """
    real = load_catalogue(FMA_CATALOGUE_PATH if path is None else path, cfg.fma_catalogue_sha256)
    m, d = real.embeddings.shape
    if d != cfg.dim:
        raise CatalogueError(f"dim {cfg.dim} differs from the real catalogue's {d}")
    if real.centres.shape[0] != cfg.n_clusters:
        raise CatalogueError(f"n_clusters {cfg.n_clusters} differs from the real catalogue's {real.centres.shape[0]}")
    if cfg.n_tracks > m:
        raise CatalogueError(f"n_tracks {cfg.n_tracks} exceeds the {m} eligible real tracks")
    idx = np.sort(rng.choice(m, size=cfg.n_tracks, replace=False))
    pop = real.listens[idx].astype(np.float64) + 1.0
    return Catalogue(embeddings=real.embeddings[idx].copy(), cluster=real.genre[idx].copy(),
                     centres=real.centres.copy(), base_pop=pop * (cfg.n_tracks / pop.sum()))


def generate_catalogue(cfg: SimConfig, rng: np.random.Generator) -> Catalogue:
    if cfg.catalogue == "fma":
        return real_catalogue(cfg, rng)
    k, d, n = cfg.n_clusters, cfg.dim, cfg.n_tracks
    centres = normalise(rng.standard_normal((k, d)))
    if cfg.cluster_weights is None:
        cluster = rng.integers(0, k, size=n)
    else:
        w = np.asarray(cfg.cluster_weights, dtype=np.float64)
        cluster = rng.choice(k, size=n, p=w / w.sum())
    x = normalise(centres[cluster] + cfg.track_spread * rng.standard_normal((n, d)))
    ranks = rng.permutation(n) + 1  # popularity independent of cluster
    return Catalogue(embeddings=x, cluster=cluster, centres=centres, base_pop=zipf_weights(n, cfg.zipf_s, ranks))


def generate_listeners(cfg: SimConfig, centres: np.ndarray, rng: np.random.Generator) -> Listeners:
    home = rng.integers(0, centres.shape[0], size=cfg.n_users)
    p0 = normalise(centres[home] + cfg.listener_spread * rng.standard_normal((cfg.n_users, cfg.dim)))
    return Listeners(initial=p0, home_cluster=home)
