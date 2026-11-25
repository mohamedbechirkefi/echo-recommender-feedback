# SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
"""Confirmatory analysis exactly as frozen (protocol v1.0, sections 2, 5, 7, 10).

Written and committed before any confirmatory output existed (DEC-012). It
reads only validated result files and never changes them.

Frozen elements implemented here:

- Primary estimand: seed-level paired mean difference in drift, SIM minus
  RAND, adaptive preferences (EXP-002; EXP-004 on the FMA catalogue).
- 95 % percentile bootstrap over seeds, 10,000 resamples, bootstrap seed 7;
  paired t interval; d_z.
- Decision rule of section 2 with the section 10.2 item 4 reading
  (``stats.decide``), SESOI 0.05 rad.
- Negative control: drift exactly 0 for every listener under the fixed
  model; any non-zero value suspends the experiment.
- Failed runs counted per arm; stop rule (more than 10 % per arm).
- EXP-003 retain / withdraw / partially robust rule (EXP-003 item 4) and
  the oracle versus estimated sign check (protocol section 7).
- EXP-004 replicates / does not replicate / inconclusive reading
  (protocol 10.1).

Choices the frozen text leaves open are fixed in DEC-012 before any
confirmatory output: the Holm-adjusted interval construction and the
reading of "practically equivalent" in the EXP-003 and EXP-004 rules (both
readings are computed; a divergence is flagged for the owner).
"""

from __future__ import annotations

import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from .metrics import METRIC_NAMES
from .report import load_runs
from .schema import UNITS
from .stats import cohen_dz, decide, paired_t_ci

SESOI = 0.05  # rad, protocol section 2 (frozen)
ALPHA = 0.05
N_BOOT = 10_000
BOOT_SEED = 7
MAX_FAIL_FRACTION = 0.10
REFERENCE = "RAND"
DRIFT_FAMILY = ("SIM", "POP", "MMR", "EXPLORE")  # protocol section 5: the four drift contrasts vs RAND
POLICY_ORDER = ("RAND", "POP", "SIM", "MMR", "EXPLORE")


# ---------------------------------------------------------------- bootstrap


def boot_means(values, n_resamples: int = N_BOOT, seed: int = BOOT_SEED) -> np.ndarray:
    """Means of seed resamples; identical index draws to ``stats.paired_bootstrap_ci``."""
    a = np.asarray(values, dtype=np.float64).ravel()
    if a.size < 2 or not np.all(np.isfinite(a)):
        raise ValueError("need at least two finite values")
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, a.size, size=(n_resamples, a.size))
    return a[idx].mean(axis=1)


def percentile_ci(means: np.ndarray, level: float) -> tuple[float, float]:
    lo, hi = np.quantile(means, [(1 - level) / 2, 1 - (1 - level) / 2])
    return float(lo), float(hi)


def boot_p_value(means: np.ndarray) -> float:
    """Two-sided bootstrap p-value: 2 min(P(mean* <= 0), P(mean* >= 0)), capped at 1 (DEC-012)."""
    return float(min(1.0, 2.0 * min(np.mean(means <= 0.0), np.mean(means >= 0.0))))


def holm(pvalues: dict[str, float], alpha: float = ALPHA) -> dict[str, dict[str, float]]:
    """Holm step-down. Returns per key: rank, adjusted p, the interval level and rejection.

    The interval level for the contrast of rank i (1-based, ascending p) among
    m is 1 - alpha / (m - i + 1) (DEC-012). Rejection follows the step-down:
    stop at the first p above alpha / (m - i + 1).
    """
    keys = sorted(pvalues, key=lambda k: (pvalues[k], k))
    m = len(keys)
    out: dict[str, dict[str, float]] = {}
    running = 0.0
    still = True
    for i, k in enumerate(keys, start=1):
        running = max(running, min(1.0, (m - i + 1) * pvalues[k]))
        thresh = alpha / (m - i + 1)
        still = still and pvalues[k] <= thresh
        out[k] = {"rank": i, "p": pvalues[k], "p_holm": running, "level": 1 - thresh, "reject": still}
    return out


# ---------------------------------------------------------------- contrasts


