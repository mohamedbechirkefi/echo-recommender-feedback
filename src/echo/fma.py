# SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
"""FMA metadata ingestion and calibration (protocol section 10.1).

FMA: A Dataset For Music Analysis (Defferrard et al., arXiv:1612.01840),
metadata licence CC BY 4.0. Only three tables are read: ``tracks.csv``
(columns set/split, track/genre_top, track/listens), ``genres.csv`` and
``features.csv`` (518 librosa statistics). Artist, title and other text
fields are never read into the processed data. Listening stays simulated.

Pure functions (no file access) do the work:

- ``parse_tracks``, ``parse_genres``, ``parse_features``: header and schema
  validation of rows already split by the csv module, with counts.
- ``fit_calibration``: K, cluster weights and the Zipf exponent from the
  calibration split (``training``).
- ``build_catalogue``: the second-test catalogue (``test`` split) embedded
  with a PCA basis fitted on the calibration split.

``read_csv_rows`` and ``save_catalogue`` / ``load_catalogue`` are the only
I/O. The processed catalogue is an ``.npz`` file loaded with
``allow_pickle=False`` and identified by its SHA-256.
"""

from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np

CALIBRATION_SPLIT = "training"
TEST_SPLIT = "test"
N_FEATURES = 518
TRACK_HEADER_ROWS = 3  # two header rows plus the "track_id" index row
FEATURE_HEADER_ROWS = 4  # feature, statistics, number, track_id
GENRE_COLUMNS = ("genre_id", "#tracks", "parent", "title", "top_level")
_TRACK_COLUMNS = {("set", "split"): "split", ("track", "genre_top"): "genre_top", ("track", "listens"): "listens"}


class IngestError(ValueError):
    """Raised when an FMA table does not match the expected schema."""


@dataclass(frozen=True)
class TrackRecord:
    track_id: int
    split: str
    genre_top: str | None  # None when missing
    listens: int


@dataclass(frozen=True)
class Genre:
    genre_id: int
    parent: int
    title: str
    top_level: int


@dataclass
class Counts:
    """Missingness and exclusion counts reported by the ingestion step."""

    values: dict[str, int] = field(default_factory=dict)

    def add(self, key: str, n: int = 1) -> None:
        self.values[key] = self.values.get(key, 0) + n


def read_csv_rows(path: Path) -> list[list[str]]:
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.reader(fh))


def parse_tracks(rows: Sequence[Sequence[str]], counts: Counts | None = None) -> list[TrackRecord]:
    """Parse tracks.csv rows (two-level header). Fails closed on schema errors."""
    counts = counts if counts is not None else Counts()
    if len(rows) < TRACK_HEADER_ROWS:
        raise IngestError("tracks table has fewer than three header rows")
    top, sub, idx = rows[0], rows[1], rows[2]
    if not idx or idx[0] != "track_id":
        raise IngestError(f"tracks table: third header row must start with 'track_id', got {idx[:1]}")
    where: dict[str, int] = {}
    for j, pair in enumerate(zip(top, sub)):
        if pair in _TRACK_COLUMNS:
            if _TRACK_COLUMNS[pair] in where:
                raise IngestError(f"tracks table: duplicate column {pair}")
            where[_TRACK_COLUMNS[pair]] = j
    missing = sorted(set(_TRACK_COLUMNS.values()) - set(where))
    if missing:
        raise IngestError(f"tracks table lacks columns {missing}")
    width = len(top)
    out: list[TrackRecord] = []
    seen: set[int] = set()
    for row in rows[TRACK_HEADER_ROWS:]:
        counts.add("tracks_rows")
        if len(row) != width:
            raise IngestError(f"tracks table: row of width {len(row)}, expected {width}")
        try:
            tid = int(row[0])
            listens = int(row[where["listens"]])
        except ValueError as exc:
            raise IngestError(f"tracks table: non-integer id or listens ({exc})") from exc
        if tid in seen:
            raise IngestError(f"tracks table: duplicate track_id {tid}")
        if listens < 0:
            raise IngestError(f"tracks table: negative listens for track {tid}")
        seen.add(tid)
        split = row[where["split"]].strip()
        if split not in ("training", "validation", "test"):
            raise IngestError(f"tracks table: unknown split {split!r} for track {tid}")
        genre = row[where["genre_top"]].strip() or None
        if genre is None:
            counts.add(f"genre_top_missing_{split}")
        out.append(TrackRecord(track_id=tid, split=split, genre_top=genre, listens=listens))
    return out


