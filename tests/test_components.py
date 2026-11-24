# SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
"""Choice, preference updates, policies and metric helpers: golden and property tests."""

import math

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from echo.catalogue import zipf_weights
from echo.choice import choice_probabilities, sample_choice
from echo.metrics import gini
from echo.policies import explore_slate, mmr_slate, pop_slate, rand_slate, sim_slate, top_k
from echo.preferences import update_one, update_preferences
from echo.vectors import normalise


# ---------- choice ----------

def test_choice_probabilities_hand_computed():
    p = choice_probabilities(np.array([[1.0, 0.0]]), tau=1.0, skip_utility=0.0)[0]
    z = math.e + 2
    assert p.tolist() == pytest.approx([math.e / z, 1 / z, 1 / z], abs=1e-15)


def test_choice_probabilities_extreme_temperature_is_stable():
    p = choice_probabilities(np.array([[1.0, -1.0]]), tau=1e-6, skip_utility=0.0)
    assert np.all(np.isfinite(p)) and p[0, 0] == pytest.approx(1.0)


def test_choice_probabilities_errors():
    with pytest.raises(ValueError):
        choice_probabilities(np.array([1.0, 0.0]), 1.0, 0.0)
    with pytest.raises(ValueError):
        choice_probabilities(np.array([[1.0]]), 0.0, 0.0)
    with pytest.raises(ValueError):
        choice_probabilities(np.array([[np.nan]]), 1.0, 0.0)


def test_sample_choice_inverse_cdf():
    probs = np.array([[0.2, 0.3, 0.5]] * 5)
    u = np.array([0.0, 0.19999, 0.2, 0.5, 0.99999])
    assert sample_choice(probs, u).tolist() == [0, 0, 1, 2, 2]


def test_sample_choice_rejects_bad_uniforms():
    with pytest.raises(ValueError):
        sample_choice(np.array([[0.5, 0.5]]), np.array([1.0]))
    with pytest.raises(ValueError):
        sample_choice(np.array([[0.5, 0.5]]), np.array([-0.1]))


# ---------- preference updates ----------

def test_update_one_hand_computed():
    p = update_one(np.array([1.0, 0.0]), np.array([0.0, 1.0]), 0.5)
    assert p.tolist() == pytest.approx([1 / math.sqrt(2), 1 / math.sqrt(2)], abs=1e-15)


def test_update_eta_zero_is_exact_identity():
    rng = np.random.default_rng(1)
    P = normalise(rng.standard_normal((20, 8)))
    X = normalise(rng.standard_normal((20, 8)))
    for rule in ("consumed", "exposure", "bounded"):
        out = update_preferences(P, rule, 0.0, X, np.ones(20, bool), X, 0.5)
        assert np.array_equal(out, P) and out is not P


def test_update_rules_masks():
    P = np.array([[1.0, 0.0], [1.0, 0.0], [1.0, 0.0]])
    X = np.array([[0.0, 1.0], [0.8, 0.6], [0.0, 1.0]])
    acc = np.array([True, True, False])
    smean = np.array([[0.0, 1.0]] * 3)
    c = update_preferences(P, "consumed", 0.5, X, acc, smean, 0.5)
    assert not np.array_equal(c[0], P[0]) and not np.array_equal(c[1], P[1]) and np.array_equal(c[2], P[2])
    b = update_preferences(P, "bounded", 0.5, X, acc, smean, 0.5)
    # cos(P0, X0) = 0 <= 0.5: no update; cos(P1, X1) = 0.8 > 0.5: update; skip: no update
    assert np.array_equal(b[0], P[0]) and not np.array_equal(b[1], P[1]) and np.array_equal(b[2], P[2])
    e = update_preferences(P, "exposure", 0.5, X, acc, smean, 0.5)
    assert all(not np.array_equal(e[i], P[i]) for i in range(3))


