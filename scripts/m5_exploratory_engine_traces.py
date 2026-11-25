# SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
"""M5 exploratory engine traces (EXPLORATORY, never confirmatory).

Two small runs of the Python research engine (`echo.simulate`), both with
exploratory seeds that are disjoint from the confirmatory seeds 20261124 to
20261133. Neither changes or replaces any frozen result.

1. The sandbox fixture, `demo/src/fixtures/engine_fixture.json`: a tiny
   session (N = 40 tracks, U = 5 listeners, T = 20 steps, k = 5) with the
   random inputs the engine drew (catalogue, initial tastes, policy keys,
   exploration flags, choice uniforms) and its outputs (slates, choices,
   final preferences, per-listener drift, metrics) for nine arms. The
   browser port in `demo/src/engine.ts` is fed the same random inputs and
   must reproduce the outputs (`demo/src/engine.test.ts`).
2. The published taste map, `results/exploratory/M5-taste-map/trace.json`:
   one exploratory seed (950001) of the EXP-002 setting (calibrated synthetic
   catalogue, consumed-item rule, eta 0.05, estimated profile, N = 1000,
   U = 200, T = 100) for the five policies. It stores a 2-D principal-
   component projection of the catalogue, the projected preference
   trajectories of three listeners per policy and the per-step mean drift
   over all 200 listeners. One seed, no interval: an illustration of the
   mechanism, not a result.

Usage:
    PYTHONPATH=src .venv/bin/python scripts/m5_exploratory_engine_traces.py [--check]

With --check nothing is written; the exit code is 1 if either committed file
differs from what this script would write.
"""

from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from echo.catalogue import generate_catalogue  # noqa: E402
from echo.config import CONFIRMATORY_SEEDS, SimConfig  # noqa: E402
from echo.metrics import compute_metrics  # noqa: E402
from echo.preferences import update_preferences  # noqa: E402
from echo.simulate import simulate  # noqa: E402
from echo.vectors import angle  # noqa: E402

FIXTURE = REPO / "demo" / "src" / "fixtures" / "engine_fixture.json"
TASTE_MAP = REPO / "results" / "exploratory" / "M5-taste-map" / "trace.json"
EXP002_CONFIG = REPO / "experiments" / "EXP-002" / "config.json"

FIXTURE_SEED = 950000
TASTE_MAP_SEED = 950001
assert FIXTURE_SEED not in CONFIRMATORY_SEEDS and TASTE_MAP_SEED not in CONFIRMATORY_SEEDS

FIXTURE_ARMS = [
    {"policy": "RAND", "preference_model": "adaptive", "update_rule": "consumed", "eta": 0.05, "profile": "estimated"},
    {"policy": "POP", "preference_model": "adaptive", "update_rule": "consumed", "eta": 0.05, "profile": "estimated"},
    {"policy": "SIM", "preference_model": "adaptive", "update_rule": "consumed", "eta": 0.05, "profile": "estimated"},
    {"policy": "MMR", "preference_model": "adaptive", "update_rule": "consumed", "eta": 0.05, "profile": "estimated"},
    {"policy": "EXPLORE", "preference_model": "adaptive", "update_rule": "consumed", "eta": 0.05, "profile": "estimated"},
    {"policy": "SIM", "preference_model": "adaptive", "update_rule": "exposure", "eta": 0.2, "profile": "estimated"},
    {"policy": "SIM", "preference_model": "adaptive", "update_rule": "bounded", "eta": 0.2, "profile": "estimated"},
    {"policy": "SIM", "preference_model": "adaptive", "update_rule": "consumed", "eta": 0.05, "profile": "oracle"},
    {"policy": "RAND", "preference_model": "fixed", "update_rule": "consumed", "eta": 0.0, "profile": "estimated"},
]


def random_inputs(cfg: SimConfig):
    """Redraw the engine's four random streams exactly as `simulate` draws them."""
    ss = np.random.SeedSequence(cfg.seed)
    s_cat, s_lis, s_choice, s_policy = ss.spawn(4)
    choice_u = np.random.default_rng(s_choice).random((cfg.n_steps, cfg.n_users))
    prng = np.random.default_rng(s_policy)
    keys, flags = [], []
    for _ in range(cfg.n_steps):
        keys.append(prng.random((cfg.n_users, cfg.n_tracks)))
        flags.append(prng.random((cfg.n_users, cfg.slate_size)))
    return choice_u, np.stack(keys), np.stack(flags)


def replay_preferences(trace) -> np.ndarray:
    """(T + 1, U, d) preference path rebuilt from the recorded slates and choices."""
    cfg = trace.config
    X = trace.catalogue.embeddings
    P = trace.listeners.initial.copy()
    path = [P.copy()]
    for t in range(cfg.n_steps):
        chosen = trace.choices[t]
        acc = chosen >= 0
        emb = np.where(acc[:, None], X[np.maximum(chosen, 0)], 0.0)
        if cfg.preference_model == "adaptive":
            P = update_preferences(P, cfg.update_rule, cfg.eta, emb, acc, X[trace.slates[t]].mean(axis=1),
                                   cfg.bounded_threshold)
        path.append(P.copy())
    out = np.stack(path)
    if not np.array_equal(out[-1], trace.final_prefs):
        raise RuntimeError("replayed preference path does not end at the engine's final preferences")
    return out


def fl(a) -> list:
    """Nested lists of Python floats (repr round-trips exactly through JSON)."""
    return np.asarray(a, dtype=np.float64).tolist()


