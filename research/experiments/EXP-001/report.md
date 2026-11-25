<!-- SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0 -->
# EXP-001 report: Simulator verification and smoke matrix (EXPLORATORY)

**This experiment is exploratory and verification only. It supports no confirmatory claim.**

## 1. Identification

- **Experiment:** EXP-001, simulator verification and smoke matrix.
- **Dates:**
  - First run 2026-11-24 (M2, commit b2e9738, journal J-0002).
  - Re-run 2026-11-25 (M3 smoke before the confirmatory runs, revision 04bc350, journal J-0004). The re-run outputs were committed in afc0850.
- **Protocol:** `research/experiments/EXP-001/protocol.md`, v1.0, SHA-256 `5d869d0f418956cdac48cb94a97a8a890aa96ba81193bb4a898664704830cff4`. The owner froze it on 2026-11-24 as the record of an exploratory experiment.
- **Status:** executed twice; all six verification checks pass in both runs.
- **Authorship:** Mohamed Bechir Kefi (owner-approved, C3). The AI assisted as a research and development assistant.
- **Report provenance:** written on the owner's approval of 2026-11-25 (DEC-014), from committed results only. Nothing was recomputed.

## 2. Executive summary

- **Question.** Does the simulator behave correctly (determinism, zero drift under fixed preferences, candidate exclusion, unit norms, metric bounds, schema)? What runtime and between-seed variance should size EXP-002?
- **Method.** 86 runs in four blocks, using exploratory seeds 900000 to 900012 only:
  - a smoke block: 5 policies x fixed and adaptive x 2 seeds, with N = 100, U = 20, T = 20;
  - a variance pilot: SIM and RAND, 10 seeds, full size;
  - a timing block;
  - a one-seed screen of the 36 EXP-003 cells.
- **Outcome.** Checks V1 to V6 pass.
  - The 2026-11-25 re-run produced 86 result files byte-identical to the 2026-11-24 run, at a different code revision and in a different process.
  - A separate smoke of the FMA catalogue code path (20 runs) also passes V1 to V6.
- **Principal caveat.** The pilot ran at the draft parameters (K = 10 uniform clusters, s = 1.0), before the FMA calibration. Its SIM minus RAND value was seen before the freeze. It is disclosed in protocol 10.2 item 6 and in `research/freeze.json`, and it is not a finding.

## 3. Rationale

EXP-002 to EXP-004 are interpretable only if the simulator operationalises the model of `research/protocol.md` section 3. A zero-drift negative control under fixed preferences shows that the drift metric measures only the update rule. Literature context: `research/literature_review.md`.

## 4. Hypotheses and operational definitions

These are pass or fail checks (protocol item 4):

- **V1:** identical config and seed give byte-identical result JSON.
- **V2:** with eta = 0, theta_u = 0 exactly for every listener and policy.
- **V3:** no consumed track reappears in a slate (re-checked from the per-step log).
- **V4:** embeddings and preferences have unit norm within 1e-12.
- **V5:** every metric lies inside its stated bounds (`src/echo/metrics.py`, METRIC_BOUNDS).
- **V6:** every result file validates against schema `echo.result.v1` on re-read.

Disconfirmation: any failed check means the implementation does not operationalise the protocol.

## 5. Methodology

- **Code:** `src/echo/` (simulation, metrics, schema, runner). The checks are in `src/echo/smoke.py`.
- **Config:** `experiments/EXP-001/config.json`. Its file SHA-256 is `7fee59c4d7587d12b2dd473b16977bc5d902a42092be3dd92da523c742b53176`, listed in `research/freeze.json`.
- **FMA-path smoke (M3 addition, exploratory):**
  - Config: `experiments/EXP-004/smoke_config.json`, the smoke block on the real FMA catalogue.
  - Processed catalogue SHA-256: `e5a0084a28a4afbcb8cc2f6b212c7de678ab21ebf3146e0066bef43172a8dd30`.
  - Seeds: 900000 and 900001.
- **Hardware and software:** Apple M1 Pro, 10 cores, 16 GiB, macOS 15.3.1; Python 3.12.1, numpy 2.2.6.
- **Budget:** 10 minutes planned. Actual on 2026-11-25, under `nice` on a shared machine:
  - 4 min 12 s for the 86 runs;
  - 1.2 s for the FMA-path smoke.

## 6. Implementation verification

