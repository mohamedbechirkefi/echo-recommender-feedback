# SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
"""M4 exploratory confounder inspection (EXPLORATORY, never confirmatory).

This script runs no simulation and no policy. It reads committed confirmatory
results and regenerates only the *inputs* (catalogue and initial listener
tastes) that the frozen configs produce for their seeds. Nothing here changes
or replaces a frozen verdict. Output: results/exploratory/M4-confounders/.

Usage:
    PYTHONPATH=src .venv/bin/python scripts/m4_exploratory_confounders.py

Parts:
  A. Per-seed sign consistency of every drift contrast (from analysis.json).
  B. Per-listener drift distributions of the adaptive arms of EXP-002 and
     EXP-004 (from the committed run files): ceiling and compression check.
  C. Skip-rate confounder: drift versus drift per accepted item (from
     analysis.json, already committed; collected side by side).
  D. Catalogue and initial-taste geometry for the ten confirmatory seeds,
     synthetic calibrated catalogue (EXP-002 config) versus FMA catalogue
     (EXP-004 config). Inputs only, no outcome is computed.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from echo.catalogue import generate_catalogue, generate_listeners  # noqa: E402
from echo.runner import expand, load_experiment  # noqa: E402

OUT = REPO / "results" / "exploratory" / "M4-confounders"


def load_json(p: Path):
    with open(p) as f:
        return json.load(f)


def sign_counts(diffs):
    d = np.asarray(diffs, dtype=float)
    return {"n": int(d.size), "negative": int((d < 0).sum()), "positive": int((d > 0).sum()),
            "zero": int((d == 0).sum())}


def part_a():
    out = {}
    for exp in ("EXP-002", "EXP-004"):
        a = load_json(REPO / "results" / exp / "analysis" / "analysis.json")
        for name, c in a["drift_family"].items():
            out[f"{exp}/{name}"] = {"mean_diff": c["mean_diff"], **sign_counts(c["diffs"])}
    a = load_json(REPO / "results" / "EXP-003" / "analysis" / "analysis.json")
    for name, c in a["cells"].items():
        out[f"EXP-003/{name}"] = {"mean_diff": c["mean_diff"], **sign_counts(c["diffs"])}
    return out


def part_b():
    out = {}
    q = [0.1, 0.5, 0.9]
    for exp in ("EXP-002", "EXP-004"):
        per_arm: dict[str, list[float]] = {}
        for p in sorted((REPO / "results" / exp / "runs").glob("*.json")):
            r = load_json(p)
            if r["config"]["preference_model"] != "adaptive" or r["status"] != "ok":
                continue
            per_arm.setdefault(r["config"]["policy"], []).extend(r["per_user"]["drift_rad"])
        for pol, vals in per_arm.items():
            v = np.asarray(vals)
            out[f"{exp}/{pol}"] = {
                "n_listener_values": int(v.size),
                "quantiles_rad": {str(k): float(x) for k, x in zip(q, np.quantile(v, q))},
                "max_rad": float(v.max()),
                "share_above_pi_over_2": float((v > math.pi / 2).mean()),
                "note": "pooled over 10 seeds x 200 listeners; listeners are not independent, descriptive only",
            }
    return out


def part_c():
    out = {}
    for exp in ("EXP-002", "EXP-004"):
        a = load_json(REPO / "results" / exp / "analysis" / "analysis.json")
        sec = a["secondary_vs_rand_descriptive"]
        for pol in ("SIM", "POP", "MMR", "EXPLORE"):
            fam = a["drift_family"][f"{pol}-RAND"]
            pa = sec[f"adaptive/{pol}-RAND/drift_per_accept_rad"]
            sk = sec[f"adaptive/{pol}-RAND/skip_rate"]
            out[f"{exp}/{pol}-RAND"] = {
                "drift_mean_diff_rad": fam["mean_diff"], "drift_ci95": fam["boot_ci95"],
                "drift_per_accept_mean_diff": pa["mean_diff"], "drift_per_accept_ci95": pa["ci95"],
                "skip_rate_mean_diff": sk["mean_diff"], "skip_rate_ci95": sk["ci95"],
                "same_sign": bool(np.sign(fam["mean_diff"]) == np.sign(pa["mean_diff"])),
            }
    return out


def _mean_offdiag(g: np.ndarray) -> float:
    n = g.shape[0]
    return float((g.sum() - np.trace(g)) / (n * (n - 1)))


def _gini(x: np.ndarray) -> float:
    x = np.sort(np.asarray(x, dtype=float))
    n = x.size
    return float((2 * np.arange(1, n + 1) - n - 1).dot(x) / (n * x.sum()))


def geometry(config_path: Path):
    exp = load_experiment(config_path)
    seen = set()
    rows = []
    for run in expand(exp):
        cfg = run.config
        if cfg.seed in seen:
            continue
        seen.add(cfg.seed)
        ss = np.random.SeedSequence(cfg.seed)
        s_cat, s_lis, _, _ = ss.spawn(4)
        cat = generate_catalogue(cfg, np.random.default_rng(s_cat))
        lis = generate_listeners(cfg, cat.centres, np.random.default_rng(s_lis))
        x = cat.embeddings
        g = x @ x.T
        nn = g.copy()
        np.fill_diagonal(nn, -np.inf)
        own = np.einsum("ij,ij->i", x, cat.centres[cat.cluster])
        shares = np.bincount(cat.cluster, minlength=cat.centres.shape[0]) / x.shape[0]
        p0 = lis.initial
        rows.append({
            "seed": cfg.seed,
            "centre_pairwise_cos_mean": _mean_offdiag(cat.centres @ cat.centres.T),
            "track_pairwise_cos_mean": _mean_offdiag(g),
            "track_resultant_length": float(np.linalg.norm(x.mean(axis=0))),
            "track_to_own_centre_cos_mean": float(own.mean()),
            "track_nearest_neighbour_cos_mean": float(nn.max(axis=1).mean()),
            "largest_cluster_share": float(shares.max()),
            "base_popularity_gini": _gini(cat.base_pop),
            "initial_taste_pairwise_cos_mean": _mean_offdiag(p0 @ p0.T),
            "initial_taste_to_tracks_cos_mean": float((p0 @ x.T).mean()),
        })
    keys = [k for k in rows[0] if k != "seed"]
    summary = {k: {"mean": float(np.mean([r[k] for r in rows])),
                   "min": float(np.min([r[k] for r in rows])),
                   "max": float(np.max([r[k] for r in rows]))} for k in keys}
    return {"per_seed": rows, "summary": summary}


def part_d():
    return {
        "synthetic_calibrated (EXP-002 config)": geometry(REPO / "experiments" / "EXP-002" / "config.json"),
        "fma (EXP-004 config)": geometry(REPO / "experiments" / "EXP-004" / "config.json"),
        "note": ("Inputs only: catalogue and initial listener tastes regenerated from the frozen configs "
                 "and the catalogue and listener streams of each confirmatory seed. No session, policy "
                 "or outcome is simulated."),
    }


def fmt(x, d=4):
    return f"{x:.{d}f}"


def markdown(res) -> str:
    L = ["<!-- SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0 -->",
         "# M4 exploratory confounder inspection (EXPLORATORY)", "",
         "Generated by `scripts/m4_exploratory_confounders.py` (journal J-0008). Exploratory only: it never changes or replaces a frozen verdict. No simulation was run.", "",
         "## A. Per-seed sign consistency of drift contrasts (n = 10 seeds each)", "",
         "| Contrast | Mean diff (rad) | Seeds < 0 | Seeds > 0 |", "|---|---|---|---|"]
    for k, v in res["A_sign_consistency"].items():
        L.append(f"| {k} | {fmt(v['mean_diff'])} | {v['negative']} | {v['positive']} |")
    L += ["", "## B. Per-listener drift, adaptive arms (pooled 10 seeds x 200 listeners, descriptive)", "",
          "| Arm | P10 (rad) | Median (rad) | P90 (rad) | Max (rad) | Share above pi/2 |", "|---|---|---|---|---|---|"]
    for k, v in res["B_listener_drift"].items():
        qq = v["quantiles_rad"]
        L.append(f"| {k} | {fmt(qq['0.1'])} | {fmt(qq['0.5'])} | {fmt(qq['0.9'])} | {fmt(v['max_rad'])} | {fmt(v['share_above_pi_over_2'], 3)} |")
    L += ["", "## C. Drift versus drift per accepted item (seed-paired vs RAND, from analysis.json)", "",
          "| Contrast | Drift diff (rad) | Per-accept diff (rad/track) | Per-accept 95 % CI | Skip-rate diff | Same sign |",
          "|---|---|---|---|---|---|"]
    for k, v in res["C_skip_confounder"].items():
        ci = v["drift_per_accept_ci95"]
        L.append(f"| {k} | {fmt(v['drift_mean_diff_rad'])} | {fmt(v['drift_per_accept_mean_diff'], 6)} | "
                 f"[{fmt(ci[0], 6)}, {fmt(ci[1], 6)}] | {fmt(v['skip_rate_mean_diff'], 4)} | {'yes' if v['same_sign'] else 'no'} |")
    L += ["", "## D. Catalogue and initial-taste geometry (inputs only; mean over the 10 confirmatory seeds, [min, max])", "",
          "| Quantity | Synthetic calibrated (EXP-002) | FMA (EXP-004) |", "|---|---|---|"]
    syn = res["D_geometry"]["synthetic_calibrated (EXP-002 config)"]["summary"]
    fma = res["D_geometry"]["fma (EXP-004 config)"]["summary"]
    for k in syn:
        s, f = syn[k], fma[k]
        L.append(f"| {k} | {fmt(s['mean'])} [{fmt(s['min'])}, {fmt(s['max'])}] | {fmt(f['mean'])} [{fmt(f['min'])}, {fmt(f['max'])}] |")
    L += ["", res["D_geometry"]["note"], ""]
    return "\n".join(L)


def main() -> int:
    res = {
        "label": "exploratory (M4 confounder inspection); not confirmatory; no simulation run",
        "script": "scripts/m4_exploratory_confounders.py",
        "A_sign_consistency": part_a(),
        "B_listener_drift": part_b(),
        "C_skip_confounder": part_c(),
        "D_geometry": part_d(),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "confounders.json").write_text(json.dumps(res, indent=1, sort_keys=False) + "\n")
    (OUT / "confounders.md").write_text(markdown(res))
    print(f"wrote {OUT / 'confounders.json'} and confounders.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
