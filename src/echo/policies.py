# SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
"""Recommendation policies (protocol section 3), vectorised over listeners.

Every policy returns a (U, k) array of track indices drawn only from
candidates (tracks the listener has not consumed). Ties are broken by the
lower track index, so every slate is deterministic given its inputs.
"""

from __future__ import annotations

import numpy as np


def _check(excluded: np.ndarray, k: int) -> None:
    if excluded.ndim != 2:
        raise ValueError("excluded must be a (U, N) boolean array")
    if k < 1:
        raise ValueError("slate size must be >= 1")
    if np.any((~excluded).sum(axis=1) < k):
        raise ValueError("candidate pool smaller than the slate size")


def top_k(scores: np.ndarray, excluded: np.ndarray, k: int) -> np.ndarray:
    """Indices of the k highest scores among non-excluded columns, per row."""
    _check(excluded, k)
    s = np.where(excluded, -np.inf, np.asarray(scores, dtype=np.float64))
    return np.argsort(-s, axis=1, kind="stable")[:, :k]


def rand_slate(keys: np.ndarray, excluded: np.ndarray, k: int) -> np.ndarray:
    """RAND: uniform random slate without replacement (k smallest random keys)."""
    _check(excluded, k)
    s = np.where(excluded, np.inf, keys)
    return np.argsort(s, axis=1, kind="stable")[:, :k]


def pop_slate(popularity: np.ndarray, excluded: np.ndarray, k: int) -> np.ndarray:
    """POP: top-k by global popularity (consumption count plus base popularity)."""
    scores = np.broadcast_to(np.asarray(popularity, dtype=np.float64), excluded.shape)
    return top_k(scores, excluded, k)


def sim_slate(profile: np.ndarray, emb: np.ndarray, excluded: np.ndarray, k: int) -> np.ndarray:
    """SIM: top-k by cosine to the (unit) profile."""
    return top_k(profile @ emb.T, excluded, k)


def mmr_slate(profile: np.ndarray, emb: np.ndarray, excluded: np.ndarray, k: int, lam: float) -> np.ndarray:
    """MMR: greedy maximal marginal relevance.

    Pick 1 is argmax relevance. Pick j > 1 maximises
    lam * cos(profile, x) - (1 - lam) * max_{s in slate} cos(x, x_s).
    """
    _check(excluded, k)
    if not 0.0 < lam <= 1.0:
        raise ValueError("mmr lambda must lie in (0, 1]")
    rel = profile @ emb.T
    n_users = rel.shape[0]
    rows = np.arange(n_users)
    blocked = excluded.copy()
    slate = np.empty((n_users, k), dtype=np.int64)
    maxsim = None
    for j in range(k):
        score = rel if maxsim is None else lam * rel - (1.0 - lam) * maxsim
        score = np.where(blocked, -np.inf, score)
        pick = np.argmax(score, axis=1)
        slate[:, j] = pick
        blocked[rows, pick] = True
        sims = emb[pick] @ emb.T
        maxsim = sims if maxsim is None else np.maximum(maxsim, sims)
    return slate


def explore_slate(
    profile: np.ndarray,
    emb: np.ndarray,
    excluded: np.ndarray,
    k: int,
    keys: np.ndarray,
    flags: np.ndarray,
    epsilon: float,
) -> np.ndarray:
    """EXPLORE: epsilon-greedy per slot.

    Slot j is a random candidate if flags[u, j] < epsilon, otherwise the next
    best SIM candidate. Random candidates follow the RAND key order. No track
    appears twice in a slate.
    """
    _check(excluded, k)
    if not 0.0 <= epsilon <= 1.0:
        raise ValueError("epsilon must lie in [0, 1]")
    # Each source needs at most 2k entries to fill k distinct slots; if the pool
    # is smaller than 2k, both orders cover the whole pool.
    depth = int(min(2 * k, (~excluded).sum(axis=1).min()))
    sim_order = top_k(profile @ emb.T, excluded, depth)
    rnd_order = rand_slate(keys, excluded, depth)
    is_rand = flags < epsilon
    out = np.empty((excluded.shape[0], k), dtype=np.int64)
    for u in range(excluded.shape[0]):
        used: set[int] = set()
        it = {True: iter(rnd_order[u].tolist()), False: iter(sim_order[u].tolist())}
        for j in range(k):
            src = it[bool(is_rand[u, j])]
            item = next(src)
            while item in used:
                item = next(src)
            used.add(item)
            out[u, j] = item
    return out
