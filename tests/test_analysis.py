# SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
"""Confirmatory analysis (echo.analysis) on hand-built inputs; no experiment is run."""

from __future__ import annotations

import math

import pytest

from echo import analysis as A
from echo.metrics import METRIC_NAMES
from echo.stats import paired_bootstrap_ci


def test_bootstrap_matches_stats_module():
    d = [0.1, -0.02, 0.05, 0.07, 0.03, 0.0, 0.08, 0.04, 0.06, 0.02]
    assert A.percentile_ci(A.boot_means(d), 0.95) == paired_bootstrap_ci(d)


def test_boot_p_value_known_cases():
    assert A.boot_p_value(A.boot_means([1.0, 2.0, 3.0])) == 0.0
    assert A.boot_p_value(A.boot_means([-1.0, -2.0, -3.0])) == 0.0
    p = A.boot_p_value(A.boot_means([-1.0, 1.0, -0.5, 0.5]))
    assert 0.5 < p <= 1.0


def test_holm_hand_computed():
    h = A.holm({"a": 0.01, "b": 0.04, "c": 0.03, "d": 0.005})
    assert [h[k]["rank"] for k in "dacb"] == [1, 2, 3, 4]
    assert h["d"]["p_holm"] == pytest.approx(0.02)
    assert h["a"]["p_holm"] == pytest.approx(0.03)
    assert h["c"]["p_holm"] == pytest.approx(0.06)
    assert h["b"]["p_holm"] == pytest.approx(0.06)  # monotone
    assert h["d"]["level"] == pytest.approx(1 - 0.05 / 4)
    assert h["b"]["level"] == pytest.approx(0.95)
    assert [h[k]["reject"] for k in "dacb"] == [True, True, False, False]


def test_holm_stops_at_first_failure():
    h = A.holm({"a": 0.02, "b": 0.001})
    assert h["b"]["reject"] is True and h["a"]["reject"] is True  # 0.02 <= 0.05 / 1
    h = A.holm({"a": 0.03, "b": 0.03})
    assert not h["a"]["reject"] and not h["b"]["reject"]  # 0.03 > 0.025


def _cell(mean, lo, hi, eta, decision=None):
    from echo.stats import decide

    return {"mean_diff": mean, "boot_ci95": [lo, hi], "eta": eta,
            "ci_excludes_zero": lo > 0 or hi < 0, "ci_inside_sesoi_band": -0.05 <= lo and hi <= 0.05,
            "decision": decision or decide((lo, hi), 0.05)}


def test_robustness_retained_withdrawn_partial():
    ref = {"mean_diff": -0.2}
    ok = {f"c{i}": _cell(-0.2, -0.25, -0.15, eta) for i, eta in enumerate((0.01, 0.05, 0.2))}
    assert A.robustness_verdict(ok, ref)["verdict"] == "retained"
    flip = dict(ok, x=_cell(0.1, 0.06, 0.14, 0.05))
    assert A.robustness_verdict(flip, ref)["verdict"] == "withdrawn as assumption-dependent"
    equiv = dict(ok, x=_cell(0.0, -0.02, 0.02, 0.05))
    assert A.robustness_verdict(equiv, ref)["verdict"] == "withdrawn as assumption-dependent"
    partial = dict(ok, x=_cell(-0.1, -0.2, 0.06, 0.2))
    assert A.robustness_verdict(partial, ref)["verdict"] == "partially robust"
    # eta = 0.01 cells do not enter the retain condition
    low = dict(ok, x=_cell(0.1, -0.2, 0.3, 0.01))
    assert A.robustness_verdict(low, ref)["verdict"] == "retained"


def test_robustness_readings_can_disagree():
    ref = {"mean_diff": -0.2}
    cells = {"a": _cell(-0.03, -0.04, -0.02, 0.05)}  # detectable but negligible
    v = A.robustness_verdict(cells, ref)
    assert v["band_reading"]["verdict"] == "withdrawn as assumption-dependent"
    assert v["label_reading"]["verdict"] == "retained"
    assert v["verdict"].startswith("readings disagree")


def test_replication_reading():
    ref = {"mean_diff": -0.2}
    assert A.replication_reading(_cell(-0.1, -0.15, -0.06, 0.05), ref)["reading"] == "replicates on the real catalogue"
    assert A.replication_reading(_cell(0.1, 0.06, 0.15, 0.05), ref)["reading"] == "does not replicate"
    assert A.replication_reading(_cell(0.0, -0.03, 0.03, 0.05), ref)["reading"] == "does not replicate"
    assert A.replication_reading(_cell(-0.05, -0.2, 0.1, 0.05), ref)["reading"] == "inconclusive on the real catalogue"
    assert A.replication_reading(_cell(-0.03, -0.04, -0.02, 0.05), ref)["reading"].startswith("readings disagree")


