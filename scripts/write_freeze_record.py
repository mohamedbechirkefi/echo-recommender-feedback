# SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
"""Fill the hash fields of research/freeze.json from the files on disk.

The freeze record's text fields (approval quotes, C1 to C4, disclosures) are
written by hand; this script only computes and inserts the SHA-256 values of
the protocols, the configs and the data manifest, and the git revision at
which they were committed. Run it after committing the frozen files, then
commit the record.

    python3 scripts/write_freeze_record.py
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "research" / "freeze.json"
PROTOCOLS = ["research/protocol.md"] + [f"research/experiments/EXP-00{i}/protocol.md" for i in (1, 2, 3, 4)]
CONFIGS = [f"experiments/EXP-00{i}/config.json" for i in (1, 2, 3, 4)]
DATA = ["data/manifest.json", "data/fma_calibration_v1.json"]


def sha(rel: str) -> str:
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def canonical(rel: str) -> str:
    obj = json.loads((ROOT / rel).read_text(encoding="utf-8"))
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main() -> None:
    rec = json.loads(RECORD.read_text(encoding="utf-8"))
    rev = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--", *PROTOCOLS, *CONFIGS, *DATA],
                           capture_output=True, text=True, check=True).stdout.strip()
    if dirty:
        raise SystemExit(f"frozen files are not committed:\n{dirty}")
    rec["frozen_revision"] = rev
    rec["protocols"] = {p: sha(p) for p in PROTOCOLS}
    rec["configs"] = {c: {"file_sha256": sha(c), "canonical_sha256": canonical(c)} for c in CONFIGS}
    rec["data"] = {d: sha(d) for d in DATA}
    RECORD.write_text(json.dumps(rec, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: rec[k] for k in ("frozen_revision", "protocols", "configs", "data")}, indent=1))


if __name__ == "__main__":
    main()
