# SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
"""Write the committed FMA-schema fixture: SYNTHETIC rows only, never real FMA rows.

The three tables mimic the FMA metadata layout (tracks.csv two-level header
plus the track_id row; genres.csv; features.csv with four header rows and 518
feature columns). All values are generated here from a fixed seed. Titles
and genre names are invented placeholders.

    python3 tests/fixtures/make_fma_fixture.py
"""

from __future__ import annotations

import csv
import random
from pathlib import Path

OUT = Path(__file__).resolve().parent / "fma_synthetic"
N_FEATURES = 518
GENRES = [  # genre_id, #tracks, parent, title, top_level
    (2, 0, 0, "GenreA", 2),
    (5, 0, 0, "GenreB", 5),
    (9, 0, 0, "GenreC", 9),
    (21, 0, 2, "GenreA-sub", 2),
]
TOPS = ["GenreA", "GenreB", "GenreC"]


def main() -> None:
    rnd = random.Random(20261124)
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "genres.csv", "w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["genre_id", "#tracks", "parent", "title", "top_level"])
        w.writerows(GENRES)
    top = ["", "album", "set", "set", "track", "track", "track"]
    sub = ["", "title", "split", "subset", "genre_top", "listens", "title"]
    rows = []
    splits = ["training"] * 30 + ["validation"] * 4 + ["test"] * 14
    for i, split in enumerate(splits):
        tid = 100 + 3 * i
        genre = TOPS[i % 3] if i % 7 != 6 else ""  # every 7th genre_top missing
        listens = 0 if i % 11 == 10 else int(1000 / (i + 1)) + rnd.randint(0, 3)
        rows.append([str(tid), f"Album {i}", split, "large", genre, str(listens), f"Synthetic, \"track\" {i}"])
    with open(OUT / "tracks.csv", "w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(top)
        w.writerow(sub)
        w.writerow(["track_id"] + [""] * (len(top) - 1))
        w.writerows(rows)
    with open(OUT / "features.csv", "w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["feature"] + [f"feat{j // 7}" for j in range(N_FEATURES)])
        w.writerow(["statistics"] + ["mean"] * N_FEATURES)
        w.writerow(["number"] + [f"{j % 7 + 1:02d}" for j in range(N_FEATURES)])
        w.writerow(["track_id"] + [""] * N_FEATURES)
        for i, r in enumerate(rows):
            g = TOPS.index(r[4]) if r[4] else 0
            vals = [f"{(g - 1) * (1 + (j % 3)) + rnd.gauss(0, 0.5):.3f}" for j in range(N_FEATURES)]
            if i == 5:
                vals[17] = "nan"  # one non-finite feature row (excluded, counted)
            if i == 40:
                continue  # one track without a feature row
            w.writerow([r[0]] + vals)


if __name__ == "__main__":
    main()