def test_update_does_not_mutate_and_rejects_bad_args():
    P = np.array([[1.0, 0.0]])
    keep = P.copy()
    update_preferences(P, "consumed", 0.3, np.array([[0.0, 1.0]]), np.array([True]), P, 0.5)
    assert np.array_equal(P, keep)
    with pytest.raises(ValueError):
        update_preferences(P, "nope", 0.1, P, np.array([True]), P, 0.5)
    with pytest.raises(ValueError):
        update_preferences(P, "consumed", 1.5, P, np.array([True]), P, 0.5)
    with pytest.raises(ValueError):
        # antipodal target with eta = 0.5 gives the zero vector: explicit error
        update_preferences(P, "consumed", 0.5, -P, np.array([True]), P, 0.5)


angles = st.floats(min_value=0.0, max_value=math.pi * 0.999)


@settings(max_examples=200, deadline=None)
@given(angles, st.floats(min_value=1e-3, max_value=1.0))
def test_update_moves_toward_target_and_keeps_unit_norm(phi, eta):
    p = np.array([1.0, 0.0, 0.0])
    x = np.array([math.cos(phi), math.sin(phi), 0.0])
    q = update_one(p, x, eta)
    assert abs(np.linalg.norm(q) - 1.0) <= 1e-12
    assert float(q @ x) >= float(p @ x) - 1e-12  # monotone: closer to the consumed item


# ---------- policies ----------

def test_top_k_ties_broken_by_lower_index():
    scores = np.array([[1.0, 2.0, 2.0, 0.0, 2.0]])
    ex = np.zeros((1, 5), bool)
    assert top_k(scores, ex, 2).tolist() == [[1, 2]]
    ex[0, 1] = True
    assert top_k(scores, ex, 2).tolist() == [[2, 4]]


def test_policies_respect_candidate_exclusion_and_pool_check():
    ex = np.array([[True, False, True, False, False]])
    assert set(rand_slate(np.array([[0.0, 0.5, 0.1, 0.9, 0.2]]), ex, 3)[0]) == {1, 3, 4}
    assert pop_slate(np.array([10.0, 1.0, 9.0, 3.0, 2.0]), ex, 2).tolist() == [[3, 4]]
    with pytest.raises(ValueError, match="candidate pool"):
        rand_slate(np.zeros((1, 5)), ex, 4)


def test_rand_slate_orders_by_key():
    keys = np.array([[0.9, 0.1, 0.5, 0.3]])
    assert rand_slate(keys, np.zeros((1, 4), bool), 3).tolist() == [[1, 3, 2]]


def test_sim_slate_hand_example():
    X = normalise(np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0], [-1.0, 0.0]]))
    prof = np.array([[1.0, 0.0]])
    assert sim_slate(prof, X, np.zeros((1, 4), bool), 3).tolist() == [[0, 2, 1]]


def test_mmr_hand_example():
    # Items 0 and 1 are near duplicates close to the profile; item 2 is orthogonal-ish.
    # Hand values: rel = (0.9, 0.85, 0.8); cos(x1, x0) = 0.995, cos(x2, x0) = 0.72.
    # Second MMR pick: x1 scores 0.5*0.85 - 0.5*0.995 = -0.07, x2 scores 0.5*0.8 - 0.5*0.72 = 0.04.
    X = normalise(np.array([[0.9, 0.43589, 0.0], [0.85, 0.52678, 0.0], [0.8, 0.0, 0.6]]))
    prof = np.array([[1.0, 0.0, 0.0]])
    ex = np.zeros((1, 3), bool)
    # SIM picks 0 then 1; MMR with lambda 0.5 picks 0 then 2 (the redundancy penalty dominates).
    assert sim_slate(prof, X, ex, 2).tolist() == [[0, 1]]
    assert mmr_slate(prof, X, ex, 2, 0.5).tolist() == [[0, 2]]
    # lambda = 1 reduces MMR to SIM.
    assert mmr_slate(prof, X, ex, 3, 1.0).tolist() == sim_slate(prof, X, ex, 3).tolist()
    with pytest.raises(ValueError):
        mmr_slate(prof, X, ex, 2, 0.0)