def contrast(treat: list[float], ref: list[float], seeds: list[int]) -> dict[str, Any]:
    """Paired SIM-minus-RAND style contrast over seeds, as frozen."""
    if not (len(treat) == len(ref) == len(seeds)):
        raise ValueError("unpaired inputs")
    diffs = [t - r for t, r in zip(treat, ref)]
    means = boot_means(diffs)
    ci = percentile_ci(means, 1 - ALPHA)
    try:
        dz = cohen_dz(diffs)
    except ValueError:
        dz = float("nan")
    return {
        "n_seeds": len(diffs), "seeds": list(seeds), "treat": list(treat), "ref": list(ref), "diffs": diffs,
        "mean_diff": statistics.fmean(diffs), "sd_diff": statistics.stdev(diffs),
        "boot_ci95": list(ci), "t_ci95": [float(x) for x in paired_t_ci(diffs)], "d_z": dz,
        "p_boot": boot_p_value(means), "decision": decide(ci, SESOI),
        "ci_inside_sesoi_band": -SESOI <= ci[0] and ci[1] <= SESOI,
        "ci_excludes_zero": ci[0] > 0 or ci[1] < 0,
    }


def _ok(runs):
    return [r for r in runs if r["result"]["status"] == "ok"]


def paired_values(runs, metric: str, treat: str, ref: str = REFERENCE, where=None) -> tuple[list[int], list[float], list[float]]:
    """Per-seed values for two policies whose configs differ only in policy."""
    by: dict[str, dict[str, float]] = defaultdict(dict)
    for r in _ok(runs):
        res = r["result"]
        if where is not None and not where(res["config"]):
            continue
        cfg = dict(res["config"])
        pol = cfg.pop("policy")
        by[json.dumps(cfg, sort_keys=True)][pol] = res["metrics"][metric]
    rows = sorted((json.loads(k)["seed"], v[treat], v[ref]) for k, v in by.items() if treat in v and ref in v)
    return [s for s, _, _ in rows], [t for _, t, _ in rows], [r for _, _, r in rows]


def holm_intervals(contrasts: dict[str, dict[str, Any]]) -> None:
    """Add Holm fields and Holm-level bootstrap intervals to each contrast, in place."""
    h = holm({k: c["p_boot"] for k, c in contrasts.items()})
    for k, c in contrasts.items():
        means = boot_means(c["diffs"])
        c["holm"] = {**h[k], "ci": list(percentile_ci(means, h[k]["level"])), "family_size": len(contrasts)}


# ---------------------------------------------------------------- integrity


def integrity(runs, planned: int) -> dict[str, Any]:
    """Failed runs per arm, stop rule, and the fixed-model negative control."""
    per_arm: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for r in runs:
        arm = r["result"]["run_id"].rsplit("_s", 1)[0]
        per_arm[arm][0] += 1
        per_arm[arm][1] += r["result"]["status"] != "ok"
    stop = sorted(a for a, (n, f) in per_arm.items() if f > MAX_FAIL_FRACTION * n)
    fixed = [r for r in _ok(runs) if r["result"]["config"]["preference_model"] == "fixed"]
    nonzero = [r["result"]["run_id"] for r in fixed if any(v != 0.0 for v in r["result"]["per_user"]["drift_rad"])]
    return {
        "planned_runs": planned, "result_files": len(runs),
        "failed_runs": sum(f for _, f in per_arm.values()),
        "failed_by_arm": {a: f for a, (_, f) in sorted(per_arm.items()) if f},
        "stop_rule_arms": stop,
        "negative_control": {"fixed_runs_checked": len(fixed), "runs_with_nonzero_drift": nonzero,
                             "pass": bool(fixed) and not nonzero} if fixed else None,
        "complete": len(runs) == planned,
    }


def arm_summaries(runs) -> list[dict[str, Any]]:
    """Descriptive seed-level means with 95 % percentile bootstrap CIs, every metric, every arm."""
    groups: dict[tuple, list] = defaultdict(list)
    for r in _ok(runs):
        c = r["result"]["config"]
        groups[(c["policy"], c["preference_model"], c["update_rule"], c["eta"], c["profile"])].append(r)
    rows = []
    for key in sorted(groups, key=lambda k: (k[1], k[2], k[3], k[4], POLICY_ORDER.index(k[0]))):
        rs = groups[key]
        row = {"policy": key[0], "preference_model": key[1], "update_rule": key[2], "eta": key[3], "profile": key[4],
               "n_seeds": len(rs)}
        for m in METRIC_NAMES:
            vals = [r["result"]["metrics"][m] for r in rs]
            mean = statistics.fmean(vals)
            ci = percentile_ci(boot_means(vals), 1 - ALPHA) if len(vals) > 1 and len(set(vals)) > 1 else (mean, mean)
            row[m] = {"mean": mean, "ci95": list(ci)}
        rows.append(row)
    return rows


