<!-- SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0 -->
# EXP-004 report: The policy contrast on a real music catalogue (FMA), second test (CONFIRMATORY, secondary)

## 1. Identification

- **Experiment:** EXP-004, the pre-specified second test of the EXP-002 contrast on real FMA tracks.
- **Run date:** 2026-11-25. In UTC, runs started 2026-11-24T23:44:16Z and ended 23:48:34Z.
- **Protocol:** `research/experiments/EXP-004/protocol.md`, v1.0, SHA-256 `4f6a5ca60c788a2bee49abaef5af3ca2c039152d1ec0569ab4d54c0f79d75402`. It is governed by `research/protocol.md` v1.0, section 10.1, which the owner froze on 2026-11-24.
- **Config:** `experiments/EXP-004/config.json`, file SHA-256 `efb26feb7078799642631b15e6ec4604b59aebf49405c6ff3dec8bf3ad55560d`.
- **Processed FMA catalogue:** SHA-256 `e5a0084a28a4afbcb8cc2f6b212c7de678ab21ebf3146e0066bef43172a8dd30`, checked at run time.
- **Raw archive:** SHA-256 `d9527a5297a65da31c5676484d5047c3e2b8a8060ce72a46e26158be736bf265`, checked before the runs.
- **Code revisions:**
  - Provenance revision: afc08509847ac362b6b95d8097aea08a615f286b, with `code_dirty: false` in all 100 manifests.
  - Analysis code: 04bc350.
  - Results: f40e935.
- **Status:** complete, 100 of 100 runs ok.
- **Authorship:** Mohamed Bechir Kefi, independent researcher (owner-approved, C3; owner, 2026-11-26, decision sheet); the AI assisted. Written on the owner's approval of 2026-11-25 (DEC-014) from committed results only.

## 2. Executive summary

- **Question.** Does the EXP-002 SIM versus RAND drift contrast hold when the synthetic catalogue is replaced by real FMA tracks (real audio-feature geometry, genres and play-count popularity), with listeners still simulated?
- **Method:**
  - The EXP-002 matrix: 5 policies x fixed and adaptive x the same 10 seeds = 100 runs.
  - Each seed samples 1000 of the 4,951 eligible FMA test-split tracks.
- **Outcome.** Delta_FMA = +0.1652 rad, 95 % CI [0.1560, 0.1735], d_z 11.15. Under the frozen rule this is **reject H0 with the opposite sign to EXP-002**. The pre-stated reading is **does not replicate**.
- **Principal caveat.** The real catalogue is one similarity space (PCA-16 of librosa statistics). The reversal may come from this embedding, the unbalanced genres or the heavier popularity tail, not from "realism" in general.

## 3. Rationale

- The EXP-002 catalogue is made of Gaussian clusters on a sphere.
- If the policy effect depends on that stylised geometry, it should change on a real catalogue.
- The owner approved real data on 2026-11-24 ("FMA metadata, CC BY 4.0. Real catalogue and genres; listening stays simulated."). The method was fixed in protocol 10.1 before any fit, and no simulation on the real catalogue was run before the freeze.

## 4. Hypotheses and operational definitions

- **Estimand and hypotheses:**
  - H0: Delta_FMA = 0; H1: Delta_FMA != 0.
  - Delta_FMA is the seed-paired SIM minus RAND mean drift, adaptive preferences, on the FMA catalogue.
  - SESOI 0.05 rad. Decision rule as in EXP-002.
- **Reading against EXP-002** (protocol 10.1, fixed before the freeze):
  - **Replicates** if Delta_FMA has the EXP-002 sign and its CI excludes 0.
  - **Does not replicate** if its CI excludes 0 with the opposite sign, or it is practically equivalent to 0.
  - **Inconclusive** otherwise.
  - Both equivalence readings of DEC-012 are evaluated; DEC-012 was ratified by the owner on 2026-11-25.
- **Negative control:** drift is exactly 0 under fixed preferences.
- **Secondaries:** as in EXP-002, with the Holm family of four drift contrasts.

## 5. Methodology