- **Test suite before the M3 runs:** 174 passed (2026-11-25, `.venv/bin/python -m pytest -q`). It includes:
  - hand-computed metric cases (`tests/test_components.py`);
  - property tests;
  - a differential test against a loop reference (`tests/reference_sim.py`, `tests/test_simulation.py`).
- **Checks, 2026-11-25 run** (`results/exploratory/EXP-001-m3-smoke/checks.json`):
  - V1: 20 runs compared, 0 mismatches.
  - V2: 15 fixed runs, with every listener's drift exactly 0.
  - V3: 20 logged runs, 0 violations; the in-simulation counter is 0 over all runs.
  - V4: worst norm error 2.2e-16.
  - V5: 0 violations, 0 failed runs.
  - V6: 86 files valid.
- **FMA-path smoke** (`results/exploratory/EXP-004-smoke/checks.json`): V1 to V6 pass. The worst norm error is 3.3e-16, and all 20 files are valid.
- **Cross-revision determinism:** `diff -rq results/exploratory/EXP-001/runs results/exploratory/EXP-001-m3-smoke/runs` reports no difference over the 86 files.

## 7. Execution record

- **2026-11-24:** `PYTHONPATH=src uv run --frozen python -m echo.cli smoke` at b2e9738. 86 runs, 0 failed (J-0002).
- **2026-11-24T23:34:52Z UTC,** at 04bc350 with a clean code tree (J-0004):
  - `nice -n 10 env PYTHONPATH=src .venv/bin/python -m echo.cli smoke --out results/exploratory/EXP-001-m3-smoke`: 86 runs, 0 failed.
  - `... smoke --config experiments/EXP-004/smoke_config.json --out results/exploratory/EXP-004-smoke`: 20 runs, 0 failed.
- **Deviations:**
  - The `timing` and `sensitivity_screen` blocks (86 runs instead of 40) were recorded before the freeze (protocol item 19).
  - The FMA-path smoke is an M3 addition. It is exploratory and disclosed here, in J-0004 and in DEC-013.

## 8. Results

The generated summary of the first run is `results/exploratory/EXP-001/report/summary.md`, with tables, the pilot figure `fig-pilot-drift.svg` and a PDF. Its values are for planning only:

- **Pilot** (10 seeds, full size, adaptive, eta 0.05, draft parameters):
  - The SD of the paired SIM minus RAND drift difference was 0.01587 rad.
  - The projected 95 % half-width at 10 seeds is 0.0114 rad, below SESOI / 2 = 0.025 rad. So 10 confirmatory seeds were kept.
  - The mean paired difference (-0.15881 rad) is disclosed under C4 and not interpreted.
- **Runtime per full-size run** (2026-11-24, loaded machine): from 1.15 s (RAND) to 2.85 s (EXPLORE).
- **Degenerate cases:**
  - The skip rate is near zero except under POP (0.13 to 0.29).
  - RAND drift reaches 1.33 to 1.36 rad at eta 0.2 under the consumed and exposure rules.
  - No listener was frozen under the bounded rule.

## 9. Interpretation

The simulator meets every pre-stated verification check, deterministically across processes and code revisions. This shows that the implementation matches its specification. It says nothing about whether the model resembles real listeners.

## 10. Threats to validity

- The checks cover the stated invariants only, so an error that respects all of them would not be detected.
- The pilot SD came from the draft parameters, not the calibrated ones, and the seed-count decision rests on it. In the confirmatory runs, the SD of the SIM minus RAND difference was 0.0286 rad in EXP-002 (see the EXP-002 report), larger than the pilot's 0.0159 rad.
- The 2026-11-24 runtime measurements were made on a shared, loaded machine.

## 11. Conclusion

The implementation passes V1 to V6, so EXP-002 to EXP-004 could proceed. No research claim follows from EXP-001.

## 12. Reproduction appendix

- **Environment:** `../.tools/py/bin/uv sync --frozen --all-groups --all-extras` (from uv.lock), then `.venv/bin/python -m pytest`.
- **Commands:**
  - `PYTHONPATH=src .venv/bin/python -m echo.cli smoke --out results/exploratory/<dir>`
  - `PYTHONPATH=src .venv/bin/python -m echo.cli report results/exploratory/EXP-001`
- **Raw outputs** (runs, manifests, `checks.json`):
  - `results/exploratory/EXP-001/`
  - `results/exploratory/EXP-001-m3-smoke/`
  - `results/exploratory/EXP-004-smoke/`
- **Expected result:** byte-identical result JSON for identical config and seed.