def test_explore_limits_equal_sim_and_rand():
    rng = np.random.default_rng(3)
    X = normalise(rng.standard_normal((40, 4)))
    prof = normalise(rng.standard_normal((5, 4)))
    ex = rng.random((5, 40)) < 0.3
    keys = rng.random((5, 40))
    flags = rng.random((5, 6))
    assert np.array_equal(explore_slate(prof, X, ex, 6, keys, flags, 0.0), sim_slate(prof, X, ex, 6))
    assert np.array_equal(explore_slate(prof, X, ex, 6, keys, flags, 1.0), rand_slate(keys, ex, 6))
    mixed = explore_slate(prof, X, ex, 6, keys, flags, 0.5)
    for u in range(5):
        assert len(set(mixed[u].tolist())) == 6 and not ex[u, mixed[u]].any()


def test_explore_small_pool_fills_without_duplicates():
    X = normalise(np.eye(4))
    ex = np.array([[False, False, False, True]])
    out = explore_slate(np.array([[1.0, 0, 0, 0]]), X, ex, 3, np.array([[0.3, 0.2, 0.1, 0.0]]), np.array([[0.9, 0.0, 0.0]]), 0.5)
    assert sorted(out[0].tolist()) == [0, 1, 2]


@settings(max_examples=100, deadline=None)
@given(st.integers(min_value=0, max_value=10_000), st.integers(min_value=2, max_value=6))
def test_all_policies_exclusion_property(seed, k):
    rng = np.random.default_rng(seed)
    N, U = 20, 4
    X = normalise(rng.standard_normal((N, 3)))
    prof = normalise(rng.standard_normal((U, 3)))
    ex = rng.random((U, N)) < 0.5
    ex[:, :k] = False  # guarantee a pool of at least k
    keys = rng.random((U, N))
    flags = rng.random((U, k))
    for s in (rand_slate(keys, ex, k), pop_slate(rng.random(N), ex, k), sim_slate(prof, X, ex, k),
              mmr_slate(prof, X, ex, k, 0.5), explore_slate(prof, X, ex, k, keys, flags, 0.3)):
        for u in range(U):
            assert len(set(s[u].tolist())) == k
            assert not ex[u, s[u]].any()


# ---------- metric helpers ----------

def test_gini_hand_computed():
    assert gini([1, 1, 1, 1]) == pytest.approx(0.0, abs=1e-15)
    assert gini([0, 0, 0, 4]) == pytest.approx(0.75, abs=1e-15)
    assert gini([1, 2, 3]) == pytest.approx(2 / 9, abs=1e-15)  # sum|diff| = 8, 2 n^2 mean = 36


def test_gini_errors():
    for bad in ([], [0, 0], [-1, 2], [np.nan, 1]):
        with pytest.raises(ValueError):
            gini(bad)


@settings(max_examples=200, deadline=None)
@given(st.lists(st.integers(min_value=0, max_value=1000), min_size=1, max_size=40).filter(lambda v: sum(v) > 0))
def test_gini_matches_pairwise_definition(v):
    x = np.array(v, dtype=float)
    ref = np.abs(x[:, None] - x[None, :]).sum() / (2 * len(x) ** 2 * x.mean())
    g = gini(x)
    assert g == pytest.approx(ref, abs=1e-12)
    assert 0.0 <= g <= 1.0


def test_zipf_weights():
    w = zipf_weights(4, 1.0, np.array([1, 2, 3, 4]))
    assert w.sum() == pytest.approx(4.0)
    assert w[0] / w[1] == pytest.approx(2.0) and w[0] / w[3] == pytest.approx(4.0)
    assert np.allclose(zipf_weights(3, 0.0, np.array([3, 1, 2])), 1.0)
    with pytest.raises(ValueError):
        zipf_weights(3, 1.0, np.array([0, 1, 2]))
