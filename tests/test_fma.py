# SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
"""FMA ingestion, calibration and real-catalogue simulation on a SYNTHETIC fixture.

The fixture (tests/fixtures/fma_synthetic/, written by make_fma_fixture.py)
has the FMA schema but no real FMA rows.
"""

from __future__ import annotations

import math
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pytest

from echo import catalogue as catmod
from echo.config import ConfigError, SimConfig, config_hash
from echo.fma import (
    Counts, IngestError, build_catalogue, fit_calibration, fit_zipf_s, load_catalogue, parse_features,
    parse_genres, parse_tracks, read_csv_rows, save_catalogue, top_level_genres,
)
from echo.metrics import compute_metrics
from echo.simulate import simulate

FIX = Path(__file__).resolve().parent / "fixtures" / "fma_synthetic"


@pytest.fixture(scope="module")
def tables():
    counts = Counts()
    tracks = parse_tracks(read_csv_rows(FIX / "tracks.csv"), counts)
    genres = parse_genres(read_csv_rows(FIX / "genres.csv"))
    features = parse_features(read_csv_rows(FIX / "features.csv"), counts=counts)
    return tracks, genres, features, counts


# ---------- schema validation and counts ----------

def test_parse_tracks_counts(tables):
    tracks, _, _, counts = tables
    assert len(tracks) == 48
    assert counts.values["tracks_rows"] == 48
    missing = sum(1 for t in tracks if t.genre_top is None)
    assert missing == sum(v for k, v in counts.values.items() if k.startswith("genre_top_missing_"))
    assert {t.split for t in tracks} == {"training", "validation", "test"}


def _tracks_rows():
    return [list(r) for r in read_csv_rows(FIX / "tracks.csv")]


@pytest.mark.parametrize("mutate, msg", [
    (lambda r: r[0].__setitem__(4, "x"), "lacks columns"),
    (lambda r: r[2].__setitem__(0, "id"), "track_id"),
    (lambda r: r[4].__setitem__(0, r[3][0]), "duplicate track_id"),
    (lambda r: r[3].__setitem__(2, "holdout"), "unknown split"),
    (lambda r: r[3].__setitem__(5, "-1"), "negative listens"),
    (lambda r: r[3].__setitem__(5, "many"), "non-integer"),
    (lambda r: r[3].append("extra"), "width"),
])
def test_parse_tracks_fails_closed(mutate, msg):
    rows = _tracks_rows()
    mutate(rows)
    with pytest.raises(IngestError, match=msg):
        parse_tracks(rows)


def test_parse_genres_and_top_level(tables):
    _, genres, _, _ = tables
    tops = top_level_genres(genres)
    assert [g.genre_id for g in tops] == [2, 5, 9]
    with pytest.raises(IngestError, match="header"):
        parse_genres([["id", "title"]])
    with pytest.raises(IngestError, match="duplicate"):
        parse_genres([list(read_csv_rows(FIX / "genres.csv")[0]), ["1", "0", "0", "A", "1"], ["1", "0", "0", "B", "1"]])


def test_parse_features_exclusions(tables):
    _, _, features, counts = tables
    assert counts.values["features_nonfinite"] == 1
    assert len(features) == 46  # 48 tracks, one row absent, one non-finite
    assert all(v.shape == (518,) and np.all(np.isfinite(v)) for v in features.values())
    rows = read_csv_rows(FIX / "features.csv")
    kept = parse_features(rows, keep={100, 103})
    assert set(kept) == {100, 103}
    bad = [list(r) for r in rows]
    bad[5] = bad[5][:-1]
    with pytest.raises(IngestError, match="width"):
        parse_features(bad)
    with pytest.raises(IngestError, match="header"):
        parse_features(rows[1:])


# ---------- calibration ----------

def test_zipf_fit_recovers_exponent_and_drops_zeros():
    listens = [int(round(1e9 * r ** -1.3)) for r in range(1, 2001)] + [0, 0, 0]
    s, n = fit_zipf_s(listens[::-1])  # order must not matter
    assert n == 2000
    assert abs(s - 1.3) < 1e-3


def test_zipf_fit_hand_computed():
    # ranks 1, 2, 3 with listens 6, 3, 2: ln y = ln 6 - 1 * ln r exactly, so s = 1.
    s, n = fit_zipf_s([2, 6, 3])
    assert n == 3 and math.isclose(s, 1.0, abs_tol=1e-12)
    with pytest.raises(IngestError):
        fit_zipf_s([5, 0])