# ---------------------------------------------------------------- experiments


def analyse_policy_matrix(runs, planned: int) -> dict[str, Any]:
    """EXP-002 and EXP-004: primary contrast, Holm family, secondaries."""
    adaptive = lambda c: c["preference_model"] == "adaptive"  # noqa: E731
    family = {}
    for pol in DRIFT_FAMILY:
        seeds, t, r = paired_values(runs, "drift_rad", pol, where=adaptive)
        if len(seeds) >= 2:
            family[f"{pol}-{REFERENCE}"] = contrast(t, r, seeds)
    holm_intervals(family)
    seeds, t, r = paired_values(runs, "drift_per_accept_rad", "SIM", where=adaptive)
    per_accept = contrast(t, r, seeds) if len(seeds) >= 2 else None
    if per_accept is not None:
        # The SESOI band is in rad; this contrast is in rad per accepted track, so no SESOI label applies
        # (evidence-audit finding F-3, fixed under DEC-016).
        for k in ("decision", "ci_inside_sesoi_band"):
            per_accept.pop(k)
    secondary_vs_rand = {}
    for pref in ("fixed", "adaptive"):
        for pol in DRIFT_FAMILY:
            for m in METRIC_NAMES:
                if m in ("drift_rad", "drift_per_accept_rad") and pref == "fixed":
                    continue
                s, t, r = paired_values(runs, m, pol, where=lambda c, p=pref: c["preference_model"] == p)
                if len(s) >= 2 and len({a - b for a, b in zip(t, r)}) > 1:
                    d = [a - b for a, b in zip(t, r)]
                    secondary_vs_rand[f"{pref}/{pol}-{REFERENCE}/{m}"] = {
                        "mean_diff": statistics.fmean(d), "ci95": list(percentile_ci(boot_means(d), 1 - ALPHA)), "n_seeds": len(d)}
    primary = family.get(f"SIM-{REFERENCE}")
    return {
        "integrity": integrity(runs, planned),
        "primary": primary,
        "drift_family": family,
        "drift_per_accept_SIM-RAND": per_accept,
        "secondary_vs_rand_descriptive": secondary_vs_rand,
        "arms": arm_summaries(runs),
    }


def analyse_sensitivity(runs, planned: int, exp002_primary: dict[str, Any] | None) -> dict[str, Any]:
    """EXP-003: per-cell SIM-RAND drift contrasts and the frozen robustness rule."""
    cells: dict[str, dict[str, Any]] = {}
    keys = sorted({(r["result"]["config"]["update_rule"], r["result"]["config"]["eta"], r["result"]["config"]["profile"]) for r in _ok(runs)})
    for rule, eta, prof in keys:
        s, t, r = paired_values(runs, "drift_rad", "SIM",
                                where=lambda c, a=rule, b=eta, d=prof: (c["update_rule"], c["eta"], c["profile"]) == (a, b, d))
        if len(s) >= 2:
            c = contrast(t, r, s)
            c.update({"update_rule": rule, "eta": eta, "profile": prof})
            for m in ("homogenisation", "skip_rate"):
                s2, t2, r2 = paired_values(runs, m, "SIM",
                                           where=lambda c_, a=rule, b=eta, d=prof: (c_["update_rule"], c_["eta"], c_["profile"]) == (a, b, d))
                d2 = [a - b for a, b in zip(t2, r2)]
                c[f"{m}_diff_mean"] = statistics.fmean(d2)
                c[f"{m}_diff_ci95"] = list(percentile_ci(boot_means(d2), 1 - ALPHA)) if len(set(d2)) > 1 else [d2[0], d2[0]]
            cells[f"{rule}/eta={eta}/{prof}"] = c
    holm_intervals(cells)
    verdict = robustness_verdict(cells, exp002_primary)
    sign_check = []
    for rule, eta in sorted({(c["update_rule"], c["eta"]) for c in cells.values()}):
        e, o = cells.get(f"{rule}/eta={eta}/estimated"), cells.get(f"{rule}/eta={eta}/oracle")
        if e and o:
            sign_check.append({
                "update_rule": rule, "eta": eta, "estimated_mean": e["mean_diff"], "oracle_mean": o["mean_diff"],
                "point_signs_differ": np.sign(e["mean_diff"]) != np.sign(o["mean_diff"]),
                "both_ci_exclude_zero_opposite_signs": bool(e["ci_excludes_zero"] and o["ci_excludes_zero"]
                                                            and np.sign(e["mean_diff"]) != np.sign(o["mean_diff"])),
            })
    for s in sign_check:
        s["point_signs_differ"] = bool(s["point_signs_differ"])
    return {"integrity": integrity(runs, planned), "cells": cells, "verdict": verdict,
            "oracle_vs_estimated_sign_check": sign_check, "arms": arm_summaries(runs)}


