# SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0
"""Evidence audit (master prompt 11.5): map every number in the manuscript,
supplement, research report and experiment reports to a committed result.

For each decimal number in a document, the script looks for a numeric leaf in
the committed result files (analysis.json of EXP-002 to EXP-004, the EXP-001
summaries and checks, the M4 exploratory confounder file, the configs, the
calibration file and the freeze record) that rounds to the printed value at
the printed precision. Percentages are matched against value x 100. Values
that are derived (a CI half-width, a unit conversion) or are design
parameters stated in the protocol are listed in DERIVED with their source.

Integer tokens are matched against integer leaves of the same files or the
DERIVED list; small integers (<= 20) are structural in most places (section,
item or seed counts) and are reported as such rather than mapped.

Writes research/publication/artifact_manifest.json. Exit code 1 if any
decimal token is unmatched.

Usage: python3 scripts/build_artifact_manifest.py [--check]
"""

from __future__ import annotations

import json
import math
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

SOURCES = {
    "results/EXP-002/analysis/analysis.json": "EXP-002",
    "results/EXP-003/analysis/analysis.json": "EXP-003",
    "results/EXP-004/analysis/analysis.json": "EXP-004",
    "results/exploratory/EXP-001/report/summary.json": "EXP-001",
    "results/exploratory/EXP-001-m3-smoke/checks.json": "EXP-001",
    "results/exploratory/EXP-004-smoke/checks.json": "EXP-001",
    "results/exploratory/M4-confounders/confounders.json": "M4-exploratory",
    "experiments/EXP-002/config.json": "EXP-002",
    "experiments/EXP-003/config.json": "EXP-003",
    "experiments/EXP-004/config.json": "EXP-004",
    "data/fma_calibration_v1.json": "data",
    "research/freeze.json": "freeze",
    "data/manifest.json": "data",
}

DOCUMENTS = [
    "research/paper/manuscript.md",
    "research/paper/supplementary.md",
    "research/report.md",
    "research/experiments/EXP-001/report.md",
    "research/experiments/EXP-002/report.md",
    "research/experiments/EXP-003/report.md",
    "research/experiments/EXP-004/report.md",
    "research/claims_register.csv",
    "research/limitations.md",
]

