# SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
"""M5 consistency (master prompt 11.6): the demo shows the manuscript's numbers.

1. Re-running the export in memory gives the committed results.json byte for byte.
2. Every display and interval_display string appears verbatim in the manuscript,
   or, where display_source is "supplementary", in the supplementary appendix
   (documented exception: nine EXP-003 oracle cells printed only in Table S2).
3. The sandbox fixture and the taste-map trace regenerate identically from the
   Python engine (exploratory, a few seconds).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
RESULTS = REPO / "demo" / "public" / "data" / "results.json"
MANUSCRIPT = REPO / "research" / "paper" / "manuscript.md"
SUPPLEMENTARY = REPO / "research" / "paper" / "supplementary.md"

needs_results = pytest.mark.skipif(not (REPO / "results" / "EXP-002" / "analysis" / "analysis.json").exists(),
                                   reason="confirmatory results not present")


def _export():
    sys.path.insert(0, str(REPO / "scripts"))
    import export_demo_data  # noqa: E402

    return export_demo_data


def _display_items(data):
    for e in data["experiments"]:
        for x in e["estimates"]:
            yield e["id"], x
    for x in data["contrast_chart"]:
        yield x["experiment"], x
    for exp, rows in data["arm_drift"].items():
        for x in rows:
            yield exp, x


@needs_results
def test_committed_export_is_reproduced_exactly():
    assert RESULTS.read_text() == _export().render()


@needs_results
def test_every_display_string_is_printed_in_the_manuscript():
    data = json.loads(RESULTS.read_text())
    texts = {"manuscript": MANUSCRIPT.read_text(), "supplementary": SUPPLEMENTARY.read_text()}
    missing, n = [], 0
    for exp, x in _display_items(data):
        src = x["display_source"]
        assert src in texts, f"{exp} {x['label']}: unknown display_source {src!r}"
        if src == "supplementary":
            assert exp == "EXP-003" and x["label"].endswith("/ oracle"), "only EXP-003 oracle cells may cite S2"
        for key in ("display", "interval_display"):
            s = x[key]
            if s is None:
                continue
            n += 1
            if s not in texts[src]:
                missing.append(f"{exp} {x['label']} {key}={s!r} not in {src}")
    assert n > 50
    assert missing == []


@needs_results
def test_every_registered_experiment_is_exported_with_status_verdict_and_claims():
    data = json.loads(RESULTS.read_text())
    ids = [e["id"] for e in data["experiments"]]
    assert ids == ["EXP-001", "EXP-002", "EXP-003", "EXP-004"]
    by = {e["id"]: e for e in data["experiments"]}
    assert by["EXP-003"]["verdict"] == "withdrawn as assumption-dependent"
    assert by["EXP-004"]["verdict"].endswith("does not replicate")
    assert by["EXP-002"]["claim_ids"][:2] == ["C-001", "C-002"]
    assert "C-004" in by["EXP-003"]["claim_ids"] and "C-006" in by["EXP-004"]["claim_ids"]
    assert data["code_revision"] == "afc08509847ac362b6b95d8097aea08a615f286b"
    assert "timestamp" not in RESULTS.read_text().lower()


@needs_results
def test_engine_fixture_and_taste_map_regenerate_identically():
    sys.path.insert(0, str(REPO / "scripts"))
    import m5_exploratory_engine_traces as m  # noqa: E402

    assert m.main(["--check"]) == 0
