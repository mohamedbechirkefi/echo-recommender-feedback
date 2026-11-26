<!-- SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0 -->
# Roadmap

Target: five focused development days. The schedule is an estimate, never a reason to weaken evidence. Effort is given in focused days. "Done" means the gate was checked.

| ID | Milestone | Depends on | Priority | Effort | Status | Blockers |
|---|---|---|---|---|---|---|
| M0 | Bootstrap and feasibility | none | P0 | 0.5 | done (2026-11-24) | none |
| M1 | Research and preregistration | M0 | P0 | 0.5 | gate passed (2026-11-24: protocol v1.0 frozen by the owner, `research/freeze.json`); two literature items still open (citation chaining, Vargas and Castells check), carried to M4 | none for M3 |
| M2 | Core implementation | M1 drafts (the freeze is not needed to implement) | P0 | 1.5 | done (2026-11-24; gate checked, see progress.md session 2) | none |
| M3 | Experiments | M2; M1 freeze for confirmatory runs | P0 | 0.5 | gate holds (2026-11-25: complete planned matrix, 560/560 confirmatory runs ok, provenance captured); not closed: the four 11.3 experiment reports are not written | experiment reports (file tool refused them in the M3 session; DEC-013) |
| M4 | Interpretation | M3 | P0 | 0.75 | gate holds for every audited document (2026-11-25: 1311 numbers mapped, 0 unmatched; external claims mapped to read sources); closes when `research/report.md` is on disk and the manifest is rebuilt | `research/report.md` (file tool refused; text returned to the coordinator) |
| M5 | Interactive experience | M3 results (precomputed) | P1 | 0.75 | done (2026-11-25; gate checked: A11Y-CHECK PASS offline, 360 px, keyboard, contrast, reduced motion, no foreign request; numbers verbatim from the manuscript; DEC-018) | none |
| M6 | Release candidate | M4, M5 | P0 | 0.5 | release candidate prepared, awaiting owner review and G-PUBLIC (2026-11-25, 0.1.0-rc1; DEC-019) | owner sign-off of `research/publication/author_review.md`; owner approval for any publication (G-PUBLIC) |

## Acceptance criteria

### M0: Bootstrap and feasibility

**Gate:** the owner can understand the question, the cost and the exclusions.

- [x] Control files created (section 2).
- [x] Hardware and tools audited by command (`research/feasibility.md`).
- [x] Zero-cost toolchain confirmed by an exploratory smoke check (DEC-003).
- [x] Sources and data licences audited (`data/manifest.json`).
- [x] Explicit scope and fallback recorded.
- [x] `uv.lock` produced.

### M1: Research and preregistration

**Gate:** protocols are frozen before confirmatory runs, and exploratory results are visibly separated.

- [x] Registry initialised (EXP-001 to EXP-003; EXP-004 added 2026-11-24 for the real-data second test).
- [x] Manuscript skeleton (headings only).
- [x] Experiment-specific draft protocols (11.2).
- [x] Zero-cost local publication toolchain confirmed.
- [ ] Citation chaining from kalimeris2021 and carroll2022; `research/paper/references.bib` from verified sources only.
- [ ] Vargas and Castells metric definitions checked against the full paper.
- [x] Fixture manifest: synthetic FMA-schema fixture `tests/fixtures/fma_synthetic/` (no real rows); real data provenance in `data/manifest.json`.
- [x] EXP-001 pilot variance used to confirm the seed count (10 or 30): pilot SD 0.0159 rad, 10 seeds (owner-approved 2026-11-24).
- [x] **Owner freezes** the protocols (2026-11-24, "Approve all"). Hashes and approval in `research/freeze.json`, the registry and DEC-010.
- [x] Real data (FMA metadata, CC BY 4.0) adopted, calibrated and recorded (DEC-008, J-0003).

### M2: Core implementation

**Gate:** correctness before UI polish.