def test_calibration_uses_training_split_only(tables):
    tracks, genres, _, _ = tables
    cal = fit_calibration(tracks, genres)
    assert cal["n_clusters"] == 3 and cal["genre_titles"] == ["GenreA", "GenreB", "GenreC"]
    train = [t for t in tracks if t.split == "training"]
    lab = [t for t in train if t.genre_top]
    assert cal["n_calibration_tracks"] == len(train)
    assert cal["genre_track_counts"] == [sum(t.genre_top == g for t in lab) for g in cal["genre_titles"]]
    assert abs(sum(cal["cluster_weights"]) - 1.0) < 1e-5
    s_train, _ = fit_zipf_s([t.listens for t in train])
    assert cal["zipf_s"] == round(s_train, 4)
    # Changing a test-split track never changes the calibration.
    altered = [t if t.split != "test" else type(t)(t.track_id, t.split, t.genre_top, t.listens * 7 + 1) for t in tracks]
    assert fit_calibration(altered, genres) == cal


def test_calibration_rejects_unknown_genre(tables):
    tracks, genres, _, _ = tables
    bad = [type(t)(t.track_id, t.split, "Unknown" if t.genre_top else None, t.listens) for t in tracks]
    with pytest.raises(IngestError, match="not top-level"):
        fit_calibration(bad, genres)


# ---------- catalogue ----------

@pytest.fixture(scope="module")
def built(tables):
    tracks, genres, features, _ = tables
    return build_catalogue(tracks, genres, features, dim=4)


def test_build_catalogue_contents(tables, built):
    tracks, _, features, _ = tables
    arrays, counts = built
    test_ok = [t for t in tracks if t.split == "test" and t.genre_top and t.track_id in features]
    assert arrays["track_id"].tolist() == [t.track_id for t in test_ok]
    assert counts["eligible_test"] == len(test_ok) == 11
    assert counts["excluded_test_genre_missing"] == 2
    assert counts["excluded_test_features_missing"] == 1
    assert arrays["embeddings"].shape == (11, 4) and arrays["centres"].shape == (3, 4)
    for key in ("embeddings", "centres"):
        assert np.allclose(np.linalg.norm(arrays[key], axis=1), 1.0, atol=1e-12)
    basis = arrays["pca_basis"]
    assert np.allclose(basis.T @ basis, np.eye(4), atol=1e-10)
    for j in range(4):  # sign convention
        assert basis[np.argmax(np.abs(basis[:, j])), j] > 0


def test_build_catalogue_is_deterministic_and_ignores_test_for_fit(tables, built):
    tracks, genres, features, _ = tables
    again, _ = build_catalogue(tracks, genres, features, dim=4)
    for k, v in built[0].items():
        assert np.array_equal(v, again[k])
    # Perturbing a test-split feature row leaves the PCA basis unchanged.
    tid = int(built[0]["track_id"][0])
    feats2 = dict(features)
    feats2[tid] = features[tid] + 5.0
    other, _ = build_catalogue(tracks, genres, feats2, dim=4)
    assert np.array_equal(other["pca_basis"], built[0]["pca_basis"])
    assert np.array_equal(other["centres"], built[0]["centres"])


def test_save_load_roundtrip_and_hash_guard(tmp_path, built):
    p = tmp_path / "cat.npz"
    sha = save_catalogue(built[0], p)
    assert save_catalogue(built[0], tmp_path / "cat2.npz") == sha  # deterministic bytes
    real = load_catalogue(p, sha)
    assert np.array_equal(real.embeddings, built[0]["embeddings"])
    with pytest.raises(IngestError, match="differs"):
        load_catalogue(tmp_path / "cat2.npz", "0" * 64)
    with pytest.raises(IngestError, match="not found"):
        load_catalogue(tmp_path / "none.npz", sha)


# ---------- configuration ----------

def test_new_fields_do_not_change_old_hashes():
    cfg = SimConfig(seed=900000)
    old = {k: v for k, v in asdict(cfg).items() if k not in ("catalogue", "cluster_weights", "fma_catalogue_sha256")}
    assert cfg.hash() == config_hash(old)
    assert SimConfig.from_dict(old) == cfg


