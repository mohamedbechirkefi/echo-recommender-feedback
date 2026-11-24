# SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
"""Report generator: tables, figures and PDF built only from result files.

Every result file is re-validated on import (fail closed). Tables and the
figure are written once into ``<results dir>/report/`` and are meant to be
reused by reports, the manuscript and the demo.

PDF route (DEC-003): pandoc -> Typst with -V mainfont="Libertinus Serif",
compiled with the typst Python package of the shared tools interpreter.
If either tool is missing, the PDF is skipped and the reason is returned.
"""

from __future__ import annotations

import csv
import json
import math
import os
import statistics
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any

from .manifest import REPO_ROOT
from .metrics import METRIC_NAMES
from .runner import expand, load_experiment
from .schema import UNITS, read_result
from .stats import projected_half_width

TOOLS = Path(os.environ.get("ECHO_TOOLS", REPO_ROOT.parent / ".tools"))
SESOI = 0.05  # rad, draft protocol section 2 (owner to confirm)


def load_runs(results_dir: Path) -> list[dict[str, Any]]:
    files = sorted((results_dir / "runs").glob("*.json"))
    if not files:
        raise FileNotFoundError(f"no result files under {results_dir / 'runs'}")
    out = []
    for f in files:
        res = read_result(f)
        mpath = results_dir / "manifests" / f"{res['run_id']}.manifest.json"
        if not mpath.exists():
            raise FileNotFoundError(f"missing manifest for {res['run_id']}")
        man = json.loads(mpath.read_text(encoding="utf-8"))
        if man.get("config_hash") != res["config_hash"]:
            raise ValueError(f"manifest config hash mismatch for {res['run_id']}")
        out.append({"result": res, "manifest": man, "path": f})
    return out


def arm_key(res: dict[str, Any]) -> str:
    return res["run_id"].rsplit("_s", 1)[0]


def _fmt(v: float, digits: int = 4) -> str:
    return "n/a" if v is None or (isinstance(v, float) and math.isnan(v)) else f"{v:.{digits}f}"


def metrics_csv(runs: list[dict[str, Any]], path: Path) -> None:
    cols = ["run_id", "block", "policy", "preference_model", "update_rule", "profile", "eta", "seed", "status",
            "runtime_s", "config_hash"] + list(METRIC_NAMES) + ["users_without_accept"]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for r in runs:
            res, cfg = r["result"], r["result"]["config"]
            m = res["metrics"] or {}
            row = [res["run_id"], res["block"], cfg["policy"], cfg["preference_model"], cfg["update_rule"],
                   cfg["profile"], cfg["eta"], res["seed"], res["status"], f"{r['manifest']['runtime_s']:.4f}",
                   res["config_hash"]] + [repr(m.get(k)) if k in m else "" for k in METRIC_NAMES]
            row.append((res["diagnostics"] or {}).get("users_without_accept", ""))
            w.writerow(row)


def arm_table(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list] = defaultdict(list)
    for r in runs:
        groups[arm_key(r["result"])].append(r)
    rows = []
    for key in sorted(groups):
        rs = groups[key]
        ok = [r for r in rs if r["result"]["status"] == "ok"]
        row = {"arm": key, "n_runs": len(rs), "n_ok": len(ok)}
        for name in METRIC_NAMES:
            vals = [r["result"]["metrics"][name] for r in ok]
            row[name] = (statistics.fmean(vals) if vals else float("nan"),
                         statistics.stdev(vals) if len(vals) > 1 else float("nan"))
        row["runtime_s"] = statistics.fmean(r["manifest"]["runtime_s"] for r in rs)
        rows.append(row)
    return rows


def paired_drift(runs: list[dict[str, Any]], block: str, treat: str = "SIM", ref: str = "RAND") -> dict[str, Any] | None:
    """Per-seed SIM minus RAND drift for runs of one block that differ only in policy."""
    by: dict[tuple, dict[str, float]] = defaultdict(dict)
    for r in runs:
        res = r["result"]
        if res["block"] != block or res["status"] != "ok":
            continue
        cfg = dict(res["config"])
        pol = cfg.pop("policy")
        by[json.dumps(cfg, sort_keys=True)][pol] = res["metrics"]["drift_rad"]
    pairs = [(json.loads(k)["seed"], v[treat], v[ref]) for k, v in by.items() if treat in v and ref in v]
    if len(pairs) < 2:
        return None
    pairs.sort()
    diffs = [t - r for _, t, r in pairs]
    sd = statistics.stdev(diffs)
    return {
        "block": block, "n_seeds": len(pairs), "seeds": [p[0] for p in pairs],
        "treat": [p[1] for p in pairs], "ref": [p[2] for p in pairs], "diffs": diffs,
        "mean_diff": statistics.fmean(diffs), "sd_diff": sd,
        "projected_half_width": {n: projected_half_width(sd, n) for n in (5, 10, 20, 30)},
    }