- [x] RAND baseline implemented first, then POP, SIM, MMR and EXPLORE.
- [x] Versioned JSON result schema with validation on export and import (11.6): `echo.result.v1`.
- [x] Run manifests: runtime, peak memory (process max RSS; tracemalloc peak with `--trace-memory`), OS, CPU, package versions, git revision, config hash.
- [x] Report generators built alongside the core (11.6): CSV, Markdown, SVG, PDF via pandoc to Typst.
- [x] Tests: cosine edge cases, normalisation, candidate exclusion, deterministic updates, zero drift under fixed preferences, hand-computed examples, property tests (hypothesis) and a differential test against a loop reference. 134 passed, 0 failed.
- [x] CLI commands: smoke, run (refuses confirmatory configs while unfrozen), report, test.
- [x] Exploratory EXP-001 run: checks V1 to V6 pass; runtime, seed spread and degenerate cases recorded (J-0002).
- [x] Holm adjustment for secondary contrasts (M3, `src/echo/analysis.py`, DEC-012).

### M3: Experiments

**Gate:** the planned matrix is complete or its failure is documented; no run is silently dropped.

- [x] EXP-001 executed (re-run 2026-11-25, J-0004). [ ] Its report written.
- [x] EXP-002, EXP-003 and EXP-004 executed after the freeze (2026-11-25, revision afc0850; J-0005 to J-0007).
- [ ] Reports generated as experiments finish (11.6): generated analysis tables and figures exist in `results/EXP-00N/analysis/`; the 11.3 reports are not written.
- [x] All unsuccessful runs and deviations recorded (0 failed runs; DEC-013).
- [x] Provenance captured at run time (per-run manifests with data hashes; `results/EXP-00N/provenance.csv`, `SHA256SUMS`).

### M4: Interpretation

**Gate:** every number maps to a result ID, a config and a figure, and every external claim maps to a verified source.

- [x] Confounders inspected (manuscript section 6 table; exploratory J-0008).
- [x] Sensitivity analysis (EXP-003) interpreted with the pre-specified retain or withdraw rule (withdrawn as assumption-dependent).
- [x] Claims register and claims audit completed, including a second pass that challenges the preferred hypothesis (`research/publication/claims_audit.md`, `review_pass_2.md`).
- [x] Manuscript synthesis includes contradictory results (11.6).
- [ ] `research/report.md` written (text composed in M4; the file tool refused it; the coordinator writes it, then reruns `python3 scripts/build_artifact_manifest.py`).

### M5: Interactive experience

**Gate:** offline after initial load, responsive, usable keyboard controls, no fabricated data, no runtime service.

- [x] Static taste map with recommendation trajectory and exploration controls (exploratory taste map from the Python engine; sandbox with seed, policy, update rule, eta, EXPLORE epsilon, run, cancel and reset).
- [x] Published results are kept separate from visitor sandbox runs (four distinct labels: measured, exploratory, sandbox, assumption).
- [x] Demo, paper, reports and articles use identical verified results (11.6): `tests/test_demo_export.py`; README, CITATION.cff, articles and demo README in the artifact-manifest scope (0 unmatched).

### M6: Release candidate

**Gate:** only verified facts are reported, and the owner approves any publication.

- [x] Clean-clone install from `uv.lock`, tests, smoke reproduction and demo build, with actual outputs recorded (`research/publication/reproducibility_report.md`).
- [x] Manuscript and report PDFs compiled and visually inspected (11.6): `scripts/build_publication_pdfs.py`, DEC-019.
- [x] References, links, equations and metadata verified: all 8 sources read in full (`claims_audit.md`, M6 table); `scripts/check_links.py`; PDF metadata checked with pypdf.
- [x] Secret, personal-data and licence scan (`release_checklist.md`; `dependency_licences.md`).
- [ ] Owner review checklist completed: prepared for the owner (`author_review.md`, M6 section); open until the owner signs it off.
- [ ] Nothing pushed without approval: nothing was pushed, tagged or released in M6. The coordinator pushed the repository on the owner's approval on 2026-11-25 (it is public); no tag or release exists, so the item stays open until the owner's release decision.
- Update (2026-11-26): demo given its own brand identity, motion and UI (owner request, `demo/DESIGN.md`); same data, tests and A11Y-CHECK PASS.

## Cut order if the five-day target is threatened

1. Optional demo features.
2. EXP-003 reduced to the update-rule factor at eta = 0.05 (the invalidation check is kept).
3. MMR arm.

Controls, reporting and evidence audits are never cut.
