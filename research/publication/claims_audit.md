<!-- SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0 -->
# Claims and evidence audit (M4, 2026-11-25)

Scope: master prompt 11.5 and the M4 brief. Audited documents: `research/paper/manuscript.md`, `research/paper/supplementary.md`, `research/report.md` (see F-9), the four experiment reports, `research/claims_register.csv` and `research/limitations.md`. AI review is internal quality control, not peer review.

## Checklist

- [x] Every observed or simulated claim maps to a result file and run IDs (`research/claims_register.csv`, columns `result_id`, `config_sha256`, `figure_or_table`, `manuscript_section`).
- [x] Every external claim maps to a source in `research/literature_review.md`, with the part actually read (rows X-001 to X-008).
- [x] Denominators, units, precision, uncertainty and sample counts cross-checked against raw outputs (F-1, F-10).
- [x] No causal or human-behaviour claim drawn from simulation (manuscript sections 6 to 8; second review pass R-1, R-9).
- [x] Failed, null and exploratory results present and labelled (EXP-001; EXP-003 withdrawal; EXP-004 non-replication; EXP-004 POP inconclusive; J-0008).
- [ ] `research/report.md` is not yet on disk (F-9); the manifest must be rebuilt once it is written.

## Method

1. **Raw outputs.** `shasum -a 256 -c SHA256SUMS` in `results/EXP-002`, `EXP-003`, `EXP-004`: every line OK (208, 727 and 208 entries). `provenance.csv` against the run files: 100, 360 and 100 rows; one revision (afc08509847ac362b6b95d8097aea08a615f286b); every manifest `code_dirty: false`; config hash and seed in each row equal those in the run file (0 mismatches); one data-manifest hash.
2. **Analysis reproduction.** `echo.analysis` was re-run on copies of the committed runs and manifests in a scratch directory with the committed commands. All 20 analysis files (`analysis.json`, `analysis.md`, `arms.csv`, `contrasts.csv`, `per_seed.csv` and the SVG figures) are byte-identical to the committed ones.
3. **Number trace.** `python3 scripts/build_artifact_manifest.py` extracts every decimal number (and every integer above 20) from the scoped documents and maps it to a numeric leaf of a committed result file that rounds to the printed value at the printed precision, or to a listed derivation or design parameter. Result: 1311 tokens mapped, 0 unmatched; 313 small integers (20 or below) are structural (section numbers, seed counts, slate sizes) and are not mapped. Output: `research/publication/artifact_manifest.json`, which also lists, per experiment, the run-id pattern, protocol and config SHA-256, code revisions and generator command, and the generator of every figure.
4. **Exact checks.** Value matching shows that a number exists in the results, not that it is the intended quantity. The claim-bearing numbers are therefore also checked exactly by `tests/test_evidence_audit.py`: the EXP-002 and EXP-004 primary CIs and the two EXP-003 trigger-cell CIs in the manuscript and the claims register, all rows of manuscript Table 1 against `drift_family`, and all 18 rows of Table S2 against `cells` (mean, bootstrap CI, Holm CI, d_z, decision).
5. **Sources.** Each external statement in the manuscript was compared with what `research/literature_review.md` says was read.

## Findings

| Id | Finding | Severity | Action |
|---|---|---|---|
| F-1 | Raw outputs, checksums and provenance are complete and consistent (method items 1 and 2). | none | none |
| F-2 | `contrasts.csv` (all three experiments) writes the paired t interval columns as `np.float64(...)` strings: `write_tables` applies `repr` to numpy scalars. The values are correct and `analysis.json` holds plain floats. | low (format) | Fixed 2026-11-25 with the owner's approval (DEC-016): plain floats; the regenerated tables are value-identical, old hashes kept in DEC-016. |
| F-3 | The analysis code attaches a decision label to the per-accepted-item contrast using the 0.05 rad SESOI band, whose unit differs from rad per track. The label (in `analysis.json`) is meaningless; no report or the manuscript uses it. | low | Fixed 2026-11-25 with the owner's approval (DEC-016): label and band flag removed from `analysis.json`; supplementary S4 note dated. |
| F-4 | The EXP-002 report (section 9) and limitations item 13 call pi/2 a "ceiling". Drift ranges over [0, pi]; 4.2 % of EXP-002 RAND listener values exceed pi/2 (J-0008). | medium (wording, interpretation) | Fixed: dated correction note in the EXP-002 report and in limitations item 13 (DEC-015). No number changed. |
| F-5 | The registry status column still said "report.md not written" for all four experiments. | low (stale) | Fixed. |
| F-6 | The claims register lacked result id, config hash, figure or table and manuscript section, and had no rows for external claims, exposure results or the exploratory inspection. | medium | Fixed: columns added; C-008 to C-013 and X-001 to X-008 added; C-001, C-004, C-006 and C-007 qualified. |
| F-7 | Every decimal in the scoped documents maps to a committed file or a listed derivation (method items 3 and 4). | none | none |
| F-8 | External claims: 7 of 8 sources were read at abstract level only, and the manuscript now marks each as such. vargas2011 was read in full on 2026-11-25 (PDF SHA-256 3b5fad52...aa23, not committed): its equation 5 (self-information novelty) and equation 16 (intra-list distance, without rank and relevance) match ECHO's metrics, which closes the M1 open item. The kalimeris2021 and vargas2011 DOIs come from search results and were not opened. Citation chaining was not done. | medium (depth) | Disclosed in manuscript section 2 and limitations item 21. |
| F-9 | The file tool refused to write `research/report.md` ("Subagents should return findings as text"). Its text was returned to the coordinator. Its numbers are a subset of the manuscript's, but the script has not audited the file itself. | open | After the coordinator writes it: rerun `python3 scripts/build_artifact_manifest.py` and the test suite. |
| F-10 | Denominators and units: every contrast and arm has n_seeds = 10; the negative control covers 50 fixed runs in EXP-002 and in EXP-004; 4,951 eligible tracks matches `data/fma_calibration_v1.json`; drift is in rad, per-accept drift in rad per accepted track, Gini, discovery and skip rate are fractions. The manuscript's percentages (4.2 %, about 28 %) are converted from fractions in `confounders.json`. | none | none |
| F-11 | The first manuscript draft said "slightly less drift" in the abstract while the practical size is unresolved. (The EXP-002 report's "slightly" is followed by an explicit statement that practical size is unresolved and is left as written.) | low (overstatement) | Fixed in the abstract (second review pass R-11). |

## Strength and scope of evidence per conclusion

| Conclusion | Evidence | Strength | Scope |
|---|---|---|---|
| SIM minus RAND drift is negative on the calibrated synthetic catalogue at eta 0.05, consumed rule (C-001) | Confirmatory, 10 seeds, all negative | Moderate (CI excludes 0; practical size unresolved) | One rule, one rate, one catalogue |
| The direction is assumption-dependent (C-004) | Confirmatory, pre-registered rule; trigger cells not marginal | Strong within the tested grid | 3 rules x 3 rates x 2 profiles |
| The direction does not replicate on FMA (C-006) | Confirmatory, pre-registered reading, all seeds positive | Strong for the sign; widths may be optimistic | One embedding of one catalogue |
| Policies change exposure (C-009) | Descriptive secondaries | Strong but largely by construction | Both catalogues |
| Skip rate does not explain the SIM contrasts; it explains POP on FMA (C-011, C-007) | Exploratory side-by-side of committed outputs | Moderate | Both catalogues |
| Geometry differs between catalogues (C-012) | Exploratory, inputs only | Descriptive; causal role not tested | Ten confirmatory seeds |
