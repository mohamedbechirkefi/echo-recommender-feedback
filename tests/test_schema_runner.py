# SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
"""Result schema, run guards (freeze, seeds, paths), runner integration, stats, report."""

import copy
import csv
import hashlib
import json
import math
from pathlib import Path

import pytest

from echo import cli
from echo.config import SimConfig
from echo.manifest import REPO_ROOT
from echo.report import generate
from echo.runner import (
    PlannedRun, RefusedError, StopRuleError, check_permission, execute, expand, load_experiment,
    protocol_frozen, run_experiment,
)
from echo.schema import SchemaError, dumps_result, read_result, validate_result
from echo.stats import cohen_dz, decide, paired_bootstrap_ci, paired_t_ci, projected_half_width, t975

SMALL = dict(n_tracks=60, n_users=6, n_steps=10, slate_size=5, dim=6, n_clusters=4, warmup_steps=2)


def _ok_result():
    run = PlannedRun("b", "b/x", "EXP-001_b_x_s900900", SimConfig(seed=900900, **SMALL))
    res, _, _ = execute(run, "EXP-001", "exploratory")
    return res


# ---------- schema ----------

def test_valid_result_round_trip(tmp_path):
    res = _ok_result()
    assert res["status"] == "ok"
    p = tmp_path / "r.json"
    p.write_text(dumps_result(res))
    assert read_result(p) == json.loads(dumps_result(res))


@pytest.mark.parametrize("mutate,msg", [
    (lambda r: r.pop("metrics"), "missing"),
    (lambda r: r.update(extra=1), "unexpected"),
    (lambda r: r.update(schema_version="echo.result.v0"), "schema_version"),
    (lambda r: r["metrics"].update(drift_rad=float("nan")), "non-finite"),
    (lambda r: r["metrics"].pop("skip_rate"), "exactly the keys"),
    (lambda r: r.update(config_hash="0" * 64), "does not match"),
    (lambda r: r["config"].update(tau=0.2), "does not match"),
    (lambda r: r.update(seed=1), "seed"),
    (lambda r: r.update(label="final"), "label"),
    (lambda r: r.update(experiment_id="EXP1"), "EXP-NNN"),
    (lambda r: r["per_user"]["drift_rad"].pop(), "length"),
    (lambda r: r["per_user"]["skips"].__setitem__(0, 99), "n_steps"),
    (lambda r: r.update(status="done"), "status"),
    (lambda r: r.update(error="x"), "null"),
    (lambda r: r["config"].update(policy="NOPE"), "config invalid"),
])
def test_schema_rejects_malformed(mutate, msg):
    r = copy.deepcopy(_ok_result())
    mutate(r)
    with pytest.raises(SchemaError, match=msg):
        validate_result(r)