def runtime_projection(runs: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Project EXP-002 and EXP-003 wall-clock from full-size exploratory runtimes."""
    full = [r for r in runs if r["result"]["config"]["n_users"] == 200 and r["result"]["config"]["n_tracks"] == 1000
            and r["result"]["config"]["n_steps"] == 100]
    if not full:
        return None
    by_pol: dict[str, list[float]] = defaultdict(list)
    for r in full:
        by_pol[r["result"]["config"]["policy"]].append(r["manifest"]["runtime_s"])
    mean_pol = {p: statistics.fmean(v) for p, v in by_pol.items()}
    proj = {}
    for exp_id in ("EXP-002", "EXP-003"):
        cpath = REPO_ROOT / "experiments" / exp_id / "config.json"
        if not cpath.exists():
            continue
        planned = expand(load_experiment(cpath))
        missing = sorted({p.config.policy for p in planned} - set(mean_pol))
        if missing:
            proj[exp_id] = {"runs": len(planned), "seconds": None, "note": f"no timing for {missing}"}
            continue
        secs = sum(mean_pol[p.config.policy] for p in planned)
        proj[exp_id] = {"runs": len(planned), "seconds": secs}
    return {"mean_runtime_s_by_policy": mean_pol, "n_timed_runs": {p: len(v) for p, v in by_pol.items()}, "projection": proj}


def pilot_figure(pd: dict[str, Any], path: Path) -> None:
    """SVG: per-seed drift under RAND and SIM, paired by seed (exploratory pilot)."""
    w, h, ml, mr, mt, mb = 640, 360, 70, 20, 40, 60
    vals = pd["treat"] + pd["ref"]
    lo, hi = min(vals), max(vals)
    pad = (hi - lo) * 0.1 or 0.01
    lo, hi = lo - pad, hi + pad
    n = pd["n_seeds"]

    def x(i: int) -> float:
        return ml + (i + 0.5) * (w - ml - mr) / n

    def y(v: float) -> float:
        return mt + (hi - v) * (h - mt - mb) / (hi - lo)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" '
        f'aria-labelledby="t d"><title id="t">Exploratory pilot: per-seed drift, RAND and SIM</title>'
        f'<desc id="d">For each of {n} exploratory seeds, mean angular drift in radians under RAND (circles) '
        f'and SIM (squares), joined by a line. Exploratory planning data, not a finding.</desc>',
        f'<rect width="{w}" height="{h}" fill="#ffffff"/>',
        f'<text x="{ml}" y="22" font-family="serif" font-size="14" fill="#222">EXPLORATORY pilot (EXP-001): mean drift per seed (rad)</text>',
        f'<line x1="{ml}" y1="{mt}" x2="{ml}" y2="{h - mb}" stroke="#444"/>',
        f'<line x1="{ml}" y1="{h - mb}" x2="{w - mr}" y2="{h - mb}" stroke="#444"/>',
    ]
    for k in range(5):
        v = lo + k * (hi - lo) / 4
        parts.append(f'<text x="{ml - 8}" y="{y(v) + 4:.1f}" text-anchor="end" font-family="sans-serif" font-size="11" fill="#333">{v:.3f}</text>')
        parts.append(f'<line x1="{ml}" y1="{y(v):.1f}" x2="{w - mr}" y2="{y(v):.1f}" stroke="#e5e5e5"/>')
    for i in range(n):
        xr, xs = x(i) - 6, x(i) + 6
        parts.append(f'<line x1="{xr:.1f}" y1="{y(pd["ref"][i]):.1f}" x2="{xs:.1f}" y2="{y(pd["treat"][i]):.1f}" stroke="#999"/>')
        parts.append(f'<circle cx="{xr:.1f}" cy="{y(pd["ref"][i]):.1f}" r="4" fill="#3a6ea5"/>')
        parts.append(f'<rect x="{xs - 4:.1f}" y="{y(pd["treat"][i]) - 4:.1f}" width="8" height="8" fill="#b5523b"/>')
        parts.append(f'<text x="{x(i):.1f}" y="{h - mb + 16}" text-anchor="middle" font-family="sans-serif" font-size="10" fill="#333">{pd["seeds"][i] - 900000}</text>')
    parts.append(f'<text x="{(ml + w - mr) / 2}" y="{h - 18}" text-anchor="middle" font-family="sans-serif" font-size="11" fill="#333">exploratory seed (offset from 900000)</text>')
    parts.append(f'<circle cx="{w - 190}" cy="{mt + 6}" r="4" fill="#3a6ea5"/><text x="{w - 180}" y="{mt + 10}" font-family="sans-serif" font-size="11">RAND</text>')
    parts.append(f'<rect x="{w - 124}" y="{mt + 2}" width="8" height="8" fill="#b5523b"/><text x="{w - 110}" y="{mt + 10}" font-family="sans-serif" font-size="11">SIM</text>')
    parts.append("</svg>\n")
    path.write_text("\n".join(parts), encoding="utf-8")


def build_markdown(exp_id: str, label: str, runs, arms, pilot, timing, checks, screen=None) -> str:
    revs = sorted({r["manifest"]["git"]["revision"] or "unknown" for r in runs})
    lines = [
        "<!-- SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0 -->",
        f"# {exp_id} generated summary ({label.upper()})",
        "",
        f"**Label: {label}.** " + ("This is an exploratory run made while the protocol is unfrozen. "
                                     "Nothing here is a finding; values serve planning only." if label == "exploratory" else ""),
        "All values are simulation outputs within the model assumptions of `research/protocol.md`.",
        "",
        f"Generated by `echo.report` from {len(runs)} validated result files (schema echo.result.v1). "
        f"Code revision(s) recorded in the manifests: {', '.join(revs)}.",
        "",
    ]
    if checks:
        lines += ["## Verification checks (EXP-001 V1 to V6)", "", "| Check | Pass | Detail |", "|---|---|---|"]
        for k in sorted(c for c in checks if c.startswith("V")):
            detail = {kk: vv for kk, vv in checks[k].items() if kk != "pass" and not isinstance(vv, (list, dict)) }
            lines.append(f"| {k} | {'yes' if checks[k]['pass'] else 'NO'} | {', '.join(f'{a}={b}' for a, b in detail.items())} |")
        lines.append("")
    lines += ["## Per-arm means over seeds", "",
              "Mean (seed SD) per arm. Units: drift in rad; see the units table below. n = runs per arm.", ""]
    show = ["drift_rad", "homogenisation", "discovery", "diversity_ild", "skip_rate", "exposure_gini"]
    lines.append("| Arm | n | " + " | ".join(show) + " | runtime (s) |")
    lines.append("|---|---|" + "---|" * len(show) + "---|")
    for a in arms:
        cells = [f"{_fmt(a[m][0], 3)} ({_fmt(a[m][1], 3)})" for m in show]
        lines.append(f"| {a['arm']} | {a['n_ok']}/{a['n_runs']} | " + " | ".join(cells) + f" | {a['runtime_s']:.2f} |")
    lines += ["", "Full per-run values for all ten metrics: `metrics.csv`.", "", "| Metric | Unit |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in UNITS.items()]
    lines.append("")
    if pilot:
        lines += [
            "## Pilot variance for the seed-count decision (protocol section 5)", "",
            f"Paired SIM minus RAND drift over {pilot['n_seeds']} exploratory seeds ({pilot['block']} block, full EXP-002 size, adaptive, eta = 0.05).",
            "The mean difference is shown only because the SD is computed around it; it is not interpreted.", "",
            f"- SD of paired differences: {pilot['sd_diff']:.5f} rad",
            f"- Mean paired difference (not interpreted): {pilot['mean_diff']:.5f} rad",
            "- Projected 95 % paired t half-width: " + ", ".join(f"n = {n}: {v:.5f} rad" for n, v in pilot["projected_half_width"].items()),
            f"- Protocol threshold: SESOI / 2 = {SESOI / 2:.3f} rad. Ten seeds are "
            + ("adequate" if pilot["projected_half_width"][10] <= SESOI / 2 else "NOT adequate") + " by this rule.",
            "",
            "![Exploratory pilot: per-seed mean drift under RAND (circles) and SIM (squares), paired by seed, in radians.](fig-pilot-drift.svg)",
            "",
        ]
    if timing:
        lines += ["## Runtime (exploratory measurement)", "",
                  "Mean wall-clock per full-size run (N = 1000, U = 200, T = 100), by policy:", ""]
        lines += [f"- {p}: {v:.2f} s (n = {timing['n_timed_runs'][p]})" for p, v in sorted(timing["mean_runtime_s_by_policy"].items())]
        lines.append("")
        for e, pj in timing["projection"].items():
            if pj["seconds"] is None:
                lines.append(f"- {e}: {pj['runs']} runs, projection unavailable ({pj['note']})")
            else:
                lines.append(f"- {e}: {pj['runs']} runs, projected {pj['seconds']:.0f} s ({pj['seconds'] / 60:.1f} min) single-process")
        lines.append("")
    if screen:
        lines += ["## Degenerate-case screen (one exploratory seed, EXP-003 cells)", "",
                  "One seed per cell, so there is no uncertainty estimate; this screens for saturation, "
                  "frozen listeners and skip extremes only. It is not a sensitivity result.", "",
                  "| Rule | eta | Profile | RAND drift (rad) | SIM drift (rad) | RAND skip | SIM skip | SIM listeners with zero drift |",
                  "|---|---|---|---|---|---|---|---|"]
        cells: dict = defaultdict(dict)
        for c in screen:
            cells[(c["update_rule"], c["eta"], c["profile"])][c["policy"]] = c
        for key in sorted(cells):
            r, s_ = cells[key].get("RAND"), cells[key].get("SIM")
            if r and s_:
                lines.append(f"| {key[0]} | {key[1]} | {key[2]} | {r['drift_rad']:.3f} | {s_['drift_rad']:.3f} | "
                             f"{r['skip_rate']:.3f} | {s_['skip_rate']:.3f} | {s_['users_with_zero_drift']} |")
        lines.append("")
    return "\n".join(lines) + "\n"


def build_pdf(md_path: Path) -> tuple[bool, str]:
    pandoc = TOOLS / "pandoc"
    py = TOOLS / "py" / "bin" / "python"
    if not pandoc.exists() or not py.exists():
        return False, f"PDF skipped: pandoc or the typst interpreter not found under {TOOLS}"
    typ = md_path.with_suffix(".typ")
    pdf = md_path.with_suffix(".pdf")
    r = subprocess.run([str(pandoc), md_path.name, "-s", "-t", "typst", "-V", "mainfont=Libertinus Serif", "-o", typ.name],
                       cwd=md_path.parent, capture_output=True, text=True)
    if r.returncode != 0:
        return False, f"pandoc failed: {r.stderr.strip()}"
    r = subprocess.run([str(py), "-I", "-c", "import sys, typst; typst.compile(sys.argv[1], output=sys.argv[2])", typ.name, pdf.name],
                       cwd=md_path.parent, capture_output=True, text=True)
    if r.returncode != 0:
        return False, f"typst failed: {r.stderr.strip()[-500:]}"
    return True, str(pdf)


def generate(results_dir: Path, pdf: bool = True) -> dict[str, Any]:
    runs = load_runs(results_dir)
    exp_ids = {r["result"]["experiment_id"] for r in runs}
    labels = {r["result"]["label"] for r in runs}
    if len(exp_ids) != 1 or len(labels) != 1:
        raise ValueError(f"mixed experiments or labels in {results_dir}: {exp_ids}, {labels}")
    exp_id, label = exp_ids.pop(), labels.pop()
    out = results_dir / "report"
    out.mkdir(parents=True, exist_ok=True)
    metrics_csv(runs, out / "metrics.csv")
    arms = arm_table(runs)
    blocks = {r["result"]["block"] for r in runs}
    pilot = paired_drift(runs, "pilot") if "pilot" in blocks else None
    timing = runtime_projection(runs)
    checks_path = results_dir / "checks.json"
    checks = json.loads(checks_path.read_text(encoding="utf-8")) if checks_path.exists() else None
    if pilot:
        pilot_figure(pilot, out / "fig-pilot-drift.svg")
    screen = None
    if "sensitivity_screen" in blocks:
        screen = []
        for r in runs:
            res = r["result"]
            if res["block"] == "sensitivity_screen" and res["status"] == "ok":
                c = res["config"]
                screen.append({"policy": c["policy"], "update_rule": c["update_rule"], "eta": c["eta"], "profile": c["profile"],
                               "drift_rad": res["metrics"]["drift_rad"], "skip_rate": res["metrics"]["skip_rate"],
                               "users_with_zero_drift": res["diagnostics"]["users_with_zero_drift"]})
    summary = {
        "experiment_id": exp_id, "label": label, "n_runs": len(runs),
        "n_failed": sum(1 for r in runs if r["result"]["status"] != "ok"),
        "pilot": pilot, "timing": timing, "checks_all_pass": None if checks is None else checks["all_pass"],
        "sensitivity_screen": screen,
    }
    (out / "summary.json").write_text(json.dumps(summary, sort_keys=True, indent=1) + "\n", encoding="utf-8")
    md = build_markdown(exp_id, label, runs, arms, pilot, timing, checks, screen)
    md_path = out / "summary.md"
    md_path.write_text(md, encoding="utf-8")
    pdf_status = build_pdf(md_path) if pdf else (False, "PDF not requested")
    summary["pdf"] = pdf_status
    return summary