def _run(policy, pref, seed, drift, status="ok"):
    eta = 0.05 if pref == "adaptive" else 0.0
    cfg = {"policy": policy, "preference_model": pref, "eta": eta, "update_rule": "consumed", "profile": "estimated", "seed": seed}
    metrics = {m: 0.5 for m in METRIC_NAMES}
    metrics["drift_rad"] = drift
    metrics["drift_per_accept_rad"] = drift / 100
    metrics["skip_rate"] = 0.01 * (seed % 3)
    return {"result": {"run_id": f"EXP-009_main_{policy}_{pref}-{eta}_s{seed}", "config": cfg, "status": status,
                       "metrics": metrics if status == "ok" else None,
                       "per_user": {"drift_rad": [drift, drift]} if status == "ok" else None},
            "manifest": {"git": {"revision": "x", "code_dirty": False}}}


def _matrix(sim_shift=-0.1):
    runs = []
    for s in range(10):
        for pol, shift in (("RAND", 0.0), ("SIM", sim_shift), ("POP", 0.2), ("MMR", 0.01 * (s - 4.5)), ("EXPLORE", -0.05)):
            runs.append(_run(pol, "adaptive", s, 0.6 + shift + 0.01 * s + (0.003 * s * s if pol == "SIM" else 0)))
            runs.append(_run(pol, "fixed", s, 0.0))
    return runs


def test_policy_matrix_end_to_end():
    a = A.analyse_policy_matrix(_matrix(), planned=100)
    assert a["integrity"]["complete"] and a["integrity"]["failed_runs"] == 0
    assert a["integrity"]["negative_control"]["pass"]
    pr = a["primary"]
    assert pr["n_seeds"] == 10 and pr["mean_diff"] == pytest.approx(-0.1 + 0.003 * 28.5)
    assert set(a["drift_family"]) == {"SIM-RAND", "POP-RAND", "MMR-RAND", "EXPLORE-RAND"}
    assert all(c["holm"]["family_size"] == 4 for c in a["drift_family"].values())
    assert a["drift_family"]["POP-RAND"]["decision"] == "reject H0"
    assert len(a["arms"]) == 10


def test_negative_control_failure_is_flagged():
    runs = _matrix()
    runs[1]["result"]["per_user"]["drift_rad"] = [0.0, 1e-15]
    it = A.integrity(runs, 100)
    assert not it["negative_control"]["pass"] and it["negative_control"]["runs_with_nonzero_drift"]


def test_failed_runs_counted_and_stop_rule():
    runs = _matrix()
    runs[0] = _run("RAND", "adaptive", 0, 0.0, status="failed")
    it = A.integrity(runs, 100)
    assert it["failed_runs"] == 1 and it["stop_rule_arms"] == []
    runs[10] = _run("RAND", "adaptive", 1, 0.0, status="failed")
    it = A.integrity(runs, 100)
    assert it["stop_rule_arms"] == ["EXP-009_main_RAND_adaptive-0.05"]
    assert not math.isnan(A.analyse_policy_matrix(runs, 100)["primary"]["mean_diff"])


def test_manifest_records_data_hashes():
    from echo.manifest import REPO_ROOT, build_manifest, data_provenance

    d = data_provenance()
    assert set(d) == {"data/manifest.json", "data/fma_calibration_v1.json"}
    assert all(v is None or len(v) == 64 for v in d.values())
    assert (REPO_ROOT / "data" / "manifest.json").exists() and d["data/manifest.json"]
    m = build_manifest(run_id="r", experiment_id="EXP-001", label="exploratory", config_hash="0" * 64, seed=1,
                       status="ok", started_utc="a", finished_utc="b", runtime_s=0.0, peak_traced_bytes=None,
                       env={}, git={}, result_path="runs/r.json", data=d)
    assert m["data_sha256"] == d


def test_analysis_refuses_exploratory_results():
    from echo.manifest import REPO_ROOT

    with pytest.raises(ValueError):
        A.run_analysis(REPO_ROOT / "results" / "exploratory" / "EXP-001", planned=86, kind="policy")


def test_tables_have_plain_floats_and_per_accept_has_no_sesoi_label(tmp_path):
    """Evidence-audit findings F-2 and F-3 (DEC-016)."""
    a = A.analyse_policy_matrix(_matrix(), planned=100)
    assert all(type(x) is float for c in a["drift_family"].values() for x in c["t_ci95"])
    pa = a["drift_per_accept_SIM-RAND"]
    assert "decision" not in pa and "ci_inside_sesoi_band" not in pa and "ci_excludes_zero" in pa
    A.write_tables(a, tmp_path)
    for name in ("arms.csv", "contrasts.csv", "per_seed.csv"):
        assert "np." not in (tmp_path / name).read_text(encoding="utf-8")
