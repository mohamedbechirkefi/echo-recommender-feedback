<!-- SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0 -->
# EXP-002 report: Policy effect on simulated taste and exposure (CONFIRMATORY, primary)

## 1. Identification

- **Experiment:** EXP-002, the primary confirmatory experiment.
- **Run date:** 2026-11-25. In UTC, runs started 2026-11-24T23:39:24Z and ended 23:44:15Z.
- **Protocol:** `research/experiments/EXP-002/protocol.md`, v1.0, SHA-256 `3852ad1950f73740378c6f19339d912da57c69daab82d218c3b8efb33af192b2`. It is governed by `research/protocol.md` v1.0 (SHA-256 `a81ed32c5e21f06e68d61e00250119762d1a56cdf4230a05ac3d89ff48c8f5dc`), which the owner froze on 2026-11-24 (DEC-010).
- **Config:** `experiments/EXP-002/config.json`, file SHA-256 `903f524679afb4a67fe4e6d36ff5b17f7f398475fa7f58c0c993846a64ef174c`.
- **Code revisions:**
  - Provenance revision of every run: afc08509847ac362b6b95d8097aea08a615f286b, with `code_dirty: false` in all 100 manifests.
  - The analysis code was committed in 04bc350, before any confirmatory output existed.
  - The results were committed in f40e935.
- **Status:** complete, 100 of 100 runs ok.
- **Authorship:** Mohamed Bechir Kefi (owner-approved, C3). The AI assisted as a research and development assistant. Written on the owner's approval of 2026-11-25 (DEC-014) from committed results only.

## 2. Executive summary

- **Question.** Under adaptive simulated preferences, does a personalised similarity policy (SIM) change listeners' end-of-session taste differently from uniform-random exposure (RAND)?
- **Method:**
  - 5 policies x fixed and adaptive preferences x 10 confirmatory seeds = 100 runs.
  - Synthetic catalogue calibrated on FMA metadata (K = 16, FMA genre weights, Zipf s = 1.3065).
  - Consumed-item update rule, eta 0.05.
  - Seed-paired analysis: 95 % percentile bootstrap with 10,000 resamples and seed 7.
- **Outcome.** Delta (SIM minus RAND drift) = -0.0355 rad, 95 % CI [-0.0535, -0.0200], d_z -1.24, n = 10 seeds. Under the frozen decision rule this is **reject H0**: SIM produced less drift than RAND.
- **Principal caveats:**
  - The point estimate is smaller than the SESOI (0.05 rad), and the CI extends past -0.05 rad, so practical size is unresolved.
  - Under the frozen EXP-003 rule the interpretation is **withdrawn as assumption-dependent**.
  - On the real FMA catalogue (EXP-004) the sign is reversed.

## 3. Rationale

- If simulated preferences move toward consumed items, a policy that controls exposure controls the direction of that movement.
- Prior simulation and modelling work motivates both narrowing and amplification mechanisms: kalimeris2021, jiang2019, chaney2018, mansoury2020 and carroll2022, verified from their abstracts. See `research/literature_review.md`.
- The gap addressed is a pre-registered, seed-paired comparison of policies against a non-personalised reference, under fixed and adaptive preferences, with the update-rule sensitivity tested separately in EXP-003.

## 4. Hypotheses and operational definitions

- **Primary estimand:**
  - `Delta = E_seed[ mean_u theta_u(SIM) - mean_u theta_u(RAND) ]`, in radians, under adaptive preferences.
  - Here theta_u is the angle between listener u's initial and final preference vectors.
- **Hypotheses:** H0 is Delta = 0; H1 is Delta != 0 (non-directional).
- **SESOI:** 0.05 rad.
- **Decision rule** (protocol section 2, with 10.2 item 4):
  - **Reject H0** if the 95 % CI excludes 0.
  - **Statistically detectable, practically negligible** if the CI excludes 0 and lies inside [-0.05, 0.05].
  - **Practically equivalent** if the CI includes 0 and lies inside the band.
  - **Inconclusive** otherwise.
- **Negative control:** under fixed preferences (eta = 0), drift must be exactly 0 for every listener and policy.
- **Secondary contrasts:**
  - POP, MMR and EXPLORE minus RAND on drift, with Holm-adjusted intervals over the family of four drift contrasts (including SIM).
  - Drift per accepted item, SIM minus RAND.
  - The other metrics, reported descriptively.
- **Disconfirmation:** a 95 % CI for Delta inside [-0.05, 0.05] rad.

## 5. Methodology