def _sign(x: float) -> int:
    return 1 if x > 0 else (-1 if x < 0 else 0)


def robustness_verdict(cells: dict[str, dict[str, Any]], ref: dict[str, Any] | None) -> dict[str, Any]:
    """EXP-003 item 4. Two readings of "practically equivalent" (DEC-012):

    - band: the 95 % CI lies inside [-SESOI, SESOI] (section 2 wording before 10.2 item 4);
    - label: the decision label is exactly "practically equivalent" (CI inside the band and including 0).
    """
    if ref is None:
        return {"verdict": "not computable: EXP-002 primary missing"}
    ref_sign = _sign(ref["mean_diff"])

    def one(reading: str) -> dict[str, Any]:
        def equivalent(c):
            return c["ci_inside_sesoi_band"] if reading == "band" else c["decision"] == "practically equivalent"
        withdraw = [k for k, c in cells.items() if c["eta"] == 0.05 and (
            (c["ci_excludes_zero"] and _sign(c["mean_diff"]) == -ref_sign) or equivalent(c))]
        retain_cells = [c for c in cells.values() if c["eta"] >= 0.05]
        retained = bool(retain_cells) and all(_sign(c["mean_diff"]) == ref_sign and c["ci_excludes_zero"] for c in retain_cells)
        if withdraw:
            v = "withdrawn as assumption-dependent"
        elif retained:
            v = "retained"
        else:
            v = "partially robust"
        return {"verdict": v, "withdraw_triggering_cells": withdraw,
                "cells_failing_retain": [k for k, c in cells.items() if c["eta"] >= 0.05
                                         and not (_sign(c["mean_diff"]) == ref_sign and c["ci_excludes_zero"])]}

    band, label = one("band"), one("label")
    return {"reference_EXP-002_mean_diff": ref["mean_diff"], "band_reading": band, "label_reading": label,
            "readings_agree": band["verdict"] == label["verdict"],
            "verdict": band["verdict"] if band["verdict"] == label["verdict"] else "readings disagree: owner decision needed"}


def replication_reading(fma: dict[str, Any] | None, ref: dict[str, Any] | None) -> dict[str, Any]:
    """Protocol 10.1 reading of EXP-004 against EXP-002, under both equivalence readings (DEC-012)."""
    if fma is None or ref is None:
        return {"reading": "not computable"}

    def one(equivalent: bool) -> str:
        same = _sign(fma["mean_diff"]) == _sign(ref["mean_diff"])
        if fma["ci_excludes_zero"] and not same:
            return "does not replicate"
        if equivalent:
            return "does not replicate"
        if fma["ci_excludes_zero"] and same:
            return "replicates on the real catalogue"
        return "inconclusive on the real catalogue"

    band = one(fma["ci_inside_sesoi_band"])
    label = one(fma["decision"] == "practically equivalent")
    return {"band_reading": band, "label_reading": label, "readings_agree": band == label,
            "reading": band if band == label else "readings disagree: owner decision needed"}


# ---------------------------------------------------------------- outputs


def _f(x: float, d: int = 4) -> str:
    return "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{d}f}"