def parse_genres(rows: Sequence[Sequence[str]]) -> list[Genre]:
    if not rows or tuple(rows[0]) != GENRE_COLUMNS:
        raise IngestError(f"genres table header must be {GENRE_COLUMNS}")
    out = []
    for row in rows[1:]:
        if len(row) != len(GENRE_COLUMNS):
            raise IngestError("genres table: wrong row width")
        try:
            out.append(Genre(genre_id=int(row[0]), parent=int(row[2]), title=row[3], top_level=int(row[4])))
        except ValueError as exc:
            raise IngestError(f"genres table: bad integer ({exc})") from exc
    if len({g.genre_id for g in out}) != len(out):
        raise IngestError("genres table: duplicate genre_id")
    return out


def top_level_genres(genres: Sequence[Genre]) -> list[Genre]:
    """Top-level genres (top_level == genre_id), ordered by genre_id."""
    return sorted((g for g in genres if g.top_level == g.genre_id), key=lambda g: g.genre_id)


def parse_features(rows: Iterable[Sequence[str]], keep: set[int] | None = None,
                   counts: Counts | None = None) -> dict[int, np.ndarray]:
    """Parse features.csv rows (four header rows, then track_id + 518 values).

    Rows whose id is not in ``keep`` (if given) are skipped. Rows with a
    non-finite or unparsable value are excluded and counted.
    """
    counts = counts if counts is not None else Counts()
    it = iter(rows)
    header = [next(it, None) for _ in range(FEATURE_HEADER_ROWS)]
    if any(h is None for h in header) or header[0][0] != "feature" or header[3][0] != "track_id":
        raise IngestError("features table: unexpected header rows")
    if len(header[0]) != N_FEATURES + 1:
        raise IngestError(f"features table: {len(header[0]) - 1} feature columns, expected {N_FEATURES}")
    out: dict[int, np.ndarray] = {}
    for row in it:
        if len(row) != N_FEATURES + 1:
            raise IngestError(f"features table: row of width {len(row)}, expected {N_FEATURES + 1}")
        tid = int(row[0])
        if keep is not None and tid not in keep:
            continue
        try:
            v = np.array([float(x) for x in row[1:]], dtype=np.float64)
        except ValueError:
            counts.add("features_unparsable")
            continue
        if not np.all(np.isfinite(v)):
            counts.add("features_nonfinite")
            continue
        out[tid] = v
    return out


def fit_zipf_s(listens: Sequence[int]) -> tuple[float, int]:
    """OLS of ln(listens) on ln(rank), listens >= 1, ranks by descending listens.

    Returns (s, n_used) with s = minus the slope (protocol section 10.1).
    """
    a = np.asarray([x for x in listens if x >= 1], dtype=np.float64)
    if a.size < 2:
        raise IngestError("Zipf fit needs at least two tracks with listens >= 1")
    y = np.log(np.sort(a)[::-1])
    x = np.log(np.arange(1, a.size + 1, dtype=np.float64))
    xc = x - x.mean()
    slope = float(np.dot(xc, y - y.mean()) / np.dot(xc, xc))
    return -slope, int(a.size)