def test_config_validation_real_data_fields():
    with pytest.raises(ConfigError, match="fma_catalogue_sha256"):
        SimConfig(seed=1, catalogue="fma").validate()
    with pytest.raises(ConfigError, match="catalogue 'fma' only"):
        SimConfig(seed=1, fma_catalogue_sha256="a" * 64).validate()
    with pytest.raises(ConfigError, match="entries"):
        SimConfig(seed=1, n_clusters=3, cluster_weights=(0.5, 0.5)).validate()
    with pytest.raises(ConfigError, match="sum to 1"):
        SimConfig(seed=1, n_clusters=2, cluster_weights=(0.5, 0.6)).validate()
    with pytest.raises(ConfigError, match="catalogue must be"):
        SimConfig(seed=1, catalogue="lastfm").validate()
    cfg = SimConfig.from_dict({"seed": 1, "n_clusters": 2, "cluster_weights": [1, 0]})
    assert cfg.cluster_weights == (1.0, 0.0)
    assert SimConfig.from_dict(cfg.to_dict()) == cfg


def test_weighted_clusters_follow_weights():
    cfg = SimConfig(seed=900990, n_tracks=4000, n_steps=10, n_clusters=3, cluster_weights=(0.7, 0.3, 0.0))
    cat = catmod.generate_catalogue(cfg.validate(), np.random.default_rng(1))
    share = np.bincount(cat.cluster, minlength=3) / 4000
    assert share[2] == 0.0 and abs(share[0] - 0.7) < 0.03


# ---------- simulation on the real-catalogue path (fixture) ----------

@pytest.fixture()
def fma_cfg(tmp_path, built, monkeypatch):
    p = tmp_path / "fma_catalogue_v1.npz"
    sha = save_catalogue(built[0], p)
    monkeypatch.setattr(catmod, "FMA_CATALOGUE_PATH", p)
    return dict(seed=900980, catalogue="fma", fma_catalogue_sha256=sha, n_tracks=10, n_users=5, n_steps=5,
                slate_size=3, dim=4, n_clusters=3, warmup_steps=1)


def test_fma_simulation_runs_and_samples_real_rows(fma_cfg, built):
    emb = built[0]["embeddings"]
    for policy in ("RAND", "POP", "SIM", "MMR", "EXPLORE"):
        tr = simulate(SimConfig(**{**fma_cfg, "policy": policy}).validate(), record=True)
        rows = {tuple(r) for r in emb}
        assert all(tuple(r) in rows for r in tr.catalogue.embeddings)
        assert len({tuple(r) for r in tr.catalogue.embeddings}) == 10  # without replacement
        assert np.isclose(tr.catalogue.base_pop.sum(), 10)
        assert tr.exclusion_violations == 0
        metrics, _, _ = compute_metrics(tr)
        assert all(np.isfinite(v) for v in metrics.values())


def test_fma_fixed_preferences_zero_drift_and_determinism(fma_cfg):
    cfg = SimConfig(**{**fma_cfg, "policy": "SIM", "preference_model": "fixed", "eta": 0.0}).validate()
    a, b = simulate(cfg), simulate(cfg)
    assert np.array_equal(a.final_prefs, a.listeners.initial)
    assert np.array_equal(a.catalogue.embeddings, b.catalogue.embeddings)
    # Common random numbers: the catalogue sample depends on the seed only.
    c = simulate(SimConfig(**{**fma_cfg, "policy": "RAND"}).validate())
    assert np.array_equal(a.catalogue.embeddings, c.catalogue.embeddings)


def test_fma_simulation_fails_closed(fma_cfg):
    with pytest.raises(catmod.CatalogueError, match="dim"):
        simulate(SimConfig(**{**fma_cfg, "dim": 5}).validate())
    with pytest.raises(catmod.CatalogueError, match="n_clusters"):
        simulate(SimConfig(**{**fma_cfg, "n_clusters": 4}).validate())
    with pytest.raises(catmod.CatalogueError, match="exceeds"):
        simulate(SimConfig(**{**fma_cfg, "n_tracks": 13, "n_steps": 2}).validate())
    with pytest.raises(IngestError, match="differs"):
        simulate(SimConfig(**{**fma_cfg, "fma_catalogue_sha256": "b" * 64}).validate())
