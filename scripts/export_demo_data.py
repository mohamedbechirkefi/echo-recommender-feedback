# SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
"""Export the published results for the M5 demo (schema lab-demo-results 1.0.0).

Reads committed files only: the three confirmatory analyses, the EXP-001
exploratory summary, the experiment registry, the claims register, the
artifact manifest, the manuscript and its supplementary appendix, and the
M5 exploratory taste-map trace. It writes demo/public/data/results.json.

Every `display` and `interval_display` string is formatted the way the
manuscript prints it (4 decimals for rad contrasts, a "+" sign where the
manuscript's running text uses one) and is checked verbatim against the
manuscript, or against the supplementary appendix where `display_source`
says so (tests/test_demo_export.py). No timestamp is written, so the output
is a pure function of the inputs.

Usage:
    PYTHONPATH=src .venv/bin/python scripts/export_demo_data.py [--check]
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "demo" / "public" / "data" / "results.json"

ANALYSIS = {e: f"results/{e}/analysis/analysis.json" for e in ("EXP-002", "EXP-003", "EXP-004")}
EXP001_SUMMARY = "results/exploratory/EXP-001/report/summary.json"
EXP001_CHECKS = "results/exploratory/EXP-001/checks.json"
REGISTRY = "research/experiment_registry.csv"
CLAIMS = "research/claims_register.csv"
MANIFEST = "research/publication/artifact_manifest.json"
MANUSCRIPT = "research/paper/manuscript.md"
SUPPLEMENTARY = "research/paper/supplementary.md"
TASTE_MAP = "results/exploratory/M5-taste-map/trace.json"
CONFIG_002 = "experiments/EXP-002/config.json"
SOURCES = [*ANALYSIS.values(), EXP001_SUMMARY, EXP001_CHECKS, CONFIG_002, REGISTRY, CLAIMS, MANIFEST, MANUSCRIPT,
           SUPPLEMENTARY, TASTE_MAP]

POLICIES = ("RAND", "POP", "SIM", "MMR", "EXPLORE")
RULES = ("consumed", "exposure", "bounded")
ETAS = (0.01, 0.05, 0.2)

# Manuscript wording of the equivalence disclosure (section 4, DEC-012 and DEC-014).
READINGS_NOTE = ("DEC-012 computes two readings of \"practically equivalent\": the band reading (the 95 % CI lies "
                 "inside [-0.05, 0.05] rad) and the label reading (the decision label is exactly \"practically "
                 "equivalent\"). Both readings give this verdict; the owner ratified the construction on "
                 "2026-11-25 (DEC-014).")


class ExportError(RuntimeError):
    """Raised when a committed input is missing, inconsistent or unexpected."""


def read(rel: str) -> bytes:
    p = REPO / rel
    if not p.is_file():
        raise ExportError(f"missing input {rel}")
    return p.read_bytes()


def load(rel: str):
    return json.loads(read(rel))


def f4(x: float, signed: bool = False) -> str:
    s = f"{x:.4f}"
    if s in ("-0.0000", "0.0000"):
        raise ExportError(f"value {x} rounds to zero at 4 decimals")
    return ("+" + s) if signed and x > 0 else s


def ci4(lo: float, hi: float) -> str:
    return f"[{lo:.4f}, {hi:.4f}]"


def est(label, value, lo, hi, unit="rad", display=None, interval=None, source="manuscript", kind="confirmatory",
        level=0.95):
    if lo is None:
        level = None
    return {
        "label": label,
        "estimate": float(value),
        "ci_low": None if lo is None else float(lo),
        "ci_high": None if hi is None else float(hi),
        "ci_level": level,
        "unit": unit,
        "display": display if display is not None else f4(value),
        "interval_display": interval if interval is not None else (None if lo is None else ci4(lo, hi)),
        "display_source": source,
        "kind": kind,
    }


def contrast_est(label, c, kind, signed=False, holm=False, t=False):
    if holm:
        lo, hi = c["holm"]["ci"]
        level = c["holm"]["level"]
    elif t:
        lo, hi = c["t_ci95"]
        level = 0.95
    else:
        lo, hi = c["boot_ci95"]
        level = 0.95
    return est(label, c["mean_diff"], lo, hi, display=f4(c["mean_diff"], signed), kind=kind, level=level)


def registry() -> dict:
    rows = list(csv.DictReader(read(REGISTRY).decode().splitlines()))
    return {r["experiment_id"]: r for r in rows}


def claim_ids(exp: str) -> list[str]:
    rows = csv.DictReader(read(CLAIMS).decode().splitlines())
    return [r["claim_id"] for r in rows if r["claim_id"].startswith("C-") and exp in r["result_id"]]


def arm(a: dict, policy: str, model: str = "adaptive") -> dict:
    hits = [x for x in a["arms"] if x["policy"] == policy and x["preference_model"] == model]
    if len(hits) != 1:
        raise ExportError(f"{a['experiment_id']}: expected one {policy}/{model} arm, found {len(hits)}")
    return hits[0]


def check_analysis(a: dict, exp: str) -> None:
    integ = a["integrity"]
    if a["experiment_id"] != exp or not integ["complete"] or integ["failed_runs"] != 0:
        raise ExportError(f"{exp}: analysis incomplete or has failed runs")
    if a["code_dirty"] != ["False"] or len(a["code_revisions"]) != 1:
        raise ExportError(f"{exp}: runs not from one clean revision")


def exp001(reg) -> dict:
    s = load(EXP001_SUMMARY)
    checks = load(EXP001_CHECKS)
    if not (s["checks_all_pass"] and checks["all_pass"]):
        raise ExportError("EXP-001: checks do not all pass")
    p = s["pilot"]
    hw = p["projected_half_width"]["10"]
    return {
        "id": "EXP-001",
        "title": reg["EXP-001"]["title"],
        "status": "exploratory (verification); not confirmatory",
        "verdict": "Pass (exploratory; no claim): checks V1 to V6 pass",
        "estimates": [
            est("Pilot SIM minus RAND drift (draft parameters, seen before the freeze)", p["mean_diff"], None, None,
                display=f"{p['mean_diff']:.5f}", kind="exploratory"),
            est("Pilot SD of paired differences", p["sd_diff"], None, None, display=f"{p['sd_diff']:.5f}",
                kind="exploratory"),
            est("Projected 95 % CI half-width at 10 seeds", hw, None, None, display=f"{hw:.4f}", kind="exploratory"),
        ],
        "claim_ids": claim_ids("EXP-001"),
        "report_path": reg["EXP-001"]["report_path"],
        "notes": [
            "Exploratory verification and smoke matrix: determinism, zero drift under fixed preferences, candidate "
            "exclusion, unit norms, metric bounds and schema (checks V1 to V6). It supports no research claim.",
            "The pilot used draft parameters and exploratory seeds; its single values carry no interval. It was "
            "used only to confirm the seed count (10 seeds).",
        ],
    }


def exp002(reg) -> dict:
    a = load(ANALYSIS["EXP-002"])
    check_analysis(a, "EXP-002")
    fam, prim = a["drift_family"], a["primary"]
    if prim["decision"] != "reject H0" or fam["SIM-RAND"]["mean_diff"] != prim["mean_diff"]:
        raise ExportError("EXP-002: unexpected primary decision")
    nc = a["integrity"]["negative_control"]
    if not nc["pass"]:
        raise ExportError("EXP-002: negative control failed")
    d = a["secondary_vs_rand_descriptive"]
    ests = [contrast_est("SIM minus RAND drift (primary), 95 % bootstrap CI", prim, "primary"),
            contrast_est("SIM minus RAND drift (primary), paired t CI", prim, "primary", t=True)]
    for name in ("POP-RAND", "MMR-RAND", "EXPLORE-RAND"):
        pretty = name.replace("-", " minus ")
        ests.append(contrast_est(f"{pretty} drift, 95 % bootstrap CI", fam[name], "secondary"))
        ests.append(contrast_est(f"{pretty} drift, Holm-adjusted CI", fam[name], "secondary", holm=True))
    for metric, lab in (("exposure_gini", "exposure Gini"), ("diversity_ild", "intra-list diversity"),
                        ("discovery", "discovery"), ("homogenisation", "homogenisation")):
        x = d[f"adaptive/SIM-RAND/{metric}"]
        ests.append(est(f"SIM minus RAND {lab} (descriptive)", x["mean_diff"], *x["ci95"], unit="",
                        display=f4(x["mean_diff"], True), kind="descriptive"))
    return {
        "id": "EXP-002",
        "title": reg["EXP-002"]["title"],
        "status": "confirmatory (primary); complete, 100 of 100 runs",
        "verdict": "reject H0; practical size unresolved (the CI extends past -0.05 rad)",
        "estimates": ests,
        "claim_ids": claim_ids("EXP-002"),
        "report_path": reg["EXP-002"]["report_path"],
        "notes": [
            f"Negative control: with fixed preferences, drift was exactly 0 in all {nc['fixed_runs_checked']} fixed "
            "runs (C-003).",
            "Uniform-random exposure is not neutral: under the adaptive model RAND itself moved preferences, so the "
            "contrast answers \"which policy moves taste more\", not \"which policy moves taste at all\" (C-008).",
            "The interpretation of this contrast was later withdrawn as assumption-dependent by EXP-003 and did not "
            "replicate on the real catalogue in EXP-004.",
            "Exposure contrasts are descriptive secondaries without multiplicity control; a personalised top-k "
            "policy concentrates exposure largely by construction.",
        ],
    }


def cell_key(rule, eta, prof):
    return f"{rule}/eta={eta}/{prof}"


def exp003(reg) -> tuple[dict, list]:
    a = load(ANALYSIS["EXP-003"])
    check_analysis(a, "EXP-003")
    v = a["verdict"]
    if not v["readings_agree"]:
        raise ExportError("EXP-003: equivalence readings disagree; owner decision needed")
    cells = a["cells"]
    if len(cells) != 18:
        raise ExportError("EXP-003: expected 18 cells")
    ests, chart = [], []
    trig = set(v["band_reading"]["withdraw_triggering_cells"]) | set(v["label_reading"]["withdraw_triggering_cells"])
    for prof in ("estimated", "oracle"):
        for rule in RULES:
            for eta in ETAS:
                k = cell_key(rule, eta, prof)
                c = cells[k]
                # Table 3 prints the estimated cells; the oracle cells are in Table S2 of the supplementary
                # appendix, except bounded / 0.05 / oracle, which section 5.2 prints too.
                src = "manuscript" if prof == "estimated" or k == "bounded/eta=0.05/oracle" else "supplementary"
                e = est(f"SIM minus RAND drift, {rule} / {eta} / {prof}", c["mean_diff"], *c["boot_ci95"],
                        source=src, kind="sensitivity")
                ests.append(e)
                chart.append({**chart_row("EXP-003", e), "cell": k, "decision": c["decision"],
                              "triggers_withdrawal": k in trig})
    return {
        "id": "EXP-003",
        "title": reg["EXP-003"]["title"],
        "status": "confirmatory sensitivity; complete, 360 of 360 runs",
        "verdict": v["verdict"],
        "estimates": ests,
        "claim_ids": claim_ids("EXP-003"),
        "report_path": reg["EXP-003"]["report_path"],
        "notes": [
            "Two cells at eta 0.05 trigger withdrawal: bounded / estimated is practically equivalent to 0, and "
            "bounded / oracle has the opposite sign. The sign also changes with eta under the consumed and "
            "exposure rules.",
            READINGS_NOTE,
            "Oracle versus estimated profile: the point signs differ, with both CIs excluding 0, in one pair "
            "(bounded, eta 0.2) (C-005).",
            "The nine oracle-profile intervals other than bounded / 0.05 / oracle are printed in Table S2 of the "
            "supplementary appendix, not in the manuscript body; they are shown here exactly as printed there.",
        ],
    }, chart


def exp004(reg) -> dict:
    a = load(ANALYSIS["EXP-004"])
    check_analysis(a, "EXP-004")
    rep = a["replication"]
    if not rep["readings_agree"]:
        raise ExportError("EXP-004: equivalence readings disagree; owner decision needed")
    fam, prim = a["drift_family"], a["primary"]
    d = a["secondary_vs_rand_descriptive"]
    ests = [contrast_est("SIM minus RAND drift (primary, FMA), 95 % bootstrap CI", prim, "primary"),
            contrast_est("SIM minus RAND drift (primary, FMA), paired t CI", prim, "primary", t=True)]
    for name in ("POP-RAND", "MMR-RAND", "EXPLORE-RAND"):
        pretty = name.replace("-", " minus ")
        ests.append(contrast_est(f"{pretty} drift, 95 % bootstrap CI", fam[name], "secondary"))
        ests.append(contrast_est(f"{pretty} drift, Holm-adjusted CI", fam[name], "secondary", holm=True))
    for metric, lab in (("exposure_gini", "exposure Gini"), ("diversity_ild", "intra-list diversity"),
                        ("discovery", "discovery"), ("homogenisation", "homogenisation")):
        x = d[f"adaptive/SIM-RAND/{metric}"]
        ests.append(est(f"SIM minus RAND {lab} (descriptive)", x["mean_diff"], *x["ci95"], unit="",
                        display=f4(x["mean_diff"], True), kind="descriptive"))
    pa = d["adaptive/POP-RAND/drift_per_accept_rad"]
    ests.append(est("POP minus RAND drift per accepted item (descriptive)", pa["mean_diff"], *pa["ci95"],
                    unit="rad per track", display=f"+{pa['mean_diff']:.6f}",
                    interval=f"[{pa['ci95'][0]:.6f}, {pa['ci95'][1]:.6f}]", kind="descriptive"))
    return {
        "id": "EXP-004",
        "title": reg["EXP-004"]["title"],
        "status": "confirmatory secondary (second test on real data); complete, 100 of 100 runs",
        "verdict": f"reject H0 with the opposite sign to EXP-002; frozen reading: {rep['reading']}",
        "estimates": ests,
        "claim_ids": claim_ids("EXP-004"),
        "report_path": reg["EXP-004"]["report_path"],
        "notes": [
            "Real FMA tracks (1000 of 4,951 per seed, PCA of librosa features, real genres and play counts); the "
            "listeners are simulated.",
            READINGS_NOTE,
            "POP's drift contrast is inconclusive, and its skip rate is far above RAND's; per accepted item POP "
            "drifts more than RAND, so the skip-rate confounder dominates the POP contrast.",
            "The ten 1000-track samples share the same 4,951 tracks, so seeds are not fully independent and the "
            "intervals may be too narrow.",
        ],
    }


def chart_row(exp: str, e: dict) -> dict:
    return {**e, "experiment": exp}


def arm_drift(exp: str) -> list:
    a = load(ANALYSIS[exp])
    out = []
    for p in POLICIES:
        x = arm(a, p)["drift_rad"]
        out.append({"policy": p, **est(f"{p} mean drift (adaptive)", x["mean"], *x["ci95"])})
    return out


def section(text: str, heading: str) -> str:
    m = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## )", text, re.S | re.M)
    if not m:
        raise ExportError(f"manuscript section {heading!r} not found")
    return m.group(1)


def bullets(block: str) -> list[str]:
    items = [ln[2:].strip() for ln in block.splitlines() if ln.startswith("- ")]
    if not items:
        raise ExportError("no bullet items found")
    return [re.sub(r"\*\*|`", "", s) for s in items]


def assumptions() -> list:
    base = load(CONFIG_002)["blocks"][0]["base"]
    src = "research/protocol.md section 3; experiments/EXP-002/config.json (frozen)"
    return [
        {"name": "Catalogue", "value": f"N = 1000 tracks, d = 16, K = {base['n_clusters']} clusters with weights "
         f"fitted on the FMA training split, Zipf exponent s = {base['zipf_s']}", "source": src},
        {"name": "Listeners and session", "value": "U = 200 simulated listeners per seed, T = 100 steps, slate of "
         "k = 10 tracks", "source": src},
        {"name": "Choice", "value": "softmax over cos(p, x) / tau with tau = 0.1 and a skip option of utility 0",
         "source": src + "; DEC-006"},
        {"name": "Preference update (primary)", "value": "consumed-item rule, eta = 0.05; EXP-003 adds an exposure "
         "rule, a bounded-confidence rule (threshold 0.5) and eta 0.01 and 0.2", "source": src},
        {"name": "Recommender profile", "value": "mean of consumed embeddings after a 5-step random warm-up "
         "(estimated); the oracle profile is an EXP-003 ablation", "source": src},
        {"name": "Policy parameters", "value": "MMR lambda = 0.5; EXPLORE epsilon = 0.2", "source": src},
        {"name": "Smallest effect size of interest", "value": "0.05 rad, a judgement-based value proposed by the AI "
         "and kept by the owner; not empirically anchored", "source": "research/protocol.md section 2"},
        {"name": "Independent unit", "value": "the seed (one catalogue and one listener population), 10 seeds per "
         "arm, matched across policies", "source": "research/protocol.md section 5"},
    ]


def taste_map() -> dict:
    t = load(TASTE_MAP)
    if t.get("schema") != "echo.m5.taste_map.v1":
        raise ExportError("taste map: unexpected schema")
    return {
        "label": t["label"],
        "source": TASTE_MAP,
        "generator": t["generator"],
        "seed": t["seed"],
        "config": t["config"],
        "setting": "EXP-002 setting (calibrated synthetic catalogue, consumed-item rule, eta 0.05, estimated "
                   "profile, N = 1000, U = 200, T = 100)",
        "projection": t["projection"],
        "tracks": t["tracks"],
        "listeners": t["listeners"],
        "policies": t["policies"],
    }


def build() -> dict:
    reg = registry()
    if sorted(reg) != ["EXP-001", "EXP-002", "EXP-003", "EXP-004"]:
        raise ExportError(f"unexpected registry: {sorted(reg)}")
    revs = {load(p)["code_revisions"][0] for p in ANALYSIS.values()}
    if len(revs) != 1:
        raise ExportError(f"results come from several revisions: {revs}")
    e3, chart3 = exp003(reg)
    e2, e4 = exp002(reg), exp004(reg)
    chart = [chart_row("EXP-002", e2["estimates"][0]) | {"cell": "consumed/eta=0.05/estimated",
                                                          "decision": "reject H0", "triggers_withdrawal": False},
             *chart3,
             chart_row("EXP-004", e4["estimates"][0]) | {"cell": "FMA catalogue", "decision": "reject H0",
                                                          "triggers_withdrawal": False}]
    man = read(MANUSCRIPT).decode()
    sesoi = {load(p)["sesoi_rad"] for p in ANALYSIS.values()}
    if sesoi != {0.05}:
        raise ExportError(f"unexpected SESOI {sesoi}")
    return {
        "schema": "lab-demo-results",
        "schema_version": "1.0.0",
        "project": "ECHO",
        "question": "Can recommendation policies change exposure and simulated taste rather than simply reflect it?",
        "status_label": ("Independent research manuscript / preprint draft, not peer-reviewed. Simulation only: "
                         "simulated preference change is not evidence of human persuasion. Protocol v1.0 frozen "
                         "by the owner on 2026-11-24; all 560 confirmatory runs complete. The owner's full-text "
                         "review of the manuscript is pending (M6)."),
        "code_revision": revs.pop(),
        "sources": [{"path": p, "sha256": hashlib.sha256(read(p)).hexdigest()} for p in SOURCES],
        "experiments": [exp001(reg), e2, e3, e4],
        "assumptions": assumptions(),
        "limitations": bullets(section(man, "7. Limitations and threats to validity")),
        # Project-specific extensions (validated by validateExtensions in demo/src/results.ts).
        "method": bullets(section(man, "4. Methods")),
        "sesoi_rad": 0.05,
        "contrast_chart": chart,
        "arm_drift": {"EXP-002": arm_drift("EXP-002"), "EXP-004": arm_drift("EXP-004")},
        "taste_map": taste_map(),
        "owner_pending": [
            "Full-text review of the manuscript, the reports and the articles (M6).",
            "Release, tag and any DOI or preprint (the owner's decision).",
        ],
    }


def render() -> str:
    return json.dumps(build(), indent=1, ensure_ascii=False) + "\n"


def main(argv) -> int:
    text = render()
    if "--check" in argv:
        same = OUT.exists() and OUT.read_text() == text
        print(f"{'OK' if same else 'DIFFERS'} {OUT.relative_to(REPO)}")
        return 0 if same else 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    print(f"wrote {OUT.relative_to(REPO)} ({len(text)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