def fit_calibration(tracks: Sequence[TrackRecord], genres: Sequence[Genre]) -> dict:
    """K, cluster weights and Zipf s from the calibration split only."""
    tops = top_level_genres(genres)
    if not tops:
        raise IngestError("no top-level genres")
    titles = [g.title for g in tops]
    if len(set(titles)) != len(titles):
        raise IngestError("top-level genre titles are not unique")
    cal = [t for t in tracks if t.split == CALIBRATION_SPLIT]
    labelled = [t for t in cal if t.genre_top is not None]
    unknown = sorted({t.genre_top for t in labelled} - set(titles))
    if unknown:
        raise IngestError(f"genre_top values that are not top-level genres: {unknown}")
    n_lab = len(labelled)
    if n_lab == 0:
        raise IngestError("no labelled calibration tracks")
    tally = {title: 0 for title in titles}
    for t in labelled:
        tally[t.genre_top] += 1
    weights = [round(tally[title] / n_lab, 6) for title in titles]
    s, n_zipf = fit_zipf_s([t.listens for t in cal])
    if not (0.0 <= s <= 10.0):
        raise IngestError(f"fitted Zipf s = {s} outside [0, 10]; calibration stops (protocol 10.1)")
    return {
        "split": CALIBRATION_SPLIT,
        "n_clusters": len(tops),
        "genre_ids": [g.genre_id for g in tops],
        "genre_titles": titles,
        "genre_track_counts": [tally[title] for title in titles],
        "cluster_weights": weights,
        "zipf_s": round(s, 4),
        "zipf_s_unrounded": s,
        "n_calibration_tracks": len(cal),
        "n_calibration_labelled": n_lab,
        "n_zipf_tracks": n_zipf,
        "n_zipf_excluded_zero_listens": len(cal) - n_zipf,
    }


def _pca_basis(z: np.ndarray, dim: int) -> np.ndarray:
    """First ``dim`` right singular vectors of z (columns), sign-fixed."""
    _, _, vt = np.linalg.svd(z, full_matrices=False)
    basis = vt[:dim].T.copy()
    for j in range(dim):
        i = int(np.argmax(np.abs(basis[:, j])))
        if basis[i, j] < 0:
            basis[:, j] = -basis[:, j]
    return basis