def write_tables(analysis: dict[str, Any], out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "arms.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["policy", "preference_model", "update_rule", "eta", "profile", "n_seeds"]
                   + [f"{m}_{s}" for m in METRIC_NAMES for s in ("mean", "ci_lo", "ci_hi")])
        for a in analysis["arms"]:
            w.writerow([a["policy"], a["preference_model"], a["update_rule"], a["eta"], a["profile"], a["n_seeds"]]
                       + [repr(v) for m in METRIC_NAMES for v in (a[m]["mean"], *a[m]["ci95"])])
    contrasts = analysis.get("drift_family") or analysis.get("cells") or {}
    with open(out / "contrasts.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["contrast", "n_seeds", "mean_diff_rad", "sd_diff_rad", "boot_ci_lo", "boot_ci_hi", "t_ci_lo", "t_ci_hi",
                    "d_z", "p_boot", "decision", "holm_rank", "holm_p", "holm_level", "holm_ci_lo", "holm_ci_hi", "holm_reject"])
        for k, c in contrasts.items():
            w.writerow([k, c["n_seeds"], repr(c["mean_diff"]), repr(c["sd_diff"]), *map(repr, c["boot_ci95"]), *map(repr, c["t_ci95"]),
                        repr(c["d_z"]), repr(c["p_boot"]), c["decision"], c["holm"]["rank"], repr(c["holm"]["p_holm"]),
                        repr(c["holm"]["level"]), *map(repr, c["holm"]["ci"]), c["holm"]["reject"]])
    with open(out / "per_seed.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["contrast", "seed", "treat_drift_rad", "ref_drift_rad", "diff_rad"])
        for k, c in contrasts.items():
            for s, t, r, d in zip(c["seeds"], c["treat"], c["ref"], c["diffs"]):
                w.writerow([k, s, repr(t), repr(r), repr(d)])


def forest_svg(contrasts: dict[str, dict[str, Any]], title: str, path: Path, subtitle: str) -> None:
    """Forest plot: point estimate, 95 % bootstrap CI (thick), Holm-level CI (thin), SESOI band."""
    names = list(contrasts)
    w, row_h, ml, mr, mt, mb = 760, 26, 230, 30, 64, 70
    h = mt + mb + row_h * len(names)
    lo = min(min(c["holm"]["ci"][0], c["boot_ci95"][0]) for c in contrasts.values())
    hi = max(max(c["holm"]["ci"][1], c["boot_ci95"][1]) for c in contrasts.values())
    lo, hi = min(lo, -SESOI, 0.0), max(hi, SESOI, 0.0)
    pad = (hi - lo) * 0.06
    lo, hi = lo - pad, hi + pad

    def x(v: float) -> float:
        return ml + (v - lo) * (w - ml - mr) / (hi - lo)

    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="t d">',
         f'<title id="t">{title}</title>',
         f'<desc id="d">Forest plot of paired seed-level drift differences (radians) versus RAND. Dots: mean over {next(iter(contrasts.values()))["n_seeds"]} seeds. '
         'Thick bars: 95 % percentile bootstrap CI. Thin bars: Holm-level bootstrap CI. Shaded band: SESOI plus or minus 0.05 rad. Dashed line: zero.</desc>',
         f'<rect width="{w}" height="{h}" fill="#ffffff"/>',
         f'<text x="12" y="22" font-family="serif" font-size="15" fill="#222">{title}</text>',
         f'<text x="12" y="42" font-family="sans-serif" font-size="11" fill="#444">{subtitle}</text>',
         f'<rect x="{x(-SESOI):.1f}" y="{mt - 6}" width="{x(SESOI) - x(-SESOI):.1f}" height="{row_h * len(names) + 6}" fill="#eeeeee"/>',
         f'<line x1="{x(0):.1f}" y1="{mt - 6}" x2="{x(0):.1f}" y2="{mt + row_h * len(names)}" stroke="#555" stroke-dasharray="4 3"/>']
    for k in range(6):
        v = lo + k * (hi - lo) / 5
        yb = mt + row_h * len(names)
        p.append(f'<line x1="{x(v):.1f}" y1="{yb}" x2="{x(v):.1f}" y2="{yb + 4}" stroke="#444"/>')
        p.append(f'<text x="{x(v):.1f}" y="{yb + 17}" text-anchor="middle" font-family="sans-serif" font-size="10" fill="#333">{v:.3f}</text>')
    for i, n in enumerate(names):
        c = contrasts[n]
        y = mt + row_h * i + row_h / 2
        p.append(f'<text x="{ml - 8}" y="{y + 4:.1f}" text-anchor="end" font-family="sans-serif" font-size="11" fill="#222">{n}</text>')
        p.append(f'<line x1="{x(c["holm"]["ci"][0]):.1f}" y1="{y:.1f}" x2="{x(c["holm"]["ci"][1]):.1f}" y2="{y:.1f}" stroke="#7a7a7a" stroke-width="1"/>')
        p.append(f'<line x1="{x(c["boot_ci95"][0]):.1f}" y1="{y:.1f}" x2="{x(c["boot_ci95"][1]):.1f}" y2="{y:.1f}" stroke="#1f4e79" stroke-width="4"/>')
        p.append(f'<circle cx="{x(c["mean_diff"]):.1f}" cy="{y:.1f}" r="4.5" fill="#b5523b"/>')
    yb = mt + row_h * len(names)
    p.append(f'<text x="{(ml + w - mr) / 2}" y="{yb + 36}" text-anchor="middle" font-family="sans-serif" font-size="11" fill="#333">'
             'paired difference in mean angular drift vs RAND (rad)</text>')
    p.append(f'<text x="{ml}" y="{yb + 56}" font-family="sans-serif" font-size="10" fill="#444">thick: 95 % bootstrap CI; thin: Holm-level CI; '
             'grey band: SESOI 0.05 rad; dashed: 0</text>')
    p.append("</svg>\n")
    path.write_text("\n".join(p), encoding="utf-8")


