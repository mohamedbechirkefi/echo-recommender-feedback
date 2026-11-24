<!-- SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0 -->
# Roadmap

Target: five focused development days. The schedule is an estimate, never a reason to weaken evidence. Effort is given in focused days. "Done" means the gate was checked.

| ID | Milestone | Depends on | Priority | Effort | Status | Blockers |
|---|---|---|---|---|---|---|
| M0 | Bootstrap and feasibility | none | P0 | 0.5 | done (2026-11-24) | none |
| M1 | Research and preregistration | M0 | P0 | 0.5 | gate passed (2026-11-24: protocol v1.0 frozen by the owner, `research/freeze.json`); two literature items still open (citation chaining, Vargas and Castells check), carried to M4 | none for M3 |
| M2 | Core implementation | M1 drafts (the freeze is not needed to implement) | P0 | 1.5 | done (2026-11-24; gate checked, see progress.md session 2) | none |
| M3 | Experiments | M2; M1 freeze for confirmatory runs | P0 | 0.5 | gate holds (2026-11-25: complete planned matrix, 560/560 confirmatory runs ok, provenance captured); not closed: the four 11.3 experiment reports are not written | experiment reports (file tool refused them in the M3 session; DEC-013) |
| M4 | Interpretation | M3 | P0 | 0.75 | not started | none |
| M5 | Interactive experience | M3 results (precomputed) | P1 | 0.75 | not started | none |
| M6 | Release candidate | M4, M5 | P0 | 0.5 | not started | owner approval for any publication (G-PUBLIC) |

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

- [ ] Confounders inspected.
- [ ] Sensitivity analysis (EXP-003) interpreted with the pre-specified retain or withdraw rule.
- [ ] Claims register and claims audit completed, including a second pass that challenges the preferred hypothesis.
- [ ] Manuscript synthesis includes contradictory results (11.6).
- [ ] `research/report.md` written.

### M5: Interactive experience

**Gate:** offline after initial load, responsive, usable keyboard controls, no fabricated data, no runtime service.

- [ ] Static taste map with recommendation trajectory and exploration controls.
- [ ] Published results are kept separate from visitor sandbox runs.
- [ ] Demo, paper, reports and articles use identical verified results (11.6).

### M6: Release candidate

**Gate:** only verified facts are reported, and the owner approves any publication.

- [ ] Clean-clone install from `uv.lock`, tests, smoke reproduction and demo build, with actual outputs recorded.
- [ ] Manuscript and report PDFs compiled and visually inspected (11.6).
- [ ] References, links, equations and metadata verified.
- [ ] Secret, personal-data and licence scan.
- [ ] Owner review checklist completed.
- [ ] Nothing pushed without approval.

## Cut order if the five-day target is threatened

1. Optional demo features.
2. EXP-003 reduced to the update-rule factor at eta = 0.05 (the invalidation check is kept).
3. MMR arm.

Controls, reporting and evidence audits are never cut.
