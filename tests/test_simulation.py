# SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
"""Simulation: determinism, negative control, exclusion, CRN, differential reference."""

import math
import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from echo.config import POLICIES, ConfigError, SimConfig
from echo.metrics import METRIC_NAMES, check_bounds, compute_metrics
from echo.simulate import simulate
from echo.smoke import exclusion_violations_from_log
from reference_sim import reference_simulate

SMALL = dict(n_tracks=60, n_users=8, n_steps=15, slate_size=5, dim=6, n_clusters=4, warmup_steps=3)


def small(**kw):
    return SimConfig(seed=kw.pop("seed", 900500), **{**SMALL, **kw})


# ---------- configuration ----------

@pytest.mark.parametrize("bad", [
    dict(policy="XYZ"), dict(preference_model="fixed", eta=0.05), dict(preference_model="adaptive", eta=0.0),
    dict(n_steps=56), dict(tau=0.0), dict(eta=1.5), dict(slate_size=1), dict(n_users=1),
    dict(mmr_lambda=0.0), dict(update_rule="none"), dict(profile="psychic"), dict(seed=-1),
    dict(tau=float("nan")), dict(n_tracks=True),
])
def test_invalid_configs_raise(bad):
    with pytest.raises(ConfigError):
        small(**bad).validate()


def test_from_dict_rejects_unknown_and_missing_seed():
    with pytest.raises(ConfigError, match="unknown"):
        SimConfig.from_dict({"seed": 1, "colour": "red"})
    with pytest.raises(ConfigError, match="seed"):
        SimConfig.from_dict({"policy": "RAND"})


def test_config_hash_is_stable_and_int_float_insensitive():
    a = SimConfig.from_dict({"seed": 1, "tau": 1})
    b = SimConfig.from_dict({"seed": 1, "tau": 1.0})
    assert a.hash() == b.hash() and len(a.hash()) == 64
    assert a.hash() != SimConfig.from_dict({"seed": 2, "tau": 1.0}).hash()


# ---------- determinism and negative control ----------

@pytest.mark.parametrize("policy", POLICIES)
def test_deterministic_updates(policy):
    a = simulate(small(policy=policy), record=True)
    b = simulate(small(policy=policy), record=True)
    assert np.array_equal(a.final_prefs, b.final_prefs)
    assert np.array_equal(a.slates, b.slates) and np.array_equal(a.choices, b.choices)
    assert compute_metrics(a) == compute_metrics(b)


@pytest.mark.parametrize("policy", POLICIES)
@pytest.mark.parametrize("rule", ["consumed", "exposure", "bounded"])
def test_fixed_preferences_give_exactly_zero_drift(policy, rule):
    tr = simulate(small(policy=policy, preference_model="fixed", eta=0.0, update_rule=rule))
    m, d, pu = compute_metrics(tr)
    assert all(v == 0.0 for v in pu["drift_rad"])
    assert m["drift_rad"] == 0.0 and m["homogenisation"] == 0.0
    assert np.array_equal(tr.final_prefs, tr.listeners.initial)


@pytest.mark.parametrize("policy", POLICIES)
def test_candidate_exclusion_from_log(policy):
    tr = simulate(small(policy=policy, n_steps=55, tau=0.01), record=True)
    assert tr.exclusion_violations == 0
    assert exclusion_violations_from_log(tr.slates, tr.choices, tr.config.n_tracks) == 0


def test_exclusion_log_checker_detects_a_violation():
    slates = np.array([[[0, 1]], [[0, 2]]])  # track 0 consumed at t=0, shown again at t=1
    choices = np.array([[0], [-1]])
    assert exclusion_violations_from_log(slates, choices, 3) == 1


def test_pool_exhaustion_boundary():
    # n_steps == n_tracks - slate_size is the largest valid design.
    cfg = small(n_tracks=20, n_steps=15, slate_size=5, tau=0.001, skip_utility=-100.0)
    tr = simulate(cfg, record=True)
    assert tr.accepted.max() <= 15 and tr.exclusion_violations == 0


def test_common_random_numbers_across_arms():
    a = simulate(small(policy="RAND"))
    b = simulate(small(policy="SIM", eta=0.2, update_rule="exposure"))
    assert np.array_equal(a.catalogue.embeddings, b.catalogue.embeddings)
    assert np.array_equal(a.listeners.initial, b.listeners.initial)
    c = simulate(small(policy="RAND", seed=900501))
    assert not np.array_equal(a.catalogue.embeddings, c.catalogue.embeddings)


