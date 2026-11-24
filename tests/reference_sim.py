# SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
"""Slow, loop-based reference implementation of the protocol section 3 model.

Used only for differential tests against the vectorised ``echo.simulate``.
It shares the generators and the random-stream layout (they define the
model inputs) but re-implements policies, choice, updates and bookkeeping
with plain Python loops over listeners, candidates and slate positions.
"""

from __future__ import annotations

import math

import numpy as np

from echo.catalogue import generate_catalogue, generate_listeners
from echo.config import SimConfig


def _norm(v):
    n = math.sqrt(sum(a * a for a in v))
    return [a / n for a in v]


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def reference_simulate(cfg: SimConfig):
    assert cfg.policy in ("RAND", "POP", "SIM", "MMR", "EXPLORE")
    assert cfg.update_rule == "consumed" and cfg.profile == "estimated"
    ss = np.random.SeedSequence(cfg.seed)
    s_cat, s_lis, s_choice, s_policy = ss.spawn(4)
    cat = generate_catalogue(cfg, np.random.default_rng(s_cat))
    lis = generate_listeners(cfg, cat.centres, np.random.default_rng(s_lis))
    choice_u = np.random.default_rng(s_choice).random((cfg.n_steps, cfg.n_users))
    prng = np.random.default_rng(s_policy)
    X = cat.embeddings.tolist()
    U, N, k = cfg.n_users, cfg.n_tracks, cfg.slate_size
    P = [list(row) for row in lis.initial.tolist()]
    consumed = [set() for _ in range(U)]
    csum = [[0.0] * cfg.dim for _ in range(U)]
    counts = [0.0] * N
    base = cat.base_pop.tolist()
    accepted = [0] * U
    slates = []
    for t in range(cfg.n_steps):
        keys = prng.random((U, N))
        flags = prng.random((U, k))
        step_slates = []
        for u in range(U):
            cand = [j for j in range(N) if j not in consumed[u]]
            rand_order = sorted(cand, key=lambda j: (keys[u, j], j))
            if cfg.policy == "RAND":
                slate = rand_order[:k]
            elif cfg.policy == "POP":
                pop = [counts[j] + base[j] for j in range(N)]
                slate = sorted(cand, key=lambda j: (-pop[j], j))[:k]
            else:
                if t < cfg.warmup_steps or accepted[u] == 0:
                    slate = rand_order[:k]
                else:
                    prof = _norm(csum[u])
                    rel = {j: _dot(prof, X[j]) for j in cand}
                    sim_order = sorted(cand, key=lambda j: (-rel[j], j))
                    if cfg.policy == "SIM":
                        slate = sim_order[:k]
                    elif cfg.policy == "MMR":
                        slate = []
                        lam = cfg.mmr_lambda
                        for pos in range(k):
                            best, best_s = None, -math.inf
                            for j in cand:
                                if j in slate:
                                    continue
                                if pos == 0:
                                    s = rel[j]
                                else:
                                    s = lam * rel[j] - (1 - lam) * max(_dot(X[j], X[q]) for q in slate)
                                if s > best_s:
                                    best, best_s = j, s
                            slate.append(best)
                    else:
                        slate = []
                        si, ri = iter(sim_order), iter(rand_order)
                        for pos in range(k):
                            src = ri if flags[u, pos] < cfg.explore_epsilon else si
                            item = next(src)
                            while item in slate:
                                item = next(src)
                            slate.append(item)
            step_slates.append(slate)
        slates.append(step_slates)
        chosen = []
        for u in range(U):
            logits = [_dot(P[u], X[j]) / cfg.tau for j in step_slates[u]] + [cfg.skip_utility / cfg.tau]
            m = max(logits)
            e = [math.exp(v - m) for v in logits]
            z = sum(e)
            cum, pick = 0.0, k
            for i, v in enumerate(e[:-1]):
                cum += v / z
                if choice_u[t, u] < cum:
                    pick = i
                    break
            chosen.append(step_slates[u][pick] if pick < k else -1)
        for u in range(U):
            c = chosen[u]
            if c < 0:
                continue
            consumed[u].add(c)
            accepted[u] += 1
            csum[u] = [a + b for a, b in zip(csum[u], X[c])]
            counts[c] += 1
            if cfg.preference_model == "adaptive":
                P[u] = _norm([(1 - cfg.eta) * a + cfg.eta * b for a, b in zip(P[u], X[c])])
    p0 = lis.initial.tolist()
    drift = []
    for u in range(U):
        a, b = _norm(p0[u]), _norm(P[u])
        chord = math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))
        drift.append(2 * math.asin(min(1.0, chord / 2)))
    return {"slates": slates, "accepted": accepted, "drift": drift, "final": P}
