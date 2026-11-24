# SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
"""The session loop (protocol section 3). Simulation only.

Random streams (common random numbers). The seed's SeedSequence spawns four
independent streams: catalogue, listeners, choice uniforms and policy keys.
Every policy, preference model and update rule under one seed therefore
sees the same catalogue, the same listeners and the same choice uniforms.
The policy stream draws the same number of values at every step whatever
the policy (U x N slate keys and U x k exploration flags), so it stays
aligned across arms too.

All listeners advance one step at a time (synchronous), so POP counts are
updated after every listener has chosen at step t.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .catalogue import Catalogue, Listeners, generate_catalogue, generate_listeners
from .choice import choice_probabilities, sample_choice
from .config import PERSONALISED_POLICIES, SimConfig
from .policies import explore_slate, mmr_slate, pop_slate, rand_slate, sim_slate
from .preferences import update_preferences


class SimulationError(RuntimeError):
    """Raised when the simulation reaches an invalid state."""


@dataclass
class Trace:
    """Raw end-of-session state, plus an optional per-step log."""

    config: SimConfig
    catalogue: Catalogue
    listeners: Listeners
    final_prefs: np.ndarray  # (U, d)
    accepted: np.ndarray  # (U,) int
    skips: np.ndarray  # (U,) int
    clusters_seen: np.ndarray  # (U, K) bool, clusters of consumed tracks
    novelty_sum: np.ndarray  # (U,) bits summed over consumed tracks
    rel_initial_sum: np.ndarray  # (U,) cos(p_u0, x_chosen) summed
    rel_current_sum: np.ndarray  # (U,) cos(p_ut, x_chosen) summed (pre-update)
    ild_sum: float  # sum over user-steps of intra-list diversity
    impressions: np.ndarray  # (N,) slate impressions
    exclusion_violations: int
    max_pref_norm_error: float
    slates: np.ndarray | None = None  # (T, U, k) if recorded
    choices: np.ndarray | None = None  # (T, U), track index or -1 for skip
    extra: dict = field(default_factory=dict)


def _ild(slate_emb: np.ndarray) -> np.ndarray:
    """Intra-list diversity per row: mean over pairs i < j of (1 - cos)."""
    k = slate_emb.shape[1]
    g = np.einsum("ukd,ujd->ukj", slate_emb, slate_emb)
    iu = np.triu_indices(k, 1)
    return (1.0 - g[:, iu[0], iu[1]]).mean(axis=1)


def simulate(cfg: SimConfig, record: bool = False) -> Trace:
    cfg.validate()
    ss = np.random.SeedSequence(cfg.seed)
    s_cat, s_lis, s_choice, s_policy = ss.spawn(4)
    cat = generate_catalogue(cfg, np.random.default_rng(s_cat))
    lis = generate_listeners(cfg, cat.centres, np.random.default_rng(s_lis))
    choice_u = np.random.default_rng(s_choice).random((cfg.n_steps, cfg.n_users))
    prng = np.random.default_rng(s_policy)

    U, N, K, k, T = cfg.n_users, cfg.n_tracks, cfg.n_clusters, cfg.slate_size, cfg.n_steps
    X = cat.embeddings
    rows = np.arange(U)
    self_info = -np.log2(cat.base_pop / cat.base_pop.sum())

    P = lis.initial.copy()
    consumed = np.zeros((U, N), dtype=bool)
    consumed_sum = np.zeros((U, cfg.dim))
    accepted = np.zeros(U, dtype=np.int64)
    skips = np.zeros(U, dtype=np.int64)
    clusters_seen = np.zeros((U, K), dtype=bool)
    novelty_sum = np.zeros(U)
    rel0 = np.zeros(U)
    relt = np.zeros(U)
    ild_sum = 0.0
    impressions = np.zeros(N, dtype=np.int64)
    counts = np.zeros(N)
    violations = 0
    max_norm_err = float(np.max(np.abs(np.linalg.norm(P, axis=1) - 1.0)))
    slates_log = np.empty((T, U, k), dtype=np.int64) if record else None
    choices_log = np.empty((T, U), dtype=np.int64) if record else None

    for t in range(T):
        keys = prng.random((U, N))
        flags = prng.random((U, k))
        slate = rand_slate(keys, consumed, k)
        if cfg.policy == "POP":
            slate = pop_slate(counts + cat.base_pop, consumed, k)
        elif cfg.policy in PERSONALISED_POLICIES:
            if cfg.profile == "oracle":
                prof, valid = P, np.ones(U, dtype=bool)
            else:
                norms = np.linalg.norm(consumed_sum, axis=1)
                valid = (accepted > 0) & (norms > 1e-12)
                prof = np.zeros_like(consumed_sum)
                prof[valid] = consumed_sum[valid] / norms[valid, None]
            use = valid & (t >= cfg.warmup_steps)
            if np.any(use):
                sub_ex = consumed[use]
                if cfg.policy == "SIM":
                    pers = sim_slate(prof[use], X, sub_ex, k)
                elif cfg.policy == "MMR":
                    pers = mmr_slate(prof[use], X, sub_ex, k, cfg.mmr_lambda)
                else:
                    pers = explore_slate(prof[use], X, sub_ex, k, keys[use], flags[use], cfg.explore_epsilon)
                slate = slate.copy()
                slate[use] = pers

        violations += int(consumed[rows[:, None], slate].sum())
        np.add.at(impressions, slate.ravel(), 1)
        semb = X[slate]  # (U, k, d)
        ild_sum += float(_ild(semb).sum())

        cos_slate = np.einsum("ud,ukd->uk", P, semb)
        pick = sample_choice(choice_probabilities(cos_slate, cfg.tau, cfg.skip_utility), choice_u[t])
        acc = pick < k
        chosen_idx = np.where(acc, slate[rows, np.minimum(pick, k - 1)], -1)
        chosen_emb = np.where(acc[:, None], X[np.maximum(chosen_idx, 0)], 0.0)

        a_rows = rows[acc]
        a_items = chosen_idx[acc]
        rel0[acc] += np.sum(lis.initial[acc] * chosen_emb[acc], axis=1)
        relt[acc] += np.sum(P[acc] * chosen_emb[acc], axis=1)
        novelty_sum[acc] += self_info[a_items]
        clusters_seen[a_rows, cat.cluster[a_items]] = True
        consumed[a_rows, a_items] = True
        consumed_sum[acc] += chosen_emb[acc]
        accepted += acc
        skips += ~acc
        counts += np.bincount(a_items, minlength=N)

        if cfg.preference_model == "adaptive":
            P = update_preferences(P, cfg.update_rule, cfg.eta, chosen_emb, acc, semb.mean(axis=1), cfg.bounded_threshold)
            max_norm_err = max(max_norm_err, float(np.max(np.abs(np.linalg.norm(P, axis=1) - 1.0))))
        if not np.all(np.isfinite(P)):
            raise SimulationError(f"non-finite preference at step {t}")
        if record:
            slates_log[t] = slate
            choices_log[t] = chosen_idx

    return Trace(
        config=cfg,
        catalogue=cat,
        listeners=lis,
        final_prefs=P,
        accepted=accepted,
        skips=skips,
        clusters_seen=clusters_seen,
        novelty_sum=novelty_sum,
        rel_initial_sum=rel0,
        rel_current_sum=relt,
        ild_sum=ild_sum,
        impressions=impressions,
        exclusion_violations=violations,
        max_pref_norm_error=max_norm_err,
        slates=slates_log,
        choices=choices_log,
    )
