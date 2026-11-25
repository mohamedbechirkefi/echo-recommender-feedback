# SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
"""M4 evidence audit: the manuscript and its tables agree with the committed
analysis outputs (master prompt 11.5). These tests read committed files only."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
MANUSCRIPT = REPO / "research" / "paper" / "manuscript.md"
SUPPLEMENT = REPO / "research" / "paper" / "supplementary.md"
CLAIMS = REPO / "research" / "claims_register.csv"


def _analysis(exp: str) -> dict:
    return json.loads((REPO / "results" / exp / "analysis" / "analysis.json").read_text())


def _f(x: float) -> str:
    return f"{x:.4f}"


def _ci(c, key="boot_ci95") -> str:
    lo, hi = c[key]
    return f"[{_f(lo)}, {_f(hi)}]"


needs_results = pytest.mark.skipif(not (REPO / "results" / "EXP-002" / "analysis" / "analysis.json").exists(),
                                   reason="confirmatory results not present")


@needs_results
def test_manifest_builder_maps_every_decimal():
    sys.path.insert(0, str(REPO / "scripts"))
    import build_artifact_manifest as b  # noqa: E402

    entries, unmatched, _structural, _missing = b.audit()
    assert entries, "no numbers found"
    assert unmatched == []


@needs_results
def test_primary_numbers_in_manuscript_and_claims():
    text = MANUSCRIPT.read_text()
    claims = CLAIMS.read_text()
    p2 = _analysis("EXP-002")["drift_family"]["SIM-RAND"]
    p4 = _analysis("EXP-004")["drift_family"]["SIM-RAND"]
    for c in (p2, p4):
        assert _f(c["mean_diff"]).lstrip("-") in text
        assert _ci(c) in text
        assert _ci(c) in claims
    cells = _analysis("EXP-003")["cells"]
    for k in ("bounded/eta=0.05/estimated", "bounded/eta=0.05/oracle"):
        assert _ci(cells[k]) in text
        assert _ci(cells[k]) in claims
    assert "not peer-reviewed" in text


@needs_results
def test_supplementary_table_s2_matches_cells():
    cells = _analysis("EXP-003")["cells"]
    rows = {}
    for line in SUPPLEMENT.read_text().splitlines():
        m = re.match(r"\| (bounded|consumed|exposure) / ([\d.]+) / (estimated|oracle) \| (.*)", line)
        if m:
            rows[f"{m.group(1)}/eta={m.group(2)}/{m.group(3)}"] = [x.strip() for x in m.group(4).split("|")]
    assert set(rows) == set(cells)
    for k, c in cells.items():
        mean, boot, holm, dz, decision = rows[k][:5]
        assert mean == _f(c["mean_diff"])
        assert boot == _ci(c)
        assert holm == f"[{_f(c['holm']['ci'][0])}, {_f(c['holm']['ci'][1])}]"
        assert dz == f"{c['d_z']:.2f}"
        assert decision == c["decision"]


@needs_results
def test_manuscript_table_1_matches_exp002():
    fam = _analysis("EXP-002")["drift_family"]
    text = MANUSCRIPT.read_text()
    for name, c in fam.items():
        row = next(line for line in text.splitlines() if line.startswith(f"| {name}"))
        cols = [x.strip() for x in row.strip("|").split("|")]
        assert cols[1] == _f(c["mean_diff"])
        assert cols[2] == _ci(c)
        assert cols[3] == f"[{_f(c['holm']['ci'][0])}, {_f(c['holm']['ci'][1])}]"
        assert cols[4] == f"{c['d_z']:.2f}"
        assert cols[5] == c["decision"]