# Values that are design parameters, unit conversions or simple derivations.
# token -> (kind, source or derivation)
DERIVED = {
    "0.05": ("parameter", "SESOI and eta, research/protocol.md sections 2 and 3"),
    "0.01": ("parameter", "eta level, EXP-003 protocol item 7; also an approximate skip-rate bound derived from S4"),
    "0.2": ("parameter", "eta level and EXPLORE epsilon, research/protocol.md section 3"),
    "0.1": ("parameter", "tau and spreads, research/protocol.md section 3 and DEC-006"),
    "0.5": ("parameter", "MMR lambda and bounded-confidence threshold, research/protocol.md section 3"),
    "0.025": ("derived", "SESOI / 2, research/protocol.md section 5"),
    "0.017": ("derived", "half-width of the EXP-002 primary CI: (-0.0200 - -0.0535) / 2 = 0.01675"),
    "2.9": ("derived", "0.05 rad in degrees (0.05 x 180 / pi = 2.86)"),
    "1.57": ("derived", "pi / 2"),
    "0.9500": ("derived", "Holm level 1 - 0.05 / 1"),
    "0.95": ("derived", "Holm level 1 - 0.05 / 1, or 1 - eta at eta 0.05"),
    "0.9750": ("derived", "Holm level 1 - 0.05 / 2"),
    "0.9833": ("derived", "Holm level 1 - 0.05 / 3"),
    "0.9875": ("derived", "Holm level 1 - 0.05 / 4"),
    "0.9972": ("derived", "Holm level 1 - 0.05 / 18"),
    "1e-12": ("parameter", "unit-norm tolerance, EXP-001 check V4"),
    "1.0": ("parameter", "draft Zipf exponent s = 1.0, research/protocol.md section 3"),
    "15.3.1": ("environment", "macOS version in the run manifests"),
    "3.12.1": ("environment", "Python version in the run manifests"),
    "2.2.6": ("environment", "numpy version in the run manifests"),
    "1.0.0": ("environment", "version string"),
    "4.0": ("licence", "CC BY 4.0"),
    "0.0": ("parameter", "eta = 0.0 for fixed preferences, run ids"),
    "0.0000": ("derived", "bootstrap p-value exactly 0 (p_boot in analysis.json)"),
    "4.2": ("derived", "share_above_pi_over_2 0.042 for EXP-002 RAND in confounders.json, as a percentage"),
    "1.11": ("derived", "EXP-002 RAND mean drift 1.1119 rad, rounded"),
    "1.2": ("derived", "runtime of the FMA-path smoke, 1.152 s, progress.md 2026-11-25"),
    "0.13": ("derived", "POP skip rate range in the EXP-001 run, results/exploratory/EXP-001/report/summary.md"),
    "0.29": ("derived", "POP skip rate range in the EXP-001 run, results/exploratory/EXP-001/report/summary.md"),
    "0.022": ("derived", "maximum skip rate of RAND, SIM, MMR and EXPLORE at full size in EXP-001, summary.md"),
    "1.15": ("derived", "EXP-001 per-run runtime (RAND), summary.md"),
    "2.85": ("derived", "EXP-001 per-run runtime (EXPLORE), summary.md"),
    "1.33": ("derived", "EXP-001 one-seed screen RAND drift at eta 0.2, summary.md"),
    "1.36": ("derived", "EXP-001 one-seed screen RAND drift at eta 0.2, summary.md"),
    "2.2e-16": ("derived", "worst norm error, results/exploratory/EXP-001-m3-smoke/checks.json"),
    "3.3e-16": ("derived", "worst norm error, results/exploratory/EXP-004-smoke/checks.json"),
    "0.0159": ("derived", "pilot SD 0.01587 rad (freeze.json c4_disclosure), rounded"),
    "0.642": ("derived", "pilot per-arm mean RAND, protocol 10.2 item 6"),
    "0.483": ("derived", "pilot per-arm mean SIM, protocol 10.2 item 6"),
    "28": ("derived", "largest_cluster_share 0.2819 (confounders.json), as a percentage"),
    "1000": ("parameter", "N = 1000 tracks per catalogue, research/protocol.md section 3"),
    "200": ("parameter", "U = 200 listeners per seed, research/protocol.md section 3"),
    "560": ("derived", "100 + 360 + 100 confirmatory runs (integrity.planned_runs of EXP-002, EXP-003, EXP-004)"),
    "36": ("derived", "18 EXP-003 cells x 2 policies, EXP-001 sensitivity_screen block"),
    "174": ("environment", "pytest count before the M3 runs, progress.md 2026-11-25"),
    "40": ("parameter", "EXP-001 smoke matrix 5 x 2 x 2 x 2, EXP-001 protocol"),
    "518": ("parameter", "number of librosa features in FMA features.csv, research/protocol.md 10.1"),
    "0.37": ("derived", "0.99^100 = 0.366, weight left on the initial taste at eta 0.01 (manuscript section 6)"),
    "0.006": ("derived", "0.95^100 = 0.0059, weight left on the initial taste at eta 0.05 (manuscript section 6)"),
    "10.2": ("section reference", "research/protocol.md section 10.2"),
    "87": ("environment", "load average observed during M3 (progress.md)"),
}

# Derivations that take precedence over a value match when the line carries the marker.
DERIVED_MARKERS = {"0.006": ("^100",), "0.37": ("^100", "weight"), "0.95": ("^100",)}