def arms_svg(analysis: dict[str, Any], title: str, path: Path) -> None:
    """Per-policy mean drift with 95 % bootstrap CI, adaptive arms (fixed arms are exactly 0)."""
    arms = [a for a in analysis["arms"] if a["preference_model"] == "adaptive"]
    w, h, ml, mr, mt, mb = 640, 340, 70, 20, 50, 60
    hi = max(a["drift_rad"]["ci95"][1] for a in arms) * 1.1
    n = len(arms)

    def x(i: int) -> float:
        return ml + (i + 0.5) * (w - ml - mr) / n

    def y(v: float) -> float:
        return mt + (hi - v) * (h - mt - mb) / hi

    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="t d">',
         f'<title id="t">{title}</title>',
         f'<desc id="d">Mean angular drift (radians) per policy under adaptive preferences, mean over {arms[0]["n_seeds"]} seeds, '
         'with 95 % percentile bootstrap CI over seeds. Fixed-preference arms have drift exactly 0 and are not drawn.</desc>',
         f'<rect width="{w}" height="{h}" fill="#ffffff"/>',
         f'<text x="12" y="24" font-family="serif" font-size="15" fill="#222">{title}</text>',
         f'<line x1="{ml}" y1="{mt}" x2="{ml}" y2="{h - mb}" stroke="#444"/>',
         f'<line x1="{ml}" y1="{h - mb}" x2="{w - mr}" y2="{h - mb}" stroke="#444"/>']
    for k in range(5):
        v = k * hi / 4
        p.append(f'<text x="{ml - 8}" y="{y(v) + 4:.1f}" text-anchor="end" font-family="sans-serif" font-size="10" fill="#333">{v:.2f}</text>')
        p.append(f'<line x1="{ml}" y1="{y(v):.1f}" x2="{w - mr}" y2="{y(v):.1f}" stroke="#e5e5e5"/>')
    for i, a in enumerate(arms):
        m, (l, u) = a["drift_rad"]["mean"], a["drift_rad"]["ci95"]
        p.append(f'<rect x="{x(i) - 22:.1f}" y="{y(m):.1f}" width="44" height="{y(0) - y(m):.1f}" fill="#9db7d5"/>')
        p.append(f'<line x1="{x(i):.1f}" y1="{y(l):.1f}" x2="{x(i):.1f}" y2="{y(u):.1f}" stroke="#1f2f4f" stroke-width="2"/>')
        p.append(f'<text x="{x(i):.1f}" y="{h - mb + 16}" text-anchor="middle" font-family="sans-serif" font-size="11" fill="#222">{a["policy"]}</text>')
    p.append(f'<text x="18" y="{(mt + h - mb) / 2}" transform="rotate(-90 18 {(mt + h - mb) / 2})" text-anchor="middle" '
             'font-family="sans-serif" font-size="11" fill="#333">mean drift (rad)</text>')
    p.append("</svg>\n")
    path.write_text("\n".join(p), encoding="utf-8")