- **Data:** FMA metadata (Defferrard et al., arXiv:1612.01840), CC BY 4.0. Only the test split is used.
  - Tracks are eligible if they have a top-level genre and all 518 librosa features are finite: 4,951 tracks.
  - Features are standardised with training-split statistics, projected on the first 16 training-split principal components, then L2-normalised.
  - Clusters are the 16 top-level genres.
  - Popularity is listens + 1.
- **Listeners:** simulated as in `research/protocol.md` section 3. No real listener data is used.
- **Parameters:** as EXP-002 (N = 1000 sampled tracks per seed, U = 200, T = 100, k = 10, eta 0.05, `skip_utility = 0`).
- **Seeds:** 20261124 to 20261133, with common random numbers. The catalogue sample depends only on the seed.
- **Hardware:** Apple M1 Pro. One of two worker processes ran under `nice` on a shared machine.
- **Budget:** at most 1 hour; actual 4 min 18 s.

## 6. Implementation verification

- **Before the runs:**
  - The raw and processed FMA hashes matched the freeze record.
  - An exploratory smoke of the FMA code path (20 runs, smoke size, seeds 900000 and 900001) passed V1 to V6 (J-0004; `results/exploratory/EXP-004-smoke/`). Its SIM minus RAND values were not inspected.
- **Negative control in this experiment:** pass. Drift was exactly 0 for every listener in all 50 fixed runs.

## 7. Execution record

- **Commands:**
  - `nice -n 10 env PYTHONPATH=src .venv/bin/python -m echo.cli run --config experiments/EXP-004/config.json`, through the run guard. The guard checked the config hash and protocol hash, and the run checked the catalogue SHA-256.
  - `PYTHONPATH=src .venv/bin/python -m echo.analysis results/EXP-004 --planned 100 --kind replication --reference results/EXP-002/analysis/analysis.json`
- **Runs:** 100 planned, 100 ok, 0 failed, 0 retried, 0 excluded.
- **Run IDs:** `EXP-004_fma_<POLICY>_<fixed-0.0|adaptive-0.05>_s<seed>`.
- **Provenance:** `results/EXP-004/provenance.csv`. Log: `results/logs/EXP-004.log`.
- **Deviations from the frozen protocol:** none. The FMA-path smoke was an exploratory addition (DEC-013).

## 8. Results

All values come from `results/EXP-004/analysis/analysis.json` (`contrasts.csv`, `arms.csv`, `per_seed.csv`, `analysis.md`).

### 8.1 Drift contrasts versus RAND (adaptive, seed-paired, rad, n = 10 seeds)

| Contrast | Mean diff | SD | 95 % bootstrap CI | 95 % paired t CI | d_z | p (boot) | Decision | Holm level | Holm CI | Holm reject |
|---|---|---|---|---|---|---|---|---|---|---|
| SIM-RAND (primary) | 0.1652 | 0.0148 | [0.1560, 0.1735] | [0.1546, 0.1758] | 11.15 | 0.0000 | reject H0 | 0.9750 | [0.1547, 0.1749] | yes |
| POP-RAND | -0.0357 | 0.0617 | [-0.0723, 0.0005] | [-0.0799, 0.0084] | -0.58 | 0.0542 | inconclusive | 0.9500 | [-0.0723, 0.0005] | no |
| MMR-RAND | 0.0570 | 0.0120 | [0.0502, 0.0643] | [0.0484, 0.0656] | 4.76 | 0.0000 | reject H0 | 0.9833 | [0.0490, 0.0660] | yes |
| EXPLORE-RAND | 0.1631 | 0.0153 | [0.1539, 0.1720] | [0.1521, 0.1740] | 10.66 | 0.0000 | reject H0 | 0.9875 | [0.1516, 0.1744] | yes |

Figure: `results/EXP-004/analysis/fig-contrasts.svg`, a forest plot with the same encoding as EXP-002. n = 10 seeds.

### 8.2 Reading against EXP-002

- Band reading: does not replicate. Label reading: does not replicate. The readings agree.
- **Reading: does not replicate.**

### 8.3 Pre-specified secondary: drift per accepted item

SIM minus RAND: +0.001581 rad per accepted track, 95 % CI [0.001489, 0.001664].