ID_PATTERNS = [
    r"`[^`]*`",  # code spans (paths, hashes, commands)
    r"https?://\S+",
    r"\b(?:EXP|DEC|J|C|RAT|F|R|M|V|H|S|D)-?\d+(?:-\w+)?\b",
    r"\b[0-9a-f]{7,64}\b",
    r"\b(?:arXiv|DOI|doi)[: ]\s*\S+",
    r"\b10\.\d{4,}/\S+",
    r"\b\d{4}-\d{2}-\d{2}(?:T[\d:.]+Z)?\b",
    r"\b\d{1,2}:\d{2}(?::\d{2})?\b",
    r"\b(?:section|sections|item|items|protocol|chapter|equation|equations|Table|table|step|steps|eta=)\s+\d+(?:\.\d+)*(?:\s*(?:,|and|to)\s*\d+(?:\.\d+)*)*",
    r"\b11\.\d\b",
    r"\b(?:R\^d|R\^16|10\^\d+)\b",
    r"\bpi/2\b|\bpi / 2\b",
    r"\b\d+\s*min\s*\d+\s*s\b",
    r"PMLR \d+:\d+-\d+",
    r"pp\. \d+-\d+",
    r"\b20261[12]\d\d\b|\b9000\d\d\b",
    r"SHA-256|SHA-1",
    r"^#+\s+[\d.]+",
    r"\b\d+\.\d+\.\d+\b",
    r"\b\d+\.\d+ item",
    r"\b(?:19|20)\d\d\b",
]
NUM = re.compile(r"(?<![\w.])-?\d{1,3}(?:,\d{3})+(?:\.\d+)?(?![\w.])|(?<![\w.])-?\d+(?:\.\d+)?(?:e-?\d+)?(?![\w])")


