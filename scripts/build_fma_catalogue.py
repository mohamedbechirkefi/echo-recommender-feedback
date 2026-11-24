# SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
"""Build the FMA calibration values and the EXP-004 real catalogue.

Reads data/raw/fma_metadata.zip (see scripts/download_fma_metadata.py) without
extracting it, runs the pure ingestion functions of src/echo/fma.py and writes:

- data/fma_calibration_v1.json  (committed: aggregate values and counts only)
- data/processed/fma_catalogue_v1.npz  (git-ignored; SHA-256 in the JSON)

Protocol section 10.1 fixes the methods. No simulation is run here.

Usage (from the repository root):
    PYTHONPATH=src .venv/bin/python scripts/build_fma_catalogue.py
"""

from __future__ import annotations

import csv
import io
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from echo.fma import (  # noqa: E402
    Counts, build_catalogue, fit_calibration, parse_features, parse_genres, parse_tracks, save_catalogue, sha256_file,
)

ZIP = ROOT / "data" / "raw" / "fma_metadata.zip"
OUT_NPZ = ROOT / "data" / "processed" / "fma_catalogue_v1.npz"
OUT_JSON = ROOT / "data" / "fma_calibration_v1.json"
DIM = 16


def rows(zf: zipfile.ZipFile, member: str):
    with zf.open(member) as raw:
        yield from csv.reader(io.TextIOWrapper(raw, encoding="utf-8", newline=""))


def main() -> int:
    counts = Counts()
    with zipfile.ZipFile(ZIP) as zf:
        names = {Path(n).name: n for n in zf.namelist()}
        tracks = parse_tracks(list(rows(zf, names["tracks.csv"])), counts)
        genres = parse_genres(list(rows(zf, names["genres.csv"])))
        keep = {t.track_id for t in tracks if t.split in ("training", "test") and t.genre_top is not None}
        features = parse_features(rows(zf, names["features.csv"]), keep=keep, counts=counts)
    calibration = fit_calibration(tracks, genres)
    arrays, cat_counts = build_catalogue(tracks, genres, features, dim=DIM)
    sha = save_catalogue(arrays, OUT_NPZ)
    record = {
        "source": "Derived aggregate values from FMA metadata (CC BY 4.0, Defferrard et al., arXiv:1612.01840)",
        "source_zip_sha256": sha256_file(ZIP),
        "method": "research/protocol.md section 10.1",
        "calibration": calibration,
        "catalogue": {
            "path": "data/processed/fma_catalogue_v1.npz (git-ignored)",
            "sha256": sha,
            "split": "test",
            "n_tracks": int(arrays["track_id"].size),
            "dim": DIM,
            "genre_counts": [int((arrays["genre"] == g).sum()) for g in range(len(arrays["genre_titles"]))],
        },
        "counts": {**dict(sorted(counts.values.items())), **dict(sorted(cat_counts.items()))},
    }
    OUT_JSON.write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