def _normalise_rows(a: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(a, axis=1, keepdims=True)
    if np.any(n <= 1e-12):
        raise IngestError("zero vector cannot be normalised")
    return a / n


def build_catalogue(tracks: Sequence[TrackRecord], genres: Sequence[Genre],
                    features: dict[int, np.ndarray], dim: int = 16) -> tuple[dict[str, np.ndarray], dict[str, int]]:
    """Second-test catalogue (test split) embedded with a calibration-split PCA.

    Returns (arrays, counts). ``arrays`` holds track_id, genre (index into the
    top-level genre order), listens, embeddings (unit rows), centres (unit
    rows, one per genre), genre_ids, genre_titles and the PCA parameters.
    """
    counts = Counts()
    tops = top_level_genres(genres)
    titles = [g.title for g in tops]
    gindex = {title: i for i, title in enumerate(titles)}

    def eligible(split: str) -> list[TrackRecord]:
        out = []
        for t in tracks:
            if t.split != split:
                continue
            if t.genre_top is None:
                counts.add(f"excluded_{split}_genre_missing")
                continue
            if t.genre_top not in gindex:
                raise IngestError(f"unknown genre_top {t.genre_top!r}")
            if t.track_id not in features:
                counts.add(f"excluded_{split}_features_missing")
                continue
            out.append(t)
        counts.add(f"eligible_{split}", len(out))
        return out

    fit = eligible(CALIBRATION_SPLIT)
    test = eligible(TEST_SPLIT)
    if len(fit) <= dim or not test:
        raise IngestError("too few eligible tracks for the PCA or the catalogue")
    f_fit = np.stack([features[t.track_id] for t in fit])
    mean = f_fit.mean(axis=0)
    sd = f_fit.std(axis=0)
    sd = np.where(sd > 0, sd, 1.0)
    counts.add("features_zero_sd", int(np.sum(f_fit.std(axis=0) == 0)))
    basis = _pca_basis((f_fit - mean) / sd, dim)
    e_fit = _normalise_rows(((f_fit - mean) / sd) @ basis)
    g_fit = np.array([gindex[t.genre_top] for t in fit])
    centres = np.zeros((len(tops), dim))
    for g in range(len(tops)):
        sel = g_fit == g
        if not np.any(sel):
            raise IngestError(f"genre {titles[g]!r} has no calibration tracks")
        centres[g] = e_fit[sel].mean(axis=0)
    centres = _normalise_rows(centres)
    f_test = np.stack([features[t.track_id] for t in test])
    emb = _normalise_rows(((f_test - mean) / sd) @ basis)
    arrays = {
        "track_id": np.array([t.track_id for t in test], dtype=np.int64),
        "genre": np.array([gindex[t.genre_top] for t in test], dtype=np.int64),
        "listens": np.array([t.listens for t in test], dtype=np.int64),
        "embeddings": emb,
        "centres": centres,
        "genre_ids": np.array([g.genre_id for g in tops], dtype=np.int64),
        "genre_titles": np.array(titles, dtype=np.str_),
        "pca_mean": mean,
        "pca_sd": sd,
        "pca_basis": basis,
    }
    return arrays, dict(counts.values)


CATALOGUE_KEYS = ("track_id", "genre", "listens", "embeddings", "centres", "genre_ids", "genre_titles",
                  "pca_mean", "pca_sd", "pca_basis")


def save_catalogue(arrays: dict[str, np.ndarray], path: Path) -> str:
    """Write an uncompressed .npz (deterministic bytes) and return its SHA-256."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as fh:
        np.savez(fh, **{k: arrays[k] for k in CATALOGUE_KEYS})
    return sha256_file(path)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass(frozen=True)
class RealCatalogue:
    embeddings: np.ndarray  # (M, d) unit rows
    genre: np.ndarray  # (M,) int in [0, K)
    listens: np.ndarray  # (M,) int >= 0
    centres: np.ndarray  # (K, d) unit rows
    sha256: str


_CACHE: dict[tuple[str, str], RealCatalogue] = {}


def load_catalogue(path: Path, expected_sha256: str) -> RealCatalogue:
    """Load and validate the processed catalogue; fail closed on a hash mismatch."""
    path = Path(path)
    key = (str(path.resolve()), expected_sha256)
    if key in _CACHE:
        return _CACHE[key]
    if not path.exists():
        raise IngestError(f"processed FMA catalogue not found at {path}; run scripts/build_fma_catalogue.py")
    actual = sha256_file(path)
    if actual != expected_sha256:
        raise IngestError(f"processed FMA catalogue SHA-256 {actual} differs from the configured {expected_sha256}")
    with np.load(path, allow_pickle=False) as z:
        missing = [k for k in CATALOGUE_KEYS if k not in z.files]
        if missing:
            raise IngestError(f"processed catalogue lacks arrays {missing}")
        emb, genre, listens, centres = z["embeddings"], z["genre"], z["listens"], z["centres"]
    m, d = emb.shape
    k = centres.shape[0]
    if genre.shape != (m,) or listens.shape != (m,) or centres.shape[1] != d:
        raise IngestError("processed catalogue arrays have inconsistent shapes")
    if np.any(genre < 0) or np.any(genre >= k) or np.any(listens < 0):
        raise IngestError("processed catalogue holds out-of-range genre or listens values")
    for a in (emb, centres):
        if not np.all(np.isfinite(a)) or np.max(np.abs(np.linalg.norm(a, axis=1) - 1.0)) > 1e-9:
            raise IngestError("processed catalogue rows are not unit vectors")
    cat = RealCatalogue(embeddings=emb, genre=genre, listens=listens, centres=centres, sha256=actual)
    _CACHE[key] = cat
    return cat