def leaves(obj, path=""):
    if isinstance(obj, bool) or obj is None:
        return
    if isinstance(obj, (int, float)):
        yield path, float(obj)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from leaves(v, f"{path}/{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from leaves(v, f"{path}/{i}")


def build_pool():
    pool = []
    for rel, exp in SOURCES.items():
        data = json.loads((REPO / rel).read_text())
        for p, v in leaves(data):
            if math.isfinite(v):
                pool.append((v, rel, p, exp))
    return pool


def strip(line: str) -> str:
    for pat in ID_PATTERNS:
        line = re.sub(pat, " ", line)
    return line


def match(token: str, pool, percent: bool):
    t = token.replace(",", "")
    if "e" in t:
        return []
    val = float(t)
    dec = len(t.split(".")[1]) if "." in t else 0
    tol = 0.5 * 10 ** (-dec) + 1e-12
    hits = []
    for v, rel, p, exp in pool:
        vv = v * 100 if percent else v
        if dec == 0 and not percent:
            if float(v).is_integer() and v == val:
                hits.append((rel, p, exp))
        elif abs(vv - val) <= tol:
            hits.append((rel, p, exp))
    return hits


GOOD = ("/primary/", "/drift_family/", "/cells/", "/mean_diff", "/boot_ci95/", "/holm/ci/", "/t_ci95/", "/sd_diff",
        "/d_z", "/drift_rad/", "/summary/", "/quantiles_rad/", "/max_rad", "/share_above", "/C_skip", "/pilot/")
BAD = ("/diffs/", "/treat/", "/ref/", "/per_seed/", "/seeds/")


def rank(hits, context_exp):
    def score(h):
        rel, p, exp = h
        sc = 0
        if context_exp and exp == context_exp:
            sc += 4
        sc += 2 * any(g in p for g in GOOD)
        sc -= 3 * any(b in p for b in BAD)
        return -sc
    return sorted(hits, key=score)


CTX = re.compile(r"EXP-00[1-4]|J-0008|exploratory")


def context_of(text: str, current: str | None) -> str | None:
    found = CTX.findall(text)
    if not found:
        return current
    last = found[-1]
    return "M4-exploratory" if last in ("J-0008",) else ("M4-exploratory" if last == "exploratory" and "J-0008" in text else (last if last.startswith("EXP") else current))


def revision() -> str:
    try:
        return subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    except OSError:
        return "unknown"


EXPERIMENTS = {
    "EXP-001": {"status": "exploratory", "run_ids": "results/exploratory/EXP-001*/runs/*.json, results/exploratory/EXP-004-smoke/runs/*.json",
                "protocol_sha256": "5d869d0f418956cdac48cb94a97a8a890aa96ba81193bb4a898664704830cff4",
                "config_sha256": "7fee59c4d7587d12b2dd473b16977bc5d902a42092be3dd92da523c742b53176",
                "code_revision": "b2e9738 (first run), 04bc350 (re-run)",
                "generator": "PYTHONPATH=src .venv/bin/python -m echo.cli smoke; echo.cli report"},
    "EXP-002": {"status": "confirmatory", "run_ids": "EXP-002_main_<POLICY>_<fixed-0.0|adaptive-0.05>_s<seed> (results/EXP-002/provenance.csv)",
                "protocol_sha256": "3852ad1950f73740378c6f19339d912da57c69daab82d218c3b8efb33af192b2",
                "config_sha256": "903f524679afb4a67fe4e6d36ff5b17f7f398475fa7f58c0c993846a64ef174c",
                "code_revision": "afc08509847ac362b6b95d8097aea08a615f286b (runs), 04bc350 (analysis code)",
                "generator": "PYTHONPATH=src .venv/bin/python -m echo.analysis results/EXP-002 --planned 100 --kind policy"},
    "EXP-003": {"status": "confirmatory", "run_ids": "EXP-003_sensitivity_<rule>_<eta>_<profile>_<POLICY>_s<seed> (results/EXP-003/provenance.csv)",
                "protocol_sha256": "f0a3e1061d05bd5b58b9998112426b02eb62ef6f34d8783f42a787f19924e49a",
                "config_sha256": "285e3dd6b52f271454f0d443934fc7588201247e09ec60d2f1496850254771c0",
                "code_revision": "afc08509847ac362b6b95d8097aea08a615f286b (runs), 04bc350 (analysis code)",
                "generator": "PYTHONPATH=src .venv/bin/python -m echo.analysis results/EXP-003 --planned 360 --kind sensitivity --reference results/EXP-002/analysis/analysis.json"},
    "EXP-004": {"status": "confirmatory", "run_ids": "EXP-004_fma_<POLICY>_<fixed-0.0|adaptive-0.05>_s<seed> (results/EXP-004/provenance.csv)",
                "protocol_sha256": "4f6a5ca60c788a2bee49abaef5af3ca2c039152d1ec0569ab4d54c0f79d75402",
                "config_sha256": "efb26feb7078799642631b15e6ec4604b59aebf49405c6ff3dec8bf3ad55560d",
                "code_revision": "afc08509847ac362b6b95d8097aea08a615f286b (runs), 04bc350 (analysis code)",
                "generator": "PYTHONPATH=src .venv/bin/python -m echo.analysis results/EXP-004 --planned 100 --kind replication --reference results/EXP-002/analysis/analysis.json"},
    "M4-exploratory": {"status": "exploratory (J-0008), no simulation", "run_ids": "reads the EXP-002, EXP-003 and EXP-004 runs; regenerates inputs for seeds 20261124-20261133",
                       "protocol_sha256": "none (exploratory)", "config_sha256": "EXP-002 and EXP-004 configs (above)",
                       "code_revision": "commit of scripts/m4_exploratory_confounders.py (see git log)",
                       "generator": "PYTHONPATH=src .venv/bin/python scripts/m4_exploratory_confounders.py"},
    "data": {"status": "calibration (J-0003)", "run_ids": "none", "protocol_sha256": "research/protocol.md a81ed32c5e21f06e68d61e00250119762d1a56cdf4230a05ac3d89ff48c8f5dc",
             "config_sha256": "data/fma_calibration_v1.json e3c763c27492dd7c7c06bbd73d5cf3a1cba232bf6bed1db80078791b6c208b98",
             "code_revision": "17ac055 (freeze)", "generator": "scripts/build_fma_catalogue.py"},
    "freeze": {"status": "freeze record", "run_ids": "pilot seeds 900002-900011 (exploratory)", "protocol_sha256": "a81ed32c5e21f06e68d61e00250119762d1a56cdf4230a05ac3d89ff48c8f5dc",
               "config_sha256": "see research/freeze.json", "code_revision": "17ac055", "generator": "scripts/write_freeze_record.py"},
}

FIGURES = {
    "results/EXP-002/analysis/fig-contrasts.svg": "EXP-002",
    "results/EXP-002/analysis/fig-arms-drift.svg": "EXP-002",
    "results/EXP-003/analysis/fig-contrasts.svg": "EXP-003",
    "results/EXP-004/analysis/fig-contrasts.svg": "EXP-004",
    "results/EXP-004/analysis/fig-arms-drift.svg": "EXP-004",
    "results/exploratory/EXP-001/report/fig-pilot-drift.svg": "EXP-001",
}


def audit():
    pool = build_pool()
    entries, unmatched, structural, missing = [], [], 0, []
    for doc in DOCUMENTS:
        path = REPO / doc
        if not path.exists():
            missing.append(doc)
            continue
        doc_ctx = re.search(r"EXP-00[1-4]", doc)
        heading_ctx = doc_ctx.group(0) if doc_ctx else None
        if doc.endswith(".csv"):
            import csv
            with open(path, newline="") as fh:
                lines = [f"{r['claim_id']}: {r['text']} {r['limitations']}" for r in csv.DictReader(fh)]
        else:
            lines = path.read_text().splitlines()
        for ln, raw in enumerate(lines, 1):
            if raw.startswith("<!-- SPDX"):
                continue
            if raw.startswith("#"):
                heading_ctx = context_of(raw, heading_ctx if doc_ctx else None)
            line_ctx = context_of(raw, heading_ctx)
            line = strip(raw)
            for m in NUM.finditer(line):
                tok = m.group(0)
                after = line[m.end():m.end() + 2]
                percent = after.strip().startswith("%")
                is_int = "." not in tok and "e" not in tok
                if is_int and not percent and abs(int(tok.replace(",", ""))) <= 20:
                    structural += 1
                    continue
                key = tok.lstrip("-")
                short = "." in key and len(key.split(".")[1]) <= 2
                forced = key in DERIVED and (short or any(mk in raw for mk in DERIVED_MARKERS.get(key, ())))
                hits = [] if forced else rank(match(tok, pool, percent), line_ctx)
                if hits:
                    rel, p, exp = hits[0]
                    entries.append({"document": doc, "line": ln, "token": tok + (" %" if percent else ""),
                                    "experiment_id": exp, "result_path": rel, "json_path": p,
                                    "metric": p.rsplit("/", 1)[-1] if not p.rsplit("/", 1)[-1].isdigit() else p,
                                    "context_experiment": line_ctx,
                                    "n_matches": len(hits),
                                    "other_matches": [f"{h[0]}#{h[1]}" for h in hits[1:4]]})
                elif key in DERIVED:
                    kind, src = DERIVED[key]
                    entries.append({"document": doc, "line": ln, "token": tok, "experiment_id": kind, "result_path": None,
                                    "json_path": None, "metric": src, "other_matches": []})
                else:
                    unmatched.append({"document": doc, "line": ln, "token": tok, "context": raw.strip()[:160]})
    return entries, unmatched, structural, missing


def main(argv) -> int:
    entries, unmatched, structural, missing = audit()
    manifest = {
        "schema_version": "1.0",
        "generated_by": "scripts/build_artifact_manifest.py",
        "repository_revision_at_generation": revision(),
        "scope": DOCUMENTS,
        "method": ("Every decimal number (and every integer above 20) in the scoped documents is matched to a numeric leaf of a "
                   "committed result file that rounds to the printed value at the printed precision, or to a listed "
                   "derivation or design parameter. Matching by value is necessary but not sufficient; the claims audit "
                   "records the manual check that each match is the intended quantity for the primary and claim-bearing numbers."),
        "experiments": EXPERIMENTS,
        "figures": {k: {"experiment_id": v, **{f: EXPERIMENTS[v][f] for f in ("generator", "code_revision")}} for k, v in FIGURES.items()},
        "missing_documents": missing,
        "counts": {"mapped_tokens": len(entries), "unmatched_tokens": len(unmatched), "small_integer_tokens_not_mapped": structural},
        "unmatched": unmatched,
        "entries": entries,
    }
    out = REPO / "research" / "publication" / "artifact_manifest.json"
    if "--check" not in argv:
        out.write_text(json.dumps(manifest, indent=1) + "\n")
    print(json.dumps(manifest["counts"]))
    for d in missing:
        print("MISSING (not audited)", d)
    for u in unmatched:
        print("UNMATCHED", u)
    return 1 if unmatched else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