### 8.4 Per-policy means, adaptive preferences (seed-level means; drift with 95 % bootstrap CI)

| Policy | Drift (rad) [95 % CI] | Homogenisation | Discovery | Skip rate | Exposure Gini |
|---|---|---|---|---|---|
| RAND | 0.6933 [0.6794, 0.7070] | 0.159 | 0.713 | 0.011 | 0.047 |
| POP | 0.6576 [0.6205, 0.6893] | 0.503 | 0.694 | 0.325 | 0.961 |
| SIM | 0.8585 [0.8427, 0.8739] | 0.187 | 0.660 | 0.001 | 0.726 |
| MMR | 0.7503 [0.7409, 0.7606] | 0.146 | 0.656 | 0.001 | 0.477 |
| EXPLORE | 0.8564 [0.8395, 0.8730] | 0.180 | 0.658 | 0.001 | 0.579 |

- Figure: `results/EXP-004/analysis/fig-arms-drift.svg`, mean drift per policy with 95 % bootstrap CI over 10 seeds.
- Full descriptive CIs: `arms.csv`.

## 9. Interpretation

- **Expected versus observed.** The test was set up to see whether EXP-002's direction (SIM below RAND) carries over. It does not:
  - On real FMA tracks, SIM drifts more than RAND by 0.1652 rad.
  - MMR and EXPLORE also drift more than RAND, the reverse of EXP-002.
- **Measured differences between catalogues:**
  - RAND drift is much lower on FMA (0.6933 rad) than on the calibrated synthetic catalogue (1.1119 rad in EXP-002).
  - Discovery under SIM is much higher on FMA (0.660 vs 0.185).
  - Both are consistent with genre centres lying close together in the PCA space, as anticipated in protocol item 16.
- **Competing explanations** (protocol item 3), not separated by this design:
  - the embedding (PCA-16 of librosa statistics is one of many similarity spaces);
  - the unbalanced genre sizes;
  - the heavier popularity tail.
- **POP:** the contrast is inconclusive (CI [-0.0723, 0.0005]). POP's skip rate is 0.325 against 0.011 for RAND, so the skip-rate confounder is strong for POP here.
- **Taken with EXP-003:** the evidence does not support a policy-level statement about the direction of simulated taste change.

## 10. Threats to validity

- **Construct:** audio-feature similarity is not listener-perceived similarity. FMA is a catalogue of freely licensed music, not of a commercial service.
- **External:** listeners are simulated; no claim about human listeners or any proprietary recommender follows.
- **Statistical:**
  - 10 seeds.
  - Each seed samples 1000 of 4,951 tracks, so the seeds share tracks.
  - The very large d_z reflects a small between-seed SD, not a large practical effect in human terms.
- **Internal:** same code and checks as EXP-002; the negative control passed.

## 11. Conclusion and next experiment

- Under the frozen rule, EXP-004 rejects H0 with the opposite sign: Delta_FMA = +0.1652 rad, 95 % CI [0.1560, 0.1735].
- The EXP-002 direction **does not replicate** on the real catalogue.
- In M4 the manuscript reports this as a contradicting result, alongside EXP-003.
- A follow-up separating embedding, genre balance and popularity effects would be a new experiment with its own protocol.

## 12. Reproduction appendix

- **Data:**
  - `python3 scripts/download_fma_metadata.py` (358,412,441 bytes; SHA-256 above).
  - `PYTHONPATH=src .venv/bin/python scripts/build_fma_catalogue.py` (the processed SHA-256 must equal `e5a0084a...dd30`, or the run refuses).
- **Run:** `PYTHONPATH=src .venv/bin/python -m echo.cli run --config experiments/EXP-004/config.json`
- **Analysis:** `PYTHONPATH=src .venv/bin/python -m echo.analysis results/EXP-004 --planned 100 --kind replication --reference results/EXP-002/analysis/analysis.json`
- **Raw results:** `results/EXP-004/runs/`, `manifests/`, `provenance.csv`, `SHA256SUMS`. Row-level FMA data is not committed; `data/raw/` and `data/processed/` are git-ignored.
- **Records:** journal J-0007; claims C-003, C-006, C-007; decisions DEC-012, DEC-013, DEC-014.