- **Model:** `research/protocol.md` sections 3 and 10. N = 1000 tracks, d = 16, U = 200 listeners, T = 100 steps, slate k = 10, tau = 0.1, warm-up 5 steps, MMR lambda 0.5, EXPLORE epsilon 0.2, `skip_utility = 0`.
- **Catalogue:** synthetic, with K = 16 clusters, cluster weights and Zipf s = 1.3065 fitted on the FMA training split (J-0003; `data/fma_calibration_v1.json`).
- **Seeds:** 20261124 to 20261133, with common random numbers across policies.
- **Data:** FMA metadata, CC BY 4.0 (`data/manifest.json`, SHA-256 `0db8d76f8dbc693496e7d5e5b35d9034fb98fd913d44ce379a9bb77669e0fae3`, recorded in every run manifest). It is used for calibration only, and listening is simulated.
- **Hardware:** Apple M1 Pro, 10 cores, 16 GiB, macOS 15.3.1. Two worker processes ran under `nice`, on a machine shared with other sessions (load average up to about 87).
- **Analysis:** `src/echo/analysis.py` (DEC-012, ratified by the owner on 2026-11-25, DEC-014):
  - percentile bootstrap (10,000 resamples, seed 7), paired t interval and d_z;
  - Holm step-down on two-sided bootstrap p-values, with each contrast's interval at level 1 - 0.05 / (m - i + 1).
- **Budget:** at most 1 hour; actual 4 min 51 s.

## 6. Implementation verification

- **Before the runs:**
  - Every frozen hash matched the files on disk.
  - The test suite passed (174 tests).
  - The EXP-001 smoke re-run passed V1 to V6, with results byte-identical to M2 (see the EXP-001 report).
- **Negative control in this experiment:** pass. Drift was exactly 0 for every listener in all 50 fixed-preference runs.
- **Analysis code:** tested on hand-built inputs (`tests/test_analysis.py`: bootstrap identity with `stats.paired_bootstrap_ci`, hand-computed Holm, decision readings, negative-control and stop-rule detection).

## 7. Execution record

- **Commands:**
  - `nice -n 10 env PYTHONPATH=src .venv/bin/python -m echo.cli run --config experiments/EXP-002/config.json`, through the run guard (frozen config and protocol hashes checked).
  - `PYTHONPATH=src .venv/bin/python -m echo.analysis results/EXP-002 --planned 100 --kind policy`
- **Runs:** 100 planned, 100 ok, 0 failed, 0 retried, 0 excluded.
- **Run IDs:** `EXP-002_main_<POLICY>_<fixed-0.0|adaptive-0.05>_s<seed>`.
- **Per-run provenance** (run id, config hash, seed, revision, data-manifest hash, hardware, start and end, status): `results/EXP-002/provenance.csv`. Log: `results/logs/EXP-002.log`.
- **Deviations from the frozen protocol:** none.
  - Analysis choices that the frozen text left open (the Holm construction) were fixed in DEC-012 before any output, then ratified by the owner (DEC-014).
  - Per-run runtimes are upper bounds because the machine was loaded.

## 8. Results

All values come from `results/EXP-002/analysis/analysis.json` (tables `contrasts.csv`, `arms.csv`, `per_seed.csv`; generated summary `analysis.md`).

### 8.1 Drift contrasts versus RAND (adaptive, seed-paired, rad, n = 10 seeds)

| Contrast | Mean diff | SD | 95 % bootstrap CI | 95 % paired t CI | d_z | Decision | Holm level | Holm CI | Holm reject |
|---|---|---|---|---|---|---|---|---|---|
| SIM-RAND (primary) | -0.0355 | 0.0286 | [-0.0535, -0.0200] | [-0.0560, -0.0151] | -1.24 | reject H0 | 0.9500 | [-0.0535, -0.0200] | yes |
| POP-RAND | 0.1630 | 0.0312 | [0.1443, 0.1810] | [0.1407, 0.1853] | 5.22 | reject H0 | 0.9750 | [0.1418, 0.1834] | yes |
| MMR-RAND | -0.1162 | 0.0278 | [-0.1339, -0.1009] | [-0.1361, -0.0963] | -4.18 | reject H0 | 0.9833 | [-0.1377, -0.0983] | yes |
| EXPLORE-RAND | -0.0381 | 0.0300 | [-0.0570, -0.0219] | [-0.0595, -0.0167] | -1.27 | reject H0 | 0.9875 | [-0.0625, -0.0186] | yes |

- All four bootstrap p-values are reported as 0.0000: no resample fell on the other side of 0.
- Holm ranks among these ties follow the contrast name. This changes the interval levels only, not any rejection (limitations item 14).

Figure: `results/EXP-002/analysis/fig-contrasts.svg`, a forest plot.
- Dots: mean paired difference.
- Thick bars: 95 % bootstrap CI.
- Thin bars: Holm-level CI.
- Grey band: the SESOI of plus or minus 0.05 rad.
- n = 10 seeds.

### 8.2 Pre-specified secondary: drift per accepted item

SIM minus RAND: -0.000419 rad per accepted track, 95 % CI [-0.000605, -0.000263]. Skips are rare under SIM and RAND, so this tracks the primary contrast.

### 8.3 Per-policy means, adaptive preferences (seed-level means; drift with 95 % bootstrap CI)