def build_fixture() -> dict:
    base = SimConfig(seed=FIXTURE_SEED, n_tracks=40, dim=16, n_clusters=4, zipf_s=1.3065, n_users=5,
                     n_steps=20, slate_size=5, warmup_steps=5).validate()
    choice_u, keys, flags = random_inputs(base)
    ss = np.random.SeedSequence(base.seed)
    s_cat, s_lis, _, _ = ss.spawn(4)
    runs = []
    cat = lis = None
    for arm in FIXTURE_ARMS:
        cfg = replace(base, **arm).validate()
        tr = simulate(cfg, record=True)
        if cat is None:
            cat, lis = tr.catalogue, tr.listeners
        assert np.array_equal(tr.catalogue.embeddings, cat.embeddings)
        metrics, _, per_user = compute_metrics(tr)
        runs.append({
            "arm": arm,
            "slates": tr.slates.tolist(),
            "choices": tr.choices.tolist(),
            "final_prefs": fl(tr.final_prefs),
            "drift_rad": per_user["drift_rad"],
            "metrics": {k: float(v) for k, v in metrics.items()},
        })
    # The recorded catalogue must equal a fresh draw from the catalogue stream.
    fresh = generate_catalogue(base, np.random.default_rng(s_cat))
    assert np.array_equal(fresh.embeddings, cat.embeddings)
    return {
        "_comment": "EXPLORATORY fixture from the Python research engine (echo.simulate) for the browser-port test. "
                    "Generated by scripts/m5_exploratory_engine_traces.py; not a research result.",
        "seed": base.seed,
        "params": {k: getattr(base, k) for k in ("n_tracks", "dim", "n_clusters", "n_users", "n_steps", "slate_size",
                                                   "tau", "warmup_steps", "mmr_lambda", "explore_epsilon",
                                                   "bounded_threshold", "skip_utility")},
        "catalogue": {"embeddings": fl(cat.embeddings), "cluster": cat.cluster.tolist(),
                      "base_pop": fl(cat.base_pop)},
        "initial_prefs": fl(lis.initial),
        "choice_u": fl(choice_u),
        "keys": fl(keys),
        "flags": fl(flags),
        "runs": runs,
    }


def pca2(X: np.ndarray):
    """First two principal axes of the rows of X; each axis's largest loading is positive."""
    mu = X.mean(axis=0)
    _, _, vt = np.linalg.svd(X - mu, full_matrices=False)
    V = vt[:2].T.copy()
    for j in range(2):
        if V[np.argmax(np.abs(V[:, j])), j] < 0:
            V[:, j] = -V[:, j]
    return mu, V


def r4(a) -> list:
    return np.round(np.asarray(a, dtype=np.float64), 4).tolist()


def build_taste_map() -> dict:
    with open(EXP002_CONFIG) as f:
        base_cfg = json.load(f)["blocks"][0]["base"]
    base = SimConfig(seed=TASTE_MAP_SEED, preference_model="adaptive", eta=0.05, update_rule="consumed",
                     profile="estimated", n_clusters=base_cfg["n_clusters"],
                     cluster_weights=tuple(base_cfg["cluster_weights"]), zipf_s=base_cfg["zipf_s"]).validate()
    listeners = [0, 1, 2]
    policies = {}
    mu = V = None
    cat = None
    for policy in ("RAND", "POP", "SIM", "MMR", "EXPLORE"):
        tr = simulate(replace(base, policy=policy).validate(), record=True)
        if cat is None:
            cat = tr.catalogue
            mu, V = pca2(cat.embeddings)
        path = replay_preferences(tr)  # (T + 1, U, d)
        drift = np.stack([angle(tr.listeners.initial, path[t]) for t in range(path.shape[0])])  # (T + 1, U)
        policies[policy] = {
            "mean_drift_by_step": r4(drift.mean(axis=1)),
            "listeners": [{"listener": u, "path": r4((path[:, u, :] - mu) @ V), "drift_by_step": r4(drift[:, u])}
                          for u in listeners],
        }
    xy = (cat.embeddings - mu) @ V
    var = np.var(cat.embeddings - mu, axis=0).sum()
    expl = [float(np.var(xy[:, j]) / var) for j in range(2)]
    return {
        "schema": "echo.m5.taste_map.v1",
        "label": "exploratory illustration: one exploratory seed of the Python research engine; not a research result",
        "generator": "scripts/m5_exploratory_engine_traces.py",
        "seed": base.seed,
        "config": base.to_dict(),
        "projection": {
            "method": "first two principal components of the 1000 catalogue embeddings (centred); "
                      "preference vectors are projected on the same axes",
            "explained_variance_share": [round(e, 4) for e in expl],
        },
        "tracks": [[round(float(x), 4), round(float(y), 4), int(c)] for (x, y), c in zip(xy, cat.cluster)],
        "listeners": listeners,
        "policies": policies,
    }


def dump(obj) -> str:
    return json.dumps(obj, indent=None, separators=(",", ":"), sort_keys=True) + "\n"


def main(argv) -> int:
    outputs = {FIXTURE: dump(build_fixture()), TASTE_MAP: dump(build_taste_map())}
    bad = 0
    for path, text in outputs.items():
        if "--check" in argv:
            same = path.exists() and path.read_text() == text
            print(f"{'OK' if same else 'DIFFERS'} {path.relative_to(REPO)}")
            bad += not same
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
            print(f"wrote {path.relative_to(REPO)} ({len(text)} bytes)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