def test_unit_norms_and_metric_bounds():
    for policy in POLICIES:
        tr = simulate(small(policy=policy, eta=0.3))
        for arr in (tr.catalogue.embeddings, tr.listeners.initial, tr.final_prefs):
            assert np.max(np.abs(np.linalg.norm(arr, axis=1) - 1.0)) <= 1e-12
        m, d, _ = compute_metrics(tr)
        assert set(m) == set(METRIC_NAMES)
        assert check_bounds(m, d) == []


def test_extreme_parameters_all_skip():
    # Skip utility far above any cosine: nobody accepts, nobody drifts.
    tr = simulate(small(policy="SIM", skip_utility=50.0))
    m, d, pu = compute_metrics(tr)
    assert d["users_without_accept"] == tr.config.n_users and m["skip_rate"] == 1.0
    assert m["drift_rad"] == 0.0 and math.isnan(m["novelty_bits"])
    assert check_bounds(m, d)  # non-finite metric is flagged, run would be recorded as failed


def test_oracle_profile_runs_and_differs():
    a = simulate(small(policy="SIM", profile="oracle"), record=True)
    b = simulate(small(policy="SIM", profile="estimated"), record=True)
    assert not np.array_equal(a.slates, b.slates)


# ---------- hand-computed micro example ----------

def test_single_step_matches_hand_computation():
    cfg = SimConfig(seed=900700, n_tracks=12, n_users=2, n_steps=1, slate_size=3, dim=3, n_clusters=2,
                    policy="RAND", eta=0.5, warmup_steps=0)
    tr = simulate(cfg, record=True)
    X, p0 = tr.catalogue.embeddings, tr.listeners.initial
    for u in range(2):
        c = tr.choices[0, u]
        if c < 0:
            assert np.array_equal(tr.final_prefs[u], p0[u])
        else:
            v = 0.5 * p0[u] + 0.5 * X[c]
            assert np.allclose(tr.final_prefs[u], v / np.linalg.norm(v), atol=1e-15)
            expected_angle = math.acos(max(-1.0, min(1.0, float(p0[u] @ (v / np.linalg.norm(v))))))
            assert compute_metrics(tr)[2]["drift_rad"][u] == pytest.approx(expected_angle, abs=1e-7)


# ---------- differential test against the loop reference ----------

@pytest.mark.parametrize("policy", POLICIES)
@pytest.mark.parametrize("pref", [("fixed", 0.0), ("adaptive", 0.1)])
def test_matches_loop_reference(policy, pref):
    cfg = small(policy=policy, preference_model=pref[0], eta=pref[1])
    fast = simulate(cfg, record=True)
    ref = reference_simulate(cfg)
    assert fast.slates.tolist() == ref["slates"]
    assert fast.accepted.tolist() == ref["accepted"]
    pu = compute_metrics(fast)[2]["drift_rad"]
    assert pu == pytest.approx(ref["drift"], abs=1e-12)


@settings(max_examples=15, deadline=None)
@given(st.integers(min_value=0, max_value=2**31), st.sampled_from(POLICIES))
def test_matches_loop_reference_random_seeds(seed, policy):
    cfg = small(seed=seed, policy=policy, n_steps=8, eta=0.2)
    fast = simulate(cfg, record=True)
    ref = reference_simulate(cfg)
    assert fast.slates.tolist() == ref["slates"]
    assert fast.accepted.tolist() == ref["accepted"]


@settings(max_examples=25, deadline=None)
@given(st.integers(min_value=0, max_value=2**31), st.sampled_from(POLICIES),
       st.sampled_from(["consumed", "exposure", "bounded"]), st.floats(min_value=0.001, max_value=1.0))
def test_invariants_random_configs(seed, policy, rule, eta):
    tr = simulate(small(seed=seed, policy=policy, update_rule=rule, eta=eta), record=True)
    m, d, pu = compute_metrics(tr)
    assert d["exclusion_violations"] == 0
    assert tr.max_pref_norm_error <= 1e-12
    assert all(a + s == tr.config.n_steps for a, s in zip(pu["accepted"], pu["skips"]))
    if d["users_without_accept"] < tr.config.n_users:
        assert check_bounds(m, d) == []