| Policy | Drift (rad) [95 % CI] | Homogenisation | Discovery | Skip rate | Exposure Gini |
|---|---|---|---|---|---|
| RAND | 1.1119 [1.0805, 1.1404] | 0.358 | 0.376 | 0.006 | 0.040 |
| POP | 1.2749 [1.2513, 1.2966] | 0.901 | 0.664 | 0.052 | 0.950 |
| SIM | 1.0763 [1.0467, 1.1035] | 0.244 | 0.185 | 0.001 | 0.552 |
| MMR | 0.9956 [0.9710, 1.0181] | 0.219 | 0.290 | 0.002 | 0.378 |
| EXPLORE | 1.0738 [1.0446, 1.1005] | 0.243 | 0.190 | 0.001 | 0.440 |

- Figure: `results/EXP-002/analysis/fig-arms-drift.svg`, mean drift per policy with 95 % bootstrap CI over 10 seeds. Fixed arms have drift exactly 0 and are not drawn.
- Descriptive CIs for all ten metrics and both preference models are in `arms.csv` and `analysis.md`.
- Under fixed preferences drift is exactly 0 in every arm.

## 9. Interpretation

- **Expected versus observed:**
  - H1 was non-directional. The pre-freeze pilot, at draft parameters (K = 10 uniform, s = 1.0), had shown SIM below RAND by -0.15881 rad (disclosed, C4).
  - At the calibrated parameters the observed direction is the same, but the magnitude is much smaller: -0.0355 rad.
  - The confirmatory SD of the paired differences (0.0286 rad) was larger than the pilot's (0.0159 rad). The CI half-width is still about 0.017 rad.
- **Measured:** in this model, at these parameters, SIM produced slightly less mean drift than uniform-random exposure. It also produced much lower homogenisation (0.244 vs 0.358) and discovery (0.185 vs 0.376), and much higher exposure concentration (Gini 0.552 vs 0.040).
- **Practical size:**
  - The CI excludes 0 but not -SESOI: the effect could be smaller or larger than 0.05 rad.
  - The frozen label is "reject H0", not "practically negligible", because the CI is not inside the band.
  - It would be an over-reading to call the SIM-RAND drift difference practically important.
- **Competing explanations:**
  - **Skip rate:** skips are near zero for SIM and RAND (0.001 and 0.006), so this confounder does not explain the primary contrast. It does apply to POP (0.052).
  - **Profile estimator, update rule and rate:** tested in EXP-003. There the contrast is reversed or vanishes under other rules and rates, and the interpretation is withdrawn.
  - **Catalogue geometry:** tested in EXP-004, where the sign reverses on real FMA tracks.
- **Compression:** RAND drift is about 1.11 rad against a pi/2 ceiling for most listeners, so the contrasts may be compressed (protocol item 16).

## 10. Threats to validity

- **Internal:** common random numbers make the contrasts seed-paired; the negative control passed. Implementation choices frozen with the code (DEC-006) may shape the result.
- **Construct:** drift is the angle between the initial and final preference vectors. It does not say toward what the listener moved.
- **External:** these are simulated listeners on a stylised catalogue (Gaussian clusters with FMA-fitted weights and popularity). The result is not evidence about human listeners or any commercial service.
- **Statistical:**
  - Only 10 seeds.
  - The percentile bootstrap with n = 10 can under-cover; the paired t interval ([-0.0560, -0.0151]) agrees in sign and order of magnitude.
  - The Holm construction is described in DEC-012.
- **Assumption dependence:** shown directly by EXP-003 (withdrawn) and EXP-004 (opposite sign).

## 11. Conclusion and next experiment

- Under the frozen rule, H0 is rejected for EXP-002: SIM minus RAND drift = -0.0355 rad, 95 % CI [-0.0535, -0.0200].
- The pre-registered robustness test withdraws this as a general statement about the policy. It is a property of the consumed-item update rule at eta 0.05 on this calibrated synthetic catalogue.
- The real-catalogue second test does not replicate it.
- Next step (M4): interpret EXP-002 to EXP-004 together. Report the direction of drift as model-dependent, and examine why catalogue geometry reverses the sign. Any new design is a new experiment with its own protocol.

## 12. Reproduction appendix

- **Environment:**
  - `../.tools/py/bin/uv sync --frozen --all-groups --all-extras` (uv.lock; numpy 2.2.6, Python 3.12.1).
  - `.venv/bin/python -m pytest` (174 passed at 04bc350 and after the runs).
- **Run:** `PYTHONPATH=src .venv/bin/python -m echo.cli run --config experiments/EXP-002/config.json`. The guard refuses the run if the config or protocol hash differs from `research/freeze.json`.
- **Analysis, tables and figures:** `PYTHONPATH=src .venv/bin/python -m echo.analysis results/EXP-002 --planned 100 --kind policy`.
- **Raw results:**
  - `results/EXP-002/runs/*.json` (schema `echo.result.v1`, validated on read);
  - manifests in `results/EXP-002/manifests/`;
  - checksums of every file in `results/EXP-002/SHA256SUMS`.
- **Expected:** result JSON byte-identical for identical config, seed and numpy build.
- **Records:** journal J-0005; claims C-001, C-002, C-003; decisions DEC-012, DEC-013, DEC-014.
