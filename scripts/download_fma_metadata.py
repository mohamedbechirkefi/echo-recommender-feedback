# SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
"""Download FMA metadata (fma_metadata.zip, CC BY 4.0) into data/raw/.

Deterministic: one fixed URL, one fixed file name. The published SHA-1 from
the FMA README is checked; the SHA-256, size, URL and access date are written
to data/raw/fma_metadata.download.json. data/raw/ is git-ignored (the archive
is 342 MiB, above the 20 MB commit limit of the owner's data rules); the
record's values are copied into data/manifest.json.

Usage (from the repository root):
    python3 scripts/download_fma_metadata.py [--force]

Source: https://github.com/mdeff/fma (Defferrard et al., arXiv:1612.01840).
Licence of the metadata: CC BY 4.0. Audio is never downloaded.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

URL = "https://os.unil.cloud.switch.ch/fma/fma_metadata.zip"
PUBLISHED_SHA1 = "f0df49ffe5f2a6008d7dc83c6915b31835dfe733"
EXPECTED_SIZE = 358412441
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
TARGET = RAW / "fma_metadata.zip"
RECORD = RAW / "fma_metadata.download.json"


def digests(path: Path) -> tuple[str, str, int]:
    h256, h1, n = hashlib.sha256(), hashlib.sha1(), 0
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h256.update(chunk)
            h1.update(chunk)
            n += len(chunk)
    return h256.hexdigest(), h1.hexdigest(), n


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="download again even if the file exists")
    args = ap.parse_args(argv)
    RAW.mkdir(parents=True, exist_ok=True)
    if args.force or not TARGET.exists():
        tmp = TARGET.with_suffix(".part")
        with urllib.request.urlopen(URL, timeout=120) as resp, open(tmp, "wb") as out:
            while chunk := resp.read(1 << 20):
                out.write(chunk)
        tmp.replace(TARGET)
    sha256, sha1, size = digests(TARGET)
    if sha1 != PUBLISHED_SHA1 or size != EXPECTED_SIZE:
        print(f"MISMATCH: sha1 {sha1} size {size}; expected {PUBLISHED_SHA1} {EXPECTED_SIZE}", file=sys.stderr)
        return 1
    record = {
        "url": URL,
        "file": "data/raw/fma_metadata.zip",
        "accessed_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "size_bytes": size,
        "sha256": sha256,
        "sha1": sha1,
        "sha1_matches_published": True,
        "licence": "CC BY 4.0 (metadata); audio not downloaded",
    }
    RECORD.write_text(json.dumps(record, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
