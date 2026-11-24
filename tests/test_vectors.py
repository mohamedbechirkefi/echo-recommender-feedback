# SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
"""Cosine similarity and normalisation edge cases (master prompt section 10)."""

import math

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.extra.numpy import arrays

from echo.vectors import angle, angle_arccos, cosine, mean_pairwise_cosine, normalise

finite = st.floats(min_value=-1e3, max_value=1e3, allow_nan=False, allow_infinity=False)
vec = arrays(np.float64, 8, elements=finite).filter(lambda v: np.linalg.norm(v) > 1e-3)


def test_cosine_parallel_antiparallel_orthogonal():
    assert cosine([1, 0], [2, 0]) == 1.0
    assert cosine([1, 0], [-3, 0]) == -1.0
    assert cosine([1, 0], [0, 5]) == 0.0


def test_cosine_hand_computed():
    # [1,2,2] . [2,1,2] = 8 ; norms 3 and 3
    assert cosine([1, 2, 2], [2, 1, 2]) == pytest.approx(8 / 9, abs=1e-15)


def test_cosine_clipped_to_unit_interval():
    v = np.array([0.1, 0.2, 0.3]) * 1e8
    assert -1.0 <= cosine(v, v) <= 1.0
    assert cosine(v, v) == pytest.approx(1.0, abs=1e-15)


@pytest.mark.parametrize("a,b", [([0, 0], [1, 0]), ([1, 0], [0, 0]), ([0, 0], [0, 0]), ([1e-13, 0], [1, 0])])
def test_cosine_zero_vector_raises(a, b):
    with pytest.raises(ValueError, match="zero-norm"):
        cosine(a, b)


@pytest.mark.parametrize("a,b", [([np.nan, 1], [1, 0]), ([np.inf, 1], [1, 0])])
def test_cosine_non_finite_raises(a, b):
    with pytest.raises(ValueError, match="non-finite"):
        cosine(a, b)


def test_cosine_shape_mismatch_raises():
    with pytest.raises(ValueError):
        cosine([1, 0], [1, 0, 0])
    with pytest.raises(ValueError):
        cosine([[1, 0]], [[1, 0]])


def test_normalise_unit_and_errors():
    assert np.allclose(normalise([3.0, 4.0]), [0.6, 0.8], atol=0, rtol=1e-15)
    with pytest.raises(ValueError):
        normalise([0.0, 0.0])
    with pytest.raises(ValueError):
        normalise([[1.0, 0.0], [0.0, 0.0]])
    with pytest.raises(ValueError):
        normalise([np.nan, 1.0])
    with pytest.raises(ValueError):
        normalise(np.float64(1.0))


def test_normalise_does_not_mutate_input():
    a = np.array([[3.0, 4.0]])
    normalise(a)
    assert a.tolist() == [[3.0, 4.0]]


def test_angle_identical_is_exactly_zero():
    rng = np.random.default_rng(0)
    p = normalise(rng.standard_normal((50, 16)))
    assert np.all(angle(p, p.copy()) == 0.0)


def test_angle_hand_computed():
    assert angle(np.array([[1.0, 0.0]]), np.array([[0.0, 1.0]]))[0] == pytest.approx(math.pi / 2, abs=1e-15)
    assert angle(np.array([[1.0, 0.0]]), np.array([[-1.0, 0.0]]))[0] == pytest.approx(math.pi, abs=1e-15)
    assert angle(np.array([[1.0, 0.0]]), np.array([[1.0, 1.0]]))[0] == pytest.approx(math.pi / 4, abs=1e-15)


def test_mean_pairwise_cosine_hand_computed():
    rows = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 0.0]])
    # ordered pairs: (0,1)=0 (0,2)=1 (1,2)=0, each twice -> 2/6
    assert mean_pairwise_cosine(rows) == pytest.approx(1 / 3, abs=1e-15)
    with pytest.raises(ValueError):
        mean_pairwise_cosine(np.array([[1.0, 0.0]]))


@settings(max_examples=200, deadline=None)
@given(vec, vec, st.floats(min_value=1e-3, max_value=1e3), st.floats(min_value=1e-3, max_value=1e3))
def test_cosine_properties(a, b, s1, s2):
    c = cosine(a, b)
    assert -1.0 <= c <= 1.0
    assert c == pytest.approx(cosine(b, a), abs=1e-12)
    assert c == pytest.approx(cosine(s1 * a, s2 * b), abs=1e-9)
    assert cosine(a, -b) == pytest.approx(-c, abs=1e-12)


@settings(max_examples=200, deadline=None)
@given(vec)
def test_normalise_gives_unit_norm(a):
    assert abs(np.linalg.norm(normalise(a)) - 1.0) <= 1e-12


@settings(max_examples=200, deadline=None)
@given(vec, vec)
def test_angle_matches_protocol_arccos_formula(a, b):
    # Differential: the stable chord form against the protocol's arccos form.
    th = angle(a[None, :], b[None, :])[0]
    ref = angle_arccos(a[None, :], b[None, :])[0]
    assert 0.0 <= th <= math.pi
    assert th == pytest.approx(ref, abs=2e-7)
