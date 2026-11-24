# SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
"""The freeze record (research/freeze.json) matches the files on disk and the registry.

Reads files only; never runs an experiment.
"""

from __future__ import annotations

import csv
import hashlib
import json

from echo.manifest import REPO_ROOT
from echo.runner import protocol_frozen

REC = json.loads((REPO_ROOT / "research" / "freeze.json").read_text(encoding="utf-8"))


def _sha(rel: str) -> str:
    return hashlib.sha256((REPO_ROOT / rel).read_bytes()).hexdigest()


def test_record_fields():
    assert REC["frozen_by_owner"] is True and REC["approved_on"] == "2026-11-24"
    assert "Approve all" in REC["owner_approval_quote"]["second_round"]
    assert "yes for all others" in REC["owner_approval_quote"]["earlier_amendment_list"]
    assert set(REC["common_decisions"]) == {"C1", "C2", "C3", "C4"}
    assert REC["common_decisions"]["C1"].startswith("Data. Real data as approved, synthetic otherwise")
    assert any("-0.15881" in d["values"] for d in REC["c4_disclosure"])
    assert len(REC["frozen_revision"]) == 40


def test_hashes_match_files():
    for rel, h in REC["protocols"].items():
        assert _sha(rel) == h, rel
    for rel, entry in REC["configs"].items():
        assert _sha(rel) == entry["file_sha256"], rel
    for rel, h in REC["data"].items():
        assert _sha(rel) == h, rel


def test_registry_matches_record_and_is_frozen():
    with open(REPO_ROOT / "research" / "experiment_registry.csv", newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert [r["experiment_id"] for r in rows] == ["EXP-001", "EXP-002", "EXP-003", "EXP-004"]
    for r in rows:
        assert r["protocol_hash"] == REC["protocols"][r["protocol_path"]]
        assert protocol_frozen(r["experiment_id"], REPO_ROOT / r["protocol_path"])[0]


def test_fitted_values_are_in_the_configs():
    cal = json.loads((REPO_ROOT / "data" / "fma_calibration_v1.json").read_text())["calibration"]
    for eid in ("EXP-002", "EXP-003"):
        exp = json.loads((REPO_ROOT / "experiments" / eid / "config.json").read_text())
        for b in exp["blocks"]:
            assert b["base"] == {"n_clusters": cal["n_clusters"], "cluster_weights": cal["cluster_weights"],
                                 "zipf_s": cal["zipf_s"]}
    exp4 = json.loads((REPO_ROOT / "experiments" / "EXP-004" / "config.json").read_text())
    assert exp4["blocks"][0]["base"]["fma_catalogue_sha256"] == REC["real_data"]["processed_catalogue_sha256"]