def markdown(exp_id: str, a: dict[str, Any]) -> str:
    """Generated tables for the experiment report (numbers only from ``a``)."""
    L = ["<!-- SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0 -->",
         f"# {exp_id} confirmatory analysis (generated by `echo.analysis`)", "",
         "Simulation outputs within the model assumptions of `research/protocol.md`. Numbers come from the result files "
         "via `analysis.json`; nothing is typed by hand.", ""]
    it = a["integrity"]
    L += ["## Integrity", "",
          f"- Result files: {it['result_files']} of {it['planned_runs']} planned; failed runs: {it['failed_runs']}; "
          f"stop-rule arms: {it['stop_rule_arms'] or 'none'}."]
    if it.get("negative_control"):
        nc = it["negative_control"]
        L.append(f"- Negative control (fixed model, drift exactly 0 for every listener): {'PASS' if nc['pass'] else 'FAIL'} "
                 f"over {nc['fixed_runs_checked']} runs.")
    L.append("")
    contrasts = a.get("drift_family") or a.get("cells")
    L += ["## Drift contrasts vs RAND (seed-paired, rad)", "",
          "| Contrast | n | Mean diff | SD | 95 % bootstrap CI | 95 % paired t CI | d_z | p (boot) | Decision | Holm level | Holm CI | Holm reject |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for k, c in contrasts.items():
        L.append(f"| {k} | {c['n_seeds']} | {_f(c['mean_diff'])} | {_f(c['sd_diff'])} | [{_f(c['boot_ci95'][0])}, {_f(c['boot_ci95'][1])}] | "
                 f"[{_f(c['t_ci95'][0])}, {_f(c['t_ci95'][1])}] | {_f(c['d_z'], 2)} | {_f(c['p_boot'])} | {c['decision']} | "
                 f"{_f(c['holm']['level'], 4)} | [{_f(c['holm']['ci'][0])}, {_f(c['holm']['ci'][1])}] | {'yes' if c['holm']['reject'] else 'no'} |")
    L.append("")
    if a.get("primary"):
        pr = a["primary"]
        L += ["## Primary estimand", "",
              f"Delta (SIM minus RAND, adaptive) = {_f(pr['mean_diff'])} rad, 95 % percentile bootstrap CI "
              f"[{_f(pr['boot_ci95'][0])}, {_f(pr['boot_ci95'][1])}] (10,000 resamples, seed 7), paired t CI "
              f"[{_f(pr['t_ci95'][0])}, {_f(pr['t_ci95'][1])}], d_z = {_f(pr['d_z'], 2)}, n = {pr['n_seeds']} seeds. "
              f"Decision under the frozen rule: **{pr['decision']}**.", ""]
    if a.get("drift_per_accept_SIM-RAND"):
        c = a["drift_per_accept_SIM-RAND"]
        L += [f"Pre-specified secondary, drift per accepted item, SIM minus RAND: {_f(c['mean_diff'], 6)} rad per accepted track, "
              f"95 % CI [{_f(c['boot_ci95'][0], 6)}, {_f(c['boot_ci95'][1], 6)}].", ""]
    if a.get("verdict"):
        v = a["verdict"]
        L += ["## Robustness verdict (EXP-003 item 4)", "",
              f"- Reading with equivalence as 'CI inside the SESOI band': **{v['band_reading']['verdict']}**; "
              f"cells triggering withdrawal: {v['band_reading']['withdraw_triggering_cells'] or 'none'}; "
              f"cells failing the retain condition: {v['band_reading']['cells_failing_retain'] or 'none'}.",
              f"- Reading with equivalence as the label 'practically equivalent': **{v['label_reading']['verdict']}**.",
              f"- Readings agree: {v['readings_agree']}. Verdict: **{v['verdict']}**.", "",
              "### Oracle versus estimated profile (protocol section 7, second check)", "",
              "| Rule | eta | Estimated mean diff | Oracle mean diff | Point signs differ | Both CIs exclude 0 with opposite signs |",
              "|---|---|---|---|---|---|"]
        for s in a["oracle_vs_estimated_sign_check"]:
            L.append(f"| {s['update_rule']} | {s['eta']} | {_f(s['estimated_mean'])} | {_f(s['oracle_mean'])} | "
                     f"{'yes' if s['point_signs_differ'] else 'no'} | {'yes' if s['both_ci_exclude_zero_opposite_signs'] else 'no'} |")
        L.append("")
    if a.get("replication"):
        r = a["replication"]
        L += ["## Reading against EXP-002 (protocol 10.1)", "",
              f"- Band reading: **{r['band_reading']}**; label reading: **{r['label_reading']}**; agree: {r['readings_agree']}. "
              f"Reading: **{r['reading']}**.", ""]
    show = ["drift_rad", "homogenisation", "discovery", "novelty_bits", "diversity_ild", "relevance_initial",
            "relevance_current", "exposure_gini", "skip_rate", "drift_per_accept_rad"]
    L += ["## Per-arm seed-level means with 95 % bootstrap CIs (descriptive)", ""]
    multi = len({(x["update_rule"], x["eta"], x["profile"]) for x in a["arms"]}) > 1
    for m in show:
        L += [f"### {m} ({UNITS[m]})", "", "| Arm | n | Mean | 95 % CI |", "|---|---|---|---|"]
        for x in a["arms"]:
            arm = f"{x['policy']} {x['preference_model']}" + (f" {x['update_rule']} eta={x['eta']} {x['profile']}" if multi else "")
            L.append(f"| {arm} | {x['n_seeds']} | {_f(x[m]['mean'])} | [{_f(x[m]['ci95'][0])}, {_f(x[m]['ci95'][1])}] |")
        L.append("")
    return "\n".join(L) + "\n"


def _jsonable(o):
    if isinstance(o, dict):
        return {k: _jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_jsonable(v) for v in o]
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, float) and math.isnan(o):
        return None
    return o