def test_read_result_fails_closed_on_bad_json(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{not json")
    with pytest.raises(SchemaError):
        read_result(p)


def test_failed_run_is_recorded_not_raised():
    cfg = SimConfig(seed=900901, **{**SMALL, "skip_utility": 50.0})  # nobody accepts -> NaN metrics
    res, _, _ = execute(PlannedRun("b", "b/x", "EXP-001_b_fail_s900901", cfg), "EXP-001", "exploratory")
    assert res["status"] == "failed" and "non-finite" in res["error"]
    assert "/Users" not in res["error"]
    validate_result(res)


# ---------- guards ----------

def test_confirmatory_configs_are_refused_while_unfrozen():
    for exp_id in ("EXP-002", "EXP-003"):
        exp = load_experiment(REPO_ROOT / "experiments" / exp_id / "config.json")
        assert exp["label"] == "confirmatory"
        with pytest.raises(RefusedError, match="not frozen"):
            check_permission(exp, expand(exp), REPO_ROOT / "results" / exp_id)


def test_cli_run_refuses_confirmatory_with_exit_code_2(capsys):
    code = cli.main(["run", "--config", str(REPO_ROOT / "experiments" / "EXP-002" / "config.json")])
    assert code == 2
    assert "REFUSED" in capsys.readouterr().err
    assert not (REPO_ROOT / "results" / "EXP-002").exists()


def _registry(tmp_path, status, h):
    p = tmp_path / "reg.csv"
    with open(p, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["experiment_id", "protocol_hash", "status"])
        w.writerow(["EXP-009", h, status])
    return p


def test_protocol_frozen_logic(tmp_path):
    proto = tmp_path / "protocol.md"
    proto.write_text("frozen text\n")
    h = hashlib.sha256(proto.read_bytes()).hexdigest()
    assert protocol_frozen("EXP-009", proto, _registry(tmp_path, "frozen v1.0", h))[0]
    assert not protocol_frozen("EXP-009", proto, _registry(tmp_path, "planned (awaiting owner freeze)", h))[0]
    assert not protocol_frozen("EXP-009", proto, _registry(tmp_path, "frozen v1.0", "none"))[0]
    assert not protocol_frozen("EXP-009", proto, _registry(tmp_path, "frozen v1.0", "a" * 64))[0]
    assert not protocol_frozen("EXP-010", proto, _registry(tmp_path, "frozen v1.0", h))[0]


def _exp(tmp_path, seeds, label="exploratory"):
    exp = {"experiment_id": "EXP-001", "label": label, "protocol_path": "research/experiments/EXP-001/protocol.md",
           "blocks": [{"name": "t", "base": SMALL, "factors": {"policy": ["RAND", "SIM"]}, "seeds": seeds}]}
    p = tmp_path / "exp.json"
    p.write_text(json.dumps(exp))
    return p


def test_exploratory_guards(tmp_path):
    with pytest.raises(RefusedError, match="confirmatory seeds"):
        run_experiment(_exp(tmp_path, [20261124]), REPO_ROOT / "results" / "exploratory" / "_never")
    with pytest.raises(RefusedError, match="exploratory output"):
        run_experiment(_exp(tmp_path, [900950]), tmp_path / "out")


def test_expand_cartesian_and_ids():
    exp = {"experiment_id": "EXP-001", "label": "exploratory", "protocol_path": "x", "blocks": [
        {"name": "b", "base": SMALL, "factors": {"policy": ["RAND", "SIM"],
                                                "pref": [{"preference_model": "fixed", "eta": 0.0}, {"eta": 0.05}]},
         "seeds": [1, 2]}]}
    runs = expand(exp)
    assert len(runs) == 8 and len({r.run_id for r in runs}) == 8
    assert runs[0].run_id == "EXP-001_b_RAND_fixed-0.0_s1"
    assert {r.config.eta for r in runs} == {0.0, 0.05}


def test_registered_configs_expand_to_planned_sizes():
    sizes = {e: len(expand(load_experiment(REPO_ROOT / "experiments" / e / "config.json"))) for e in ("EXP-001", "EXP-002", "EXP-003")}
    assert sizes["EXP-002"] == 100 and sizes["EXP-003"] == 360
    assert sizes["EXP-001"] == 20 + 20 + 10 + 36


def test_run_experiment_integration_and_report(tmp_path, monkeypatch):
    out = REPO_ROOT / "results" / "exploratory" / "_pytest_tmp"
    try:
        summ = run_experiment(_exp(tmp_path, [900960, 900961]), out)
        assert len(summ) == 4 and all(s["result"]["status"] == "ok" for s in summ)
        man = json.loads((out / "manifests" / f"{summ[0]['run'].run_id}.manifest.json").read_text())
        assert man["runtime_s"] > 0 and man["config_hash"] == summ[0]["result"]["config_hash"]
        assert "/Users" not in json.dumps(man)
        rep = generate(out, pdf=False)
        assert rep["n_runs"] == 4 and rep["n_failed"] == 0
        assert (out / "report" / "metrics.csv").exists() and (out / "report" / "summary.md").exists()
        # fail closed on a corrupted result file
        f = next((out / "runs").glob("*.json"))
        f.write_text(f.read_text().replace('"status": "ok"', '"status": "maybe"'))
        with pytest.raises(SchemaError):
            generate(out, pdf=False)
    finally:
        import shutil
        shutil.rmtree(out, ignore_errors=True)


def test_stop_rule(tmp_path):
    exp = {"experiment_id": "EXP-001", "label": "exploratory", "protocol_path": "x",
           "blocks": [{"name": "f", "base": {**SMALL, "skip_utility": 50.0}, "factors": {"policy": ["RAND"]}, "seeds": [900970, 900971]}]}
    p = tmp_path / "e.json"
    p.write_text(json.dumps(exp))
    out = REPO_ROOT / "results" / "exploratory" / "_pytest_stop"
    try:
        with pytest.raises(StopRuleError):
            run_experiment(p, out)
    finally:
        import shutil
        shutil.rmtree(out, ignore_errors=True)


# ---------- stats ----------

def test_stats_hand_computed():
    d = [1.0, 2.0, 3.0]
    lo, hi = paired_t_ci(d)  # mean 2, sd 1, t(2) = 4.303
    assert lo == pytest.approx(2 - 4.303 / math.sqrt(3)) and hi == pytest.approx(2 + 4.303 / math.sqrt(3))
    assert cohen_dz(d) == pytest.approx(2.0)
    assert projected_half_width(1.0, 10) == pytest.approx(2.262 / math.sqrt(10))
    with pytest.raises(ValueError):
        t975(1000)
    with pytest.raises(ValueError):
        cohen_dz([1.0, 1.0])


def test_bootstrap_deterministic_and_contains_mean():
    d = [0.1, 0.3, -0.2, 0.05, 0.12, 0.2]
    a = paired_bootstrap_ci(d)
    assert a == paired_bootstrap_ci(d)
    assert a[0] <= sum(d) / len(d) <= a[1]


@pytest.mark.parametrize("ci,expected", [
    ((0.06, 0.2), "reject H0"), ((-0.3, -0.1), "reject H0"), ((-0.02, 0.03), "practically equivalent"),
    ((-0.1, 0.2), "inconclusive"), ((0.01, 0.04), "reject H0, smaller than SESOI"), ((-0.01, 0.07), "inconclusive"),
])
def test_decision_rule(ci, expected):
    assert decide(ci, 0.05) == expected
