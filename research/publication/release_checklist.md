<!-- SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0 -->
# Release checklist (owner-controlled; nothing is published without owner approval)

Status, 2026-11-25 (M6): release candidate 0.1.0-rc1 prepared; awaiting the owner's review (`author_review.md`) and G-PUBLIC. Ticks below were verified in the M6 session of 2026-11-25; the evidence follows each item.

- [x] Owner has frozen all confirmatory protocols (hash recorded in the registry). Evidence: `research/freeze.json` (DEC-010); SHA-256 of the 5 protocols, 4 configs and 2 data files recomputed: 11 of 11 match.
- [x] Every registered experiment has a truthful standalone report (11.3). Evidence: `research/experiment_registry.csv` lists EXP-001 to EXP-004; `research/experiments/EXP-00N/report.md` exists for all 4 and compiles to PDF.
- [x] Manuscript complete; PDF compiled and visually inspected. Evidence: `scripts/build_publication_pdfs.py`; `research/paper/manuscript.pdf` 14 pages, every page inspected at 60 ppi; PDF title set, no e-mail address, no local path (pypdf).
- [x] Every number in the manuscript, reports, demo and articles maps to a result artifact (artifact_manifest.json). Evidence: `scripts/build_artifact_manifest.py`: 1441 mapped, 0 unmatched; `tests/test_evidence_audit.py` and `tests/test_demo_export.py` pass.
- [x] claims_audit.md completed; unsupported claims removed or qualified. Evidence: `claims_audit.md` M6 reference table; all 8 sources read in full; F-12 (carroll2022) corrected, F-13 (introduction) reworded.
- [x] Clean clone: locked install, tests, smoke reproduction (reproducibility_report.md). Evidence: 183 passed in the clone; smoke 86 of 86 ok, V1 to V6 PASS, 86 result files byte-identical.
- [x] Demo builds, works offline, keyboard accessible, fails closed on bad results. Evidence: clone `npm test` 29 passed, `npm run build`, `A11Y-CHECK PASS`; negative check with a corrupted `results.json`: "0 experiment panels", `A11Y-CHECK FAIL (2)`.
- [x] Data manifest and licences verified; no non-redistributable data bundled. Evidence: `data/manifest.json` SHA-256 of the FMA archive and processed catalogue recomputed, both match; only `data/manifest.json` and `data/fma_calibration_v1.json` (aggregates) are tracked under `data/`; `dependency_licences.md`: no flags.
- [x] Secret and personal-data scan clean. Evidence: `git ls-files` (1663 files at the start of M6): 0 e-mail addresses, 0 private-key headers or token patterns, 0 `.env` files; absolute home paths removed from `CLAUDE.md` and `research/feasibility.md`; 2 remain in the append-only `progress.md` (M0 commands), with a note appended there.
- [x] Licence files unchanged; SPDX headers present. Evidence: `LICENSE`, `NOTICE.md`, `LICENSE_HISTORY.md`, `CLA.md`, `.github/` last changed in bc5bb42 (the owner's repository rename, 2026-11-24) and untouched since; SPDX header on every text file added since M0, except the committed generated `results/exploratory/EXP-001/report/summary.typ` (a result artifact, left unchanged).
- [ ] author_review.md signed off by the owner
- [ ] Owner explicitly approves any push, release or publication