def run_analysis(results_dir: Path, planned: int, kind: str, reference: Path | None = None) -> dict[str, Any]:
    """Analyse one experiment directory and write ``<dir>/analysis/``.

    kind: "policy" (EXP-002), "sensitivity" (EXP-003, needs reference = EXP-002 analysis.json),
    "replication" (EXP-004, needs reference = EXP-002 analysis.json).
    """
    runs = load_runs(results_dir)
    exp_ids = {r["result"]["experiment_id"] for r in runs}
    labels = {r["result"]["label"] for r in runs}
    if len(exp_ids) != 1 or labels != {"confirmatory"}:
        raise ValueError(f"expected one confirmatory experiment in {results_dir}, got {exp_ids} {labels}")
    exp_id = exp_ids.pop()
    ref = json.loads(Path(reference).read_text(encoding="utf-8"))["primary"] if reference else None
    if kind == "policy":
        a = analyse_policy_matrix(runs, planned)
    elif kind == "replication":
        a = analyse_policy_matrix(runs, planned)
        a["replication"] = replication_reading(a["primary"], ref)
    elif kind == "sensitivity":
        a = analyse_sensitivity(runs, planned, ref)
    else:
        raise ValueError(f"unknown kind {kind}")
    revs = sorted({r["manifest"]["git"]["revision"] or "unknown" for r in runs})
    dirty = sorted({str(r["manifest"]["git"]["code_dirty"]) for r in runs})
    a = _jsonable({"experiment_id": exp_id, "kind": kind, "sesoi_rad": SESOI, "n_boot": N_BOOT, "boot_seed": BOOT_SEED,
                   "code_revisions": revs, "code_dirty": dirty, **a})
    out = results_dir / "analysis"
    out.mkdir(parents=True, exist_ok=True)
    (out / "analysis.json").write_text(json.dumps(a, sort_keys=True, indent=1) + "\n", encoding="utf-8")
    write_tables(a, out)
    contrasts = a.get("drift_family") or a.get("cells")
    forest_svg(contrasts, f"{exp_id}: drift contrasts vs RAND (confirmatory)", out / "fig-contrasts.svg",
               f"Seed-paired differences, n = {next(iter(contrasts.values()))['n_seeds']} seeds; simulation only")
    if kind in ("policy", "replication"):
        arms_svg(a, f"{exp_id}: mean drift per policy, adaptive (confirmatory)", out / "fig-arms-drift.svg")
    (out / "analysis.md").write_text(markdown(exp_id, a), encoding="utf-8")
    return a


def main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(prog="echo.analysis")
    p.add_argument("results_dir")
    p.add_argument("--planned", type=int, required=True)
    p.add_argument("--kind", choices=("policy", "sensitivity", "replication"), required=True)
    p.add_argument("--reference", default=None, help="EXP-002 analysis.json (for sensitivity and replication)")
    args = p.parse_args(argv)
    a = run_analysis(Path(args.results_dir), args.planned, args.kind, Path(args.reference) if args.reference else None)
    print(json.dumps({"experiment_id": a["experiment_id"], "integrity": a["integrity"],
                      "primary": {k: a["primary"][k] for k in ("mean_diff", "boot_ci95", "decision")} if a.get("primary") else None,
                      "verdict": a.get("verdict", {}).get("verdict"), "replication": a.get("replication", {}).get("reading")}, indent=1))
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
