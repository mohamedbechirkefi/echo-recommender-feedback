<!-- SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0 -->
# ECHO research protocol

**Status: v1.0, frozen by the owner on 2026-11-24 (G-FREEZE; second-round approval "Approve all").** The SHA-256 of this file is recorded in `research/freeze.json` and the registry. Section 10 holds the amendments made before the freeze; it overrides the planning values in sections 3 to 9 where they differ.

Feasibility audit: `research/feasibility.md`. Literature: `research/literature_review.md`. Per-experiment protocols: `research/experiments/EXP-NNN/protocol.md`.

## 1. Research question

Can recommendation policies change exposure and simulated taste rather than simply reflect it?

Operational form: in a seeded simulation of listeners with either fixed or adaptive preference vectors, does the recommendation policy change the listeners' end-of-session preferences (beyond what a non-personalised uniform-random policy induces), and does it change what they are exposed to?

All results are simulation results. They hold only within the model assumptions in section 3. Simulated preference change is not evidence of human persuasion.

## 2. Hypotheses (primary)

- **Primary estimand.** Under adaptive preferences, the seed-level mean paired difference in preference drift between the similarity policy and the uniform-random baseline:
  `Delta = E_seed[ mean_u theta_u(SIM) - mean_u theta_u(RAND) ]`, in radians.
- **H0:** Delta = 0. The personalised similarity policy induces the same mean preference drift as uniform-random exposure.
- **H1 (non-directional):** Delta != 0.
- Rationale for non-directional H1: the literature supports both a narrowing mechanism (similarity recommendations pull users toward what they already like, so drift could be smaller than under random exposure) and an amplification mechanism (repeated exposure to one region moves the profile further in that direction). The draft does not prejudge the sign.
- **Smallest effect size of interest (SESOI):** 0.05 rad (about 2.9 degrees) of mean drift. Proposed by the AI; owner to confirm or replace.
- **Decision rule.** Reject H0 if the 95 % paired bootstrap CI of Delta excludes 0. Report "practically equivalent" only if the 95 % CI lies inside [-SESOI, +SESOI]. Otherwise report "inconclusive". Non-significance is never reported as equivalence.
- **What would contradict H1:** a 95 % CI for Delta inside [-0.05, 0.05] rad.
- **Negative control (must hold, not a hypothesis):** with fixed preferences (eta = 0), theta_u = 0 for every user and policy, exactly. Any non-zero value is an implementation defect and suspends the experiment.

## 3. Formal model (simulation, proposed)

- **Catalogue.** N tracks with unit-norm embeddings x_i in R^d. Embeddings are drawn from a mixture of K Gaussian "genre" clusters, then L2-normalised. Each track has a base popularity drawn from a Zipf law with exponent s, independent of the cluster.
- **Listeners.** U listeners per seed. The initial preference p_u,0 is a unit vector drawn near a randomly chosen cluster centre.
- **Session.** T steps. At each step the policy shows a slate of k tracks drawn from the candidates the listener has not yet consumed (candidate exclusion). The listener picks one track or skips. Choice is a softmax over cos(p_u,t, x_i) / tau for the slate plus a skip option with fixed utility.
- **Preference models.**
  - Fixed: p_u,t+1 = p_u,t.
  - Adaptive (default rule "consumed-item"): p_u,t+1 = normalise((1 - eta) p_u,t + eta x_chosen). No update on skip.
- **Recommender profile.** Personalised policies use an estimated profile p_hat = normalise(mean of consumed embeddings), cold-started from a short random warm-up. They never see the true p_u,t (the oracle profile is an ablation in EXP-003 only).
- **Policies.**
  - RAND (baseline): uniform random slate from the candidates.
  - POP: top-k candidates by current global consumption count plus base popularity.
  - SIM: top-k candidates by cos(p_hat, x_i).
  - MMR (diversity): maximal marginal relevance re-ranking of SIM with trade-off lambda.
  - EXPLORE: epsilon-greedy; each slot is a SIM pick with probability 1 - epsilon, otherwise a uniform random candidate.
- Draft parameter values (to be confirmed at freeze): N = 1000, d = 16, K = 10, s = 1.0, U = 200, T = 100, k = 10, tau = 0.1, eta = 0.05, warm-up = 5 steps, lambda = 0.5, epsilon = 0.2.

## 4. Metrics

| Metric | Formula | Unit | Role |
|---|---|---|---|
| Preference drift | theta_u = arccos(clip(<p_u,0, p_u,T>, -1, 1)), averaged over users | rad | **Primary** |
| Homogenisation | mean pairwise cosine of final preferences minus mean pairwise cosine of initial preferences | cosine (unitless) | Secondary |
| Discovery | distinct clusters consumed by the user / K | fraction | Secondary |
| Novelty | mean self-information -log2(pop_i / sum pop) of consumed tracks, using base popularity | bits | Secondary |
| Diversity | intra-list diversity: mean pairwise (1 - cos) within each slate, averaged over steps | unitless, [0, 2] | Secondary |
| Relevance | mean cos(p_u,0, x_chosen) (to initial taste) and mean cos(p_u,t, x_chosen) (to current taste) | cosine | Secondary |
| Exposure concentration | Gini coefficient of total slate impressions across tracks | [0, 1] | Secondary |
| Skip rate | skips / T | fraction | Diagnostic |

## 5. Design and analysis

- **Experimental unit.** One seed = one independently generated catalogue, listener population and random-number streams. Listeners within a seed are correlated (shared catalogue, shared POP counts) and are aggregated to a seed-level mean. The seed is the independent unit for inference.
- **Pairing.** Common random numbers: every policy within a seed sees the same catalogue, the same listeners and the same per-listener choice streams. Contrasts are paired by seed.
- **Seeds.** 10 confirmatory seeds per arm (at least 5 required). Confirmatory seeds are fixed in advance (20261124 + 0..9) and disjoint from smoke and exploratory seeds (900000 + i).
- **Sample-size rationale.** The simulation is cheap, so the seed count is set by precision. The exploratory smoke run (EXP-001) estimates the between-seed SD of the paired difference. If the projected 95 % CI half-width with 10 seeds exceeds SESOI / 2 = 0.025 rad, the seed count is raised to 30 before freezing. This decision uses only smoke seeds.
- **Uncertainty.** 95 % percentile bootstrap over seeds (10,000 resamples, fixed bootstrap seed) of the paired mean difference; also the paired t interval for comparison. Effect size d_z = mean difference / SD of differences. Raw per-seed values and per-listener distributions are exported.
- **Secondary contrasts.** POP, MMR and EXPLORE vs RAND on drift, and all policies on secondary metrics. Reported with Holm-adjusted intervals for the four drift contrasts and as descriptive for the rest. They do not change the primary conclusion.
- **Exclusion rules.** No listener or seed is excluded. A run that raises an error or produces a non-finite metric is recorded as failed with its traceback and reported. If more than 10 % of runs in an arm fail, the experiment stops and is reported as failed.
- **Stopping rule.** Fixed matrix, run in full. No optional stopping, no adding seeds after seeing confirmatory results.
- **No tuning on evaluation seeds.** Parameters are fixed at freeze from the literature and smoke seeds only.

## 6. Matrices

- **Smoke (EXP-001, exploratory):** 5 policies x 2 preference models x 2 smoke seeds, with N = 100, U = 20, T = 20. Purpose: determinism, negative control, schema validation, runtime estimate.
- **Full (EXP-002, confirmatory after freeze):** 5 policies x 2 preference models x 10 seeds = 100 runs at the section 3 values.
- **Sensitivity and ablation (EXP-003, confirmatory after freeze):** RAND and SIM only, adaptive preferences, eta in {0.01, 0.05, 0.2} x update rule in {consumed-item, exposure (slate mean), bounded-confidence (update only if cos > 0.5)} x profile in {estimated, oracle} x 10 seeds = 360 runs.

## 7. Sensitivity analysis that could invalidate the main interpretation

The primary contrast depends on an assumed drift mechanism. If the sign of Delta flips, or Delta becomes practically equivalent to zero, under another plausible update rule or drift rate (EXP-003), then the EXP-002 result is a property of the consumed-item update rule and not of the policy. In that case the main interpretation is withdrawn and reported as assumption-dependent. A second check: if Delta under the oracle profile differs in sign from Delta under the estimated profile, the effect comes from the profile estimator and not from the policy family.

## 8. Confounders and threats (summary)

Cluster geometry (d, K), popularity skew, choice temperature and skip utility all affect drift. Draft values are fixed in advance; the main ones are varied only in EXP-003. Synthetic listeners are not people. See `research/limitations.md`.

## 9. Compute budget

Local only (Apple M1 Pro, CPU). Expected cost of a full run: U x T x N cosine scores = 2 x 10^7 per run. That should take seconds per run, but this is an estimate, not a measurement. EXP-001 measures it. Hard cap: 2 hours of wall-clock for EXP-002 plus EXP-003. No cloud.

## 10. Amendments before freeze (owner-approved 2026-11-24, round 2)

Source: `labs/_shared/owner-approvals-2026-11-24b.md` (outside this repository), sections 1 and 7. The owner answered "Approve all" to the second-round list and "yes for all others" to the earlier amendment list. These amendments were written into this file before any fit to real data and before any confirmatory run. Where a fitted value replaces a planning value in sections 3 to 9, the fitted value wins; the earlier text is kept above for the record.

### 10.1 How real data enters the study (FMA metadata, CC BY 4.0)

- **Dataset.** FMA: A Dataset For Music Analysis, `fma_metadata.zip` (Defferrard et al., arXiv:1612.01840), from https://github.com/mdeff/fma. Metadata licence CC BY 4.0. Audio is never downloaded. Only `tracks.csv`, `genres.csv` and `features.csv` are read. Provenance (URL, access date, SHA-256, size) is in `data/manifest.json`.
- **What stays simulated.** Listeners, their initial tastes, their choices and their preference updates. FMA contains no listening sessions that this study uses; the play count is used only as a popularity signal. Artist, title and other descriptive text fields are never read into the processed data.
- **Splits.** FMA's own column `set/split` is used. The **calibration split** is `training`. The **second-test split** is `test`. The `validation` split is not used. Nothing fitted on the calibration split is evaluated on it, and the second-test catalogue never contributes to a fit except through the fixed PCA basis and genre centres, which come from the calibration split only.
- **Calibration of the synthetic model (EXP-002 and EXP-003).** Three planning values are replaced by values fitted on the calibration split, by the following methods, fixed before fitting:
  1. **K (number of genre clusters):** the number of top-level genres in `genres.csv` (rows whose `top_level` equals their own `genre_id`). Replaces the planning value K = 10.
  2. **Cluster weights:** the share of each top-level genre among calibration-split tracks whose `genre_top` is not missing, ordered by `genre_id` and rounded to 6 decimals. Tracks are assigned to clusters with these probabilities (`cluster_weights`), instead of uniformly. Listener home clusters stay uniform over the K clusters (listening is simulated and FMA has no listener data).
  3. **Zipf exponent s:** ordinary least squares of ln(listens) on ln(rank) over calibration-split tracks with listens >= 1, ranked 1..n by descending listens (ties do not change the fit); s = minus the slope, rounded to 4 decimals. Replaces the planning value s = 1.0. If the fitted s fell outside [0, 10] the calibration would stop and be reported; it would not be clipped.
  - The fit reads only FMA metadata. It runs no simulation, uses no seed, and does not involve any policy, so it cannot use the primary contrast in any way. It is journaled as an exploratory entry (J-0003), and the fitted values are written into `experiments/EXP-002/config.json` and `experiments/EXP-003/config.json` (block `base`).
  - The other parameters (d, N, U, T, k, tau, eta, warm-up, lambda, epsilon, spreads, skip utility) are not calibrated from FMA: they describe the simulated listener and recommender, which FMA does not observe.
- **Second test (EXP-004): the primary contrast on a real catalogue.** EXP-004 repeats the EXP-002 matrix (5 policies x fixed and adaptive preferences x the same 10 confirmatory seeds, the same parameters) with the synthetic catalogue replaced by real FMA tracks:
  - Eligible tracks: second-test split, `genre_top` not missing, all 518 librosa features finite. Exclusions are counted and reported by the ingestion step.
  - Embeddings: the 518 features are standardised with the calibration-split means and standard deviations (a zero SD is replaced by 1), projected onto the first d = 16 principal components of the standardised calibration-split features (genre-labelled tracks with finite features; component signs fixed so that the largest-magnitude loading is positive), then L2-normalised.
  - Clusters are the K top-level genres. Genre centres are the normalised means of the calibration-split embeddings of each genre. Simulated listeners start near a uniformly chosen genre centre exactly as in section 3.
  - Base popularity: listens + 1 (add-one, so tracks with zero plays stay eligible), scaled to sum to N within the sampled catalogue.
  - Per seed, N = 1000 tracks are drawn uniformly without replacement from the eligible set with the seed's catalogue stream.
  - The processed catalogue is identified by its SHA-256, which is part of every EXP-004 run configuration.
  - Primary estimand, decision rule, SESOI, uncertainty method and Holm family are those of EXP-002. EXP-004 is a pre-specified secondary test: it does not change the EXP-002 conclusion. Reading, fixed now: the EXP-002 direction **replicates on the real catalogue** if the EXP-004 Delta has the same sign as the EXP-002 Delta and its 95 % CI excludes 0; it **does not replicate** if the CI excludes 0 with the opposite sign or is practically equivalent to 0; otherwise it is **inconclusive on the real catalogue**.
  - No simulation was run on the real catalogue before the freeze.
- **Redistribution.** The archive is 342 MiB, above the 20 MB commit limit, so `data/raw/` and `data/processed/` are git-ignored and rebuilt by `scripts/download_fma_metadata.py` and `scripts/build_fma_catalogue.py`. Only aggregate calibration values (`data/fma_calibration_v1.json`) are committed. FMA holds no listener identifiers; artist fields are never processed.

### 10.2 Section 7 amendments (approved "yes for all others")

1. **Baseline.** RAND (uniform random slate) is confirmed as the primary comparator (DEC-005).
2. **Skip utility.** `skip_utility = 0` is kept. Disclosure: under this value the skip rate is close to zero for RAND, SIM, MMR and EXPLORE (at most 0.022 at full size in the exploratory EXP-001 run, J-0002) and noticeable only for POP (0.13 to 0.29). The skip-rate confounder named in EXP-002 is therefore active for POP only, and drift per accepted item is almost proportional to drift for the other policies. This is reported as a limitation.
3. **Seeds.** 10 confirmatory seeds per arm (20261124 to 20261133), confirmed. The pilot rule of section 5 was met (projected half-width 0.0114 rad < 0.025 rad, J-0002).
4. **Decision rule, completed.** When the 95 % CI of Delta excludes 0 and lies inside [-SESOI, +SESOI], the result is reported as **"statistically detectable, practically negligible"**. The other three readings of section 2 are unchanged.
5. **EXP-001 additions recorded.** The exploratory EXP-001 run added two blocks to the draft EXP-001 protocol: `timing` (5 policies x fixed and adaptive, seed 900012, full size) and `sensitivity_screen` (the 36 EXP-003 cells, seed 900012). They are recorded in `research/experiments/EXP-001/protocol.md` item 19.
6. **Disclosure of SIM minus RAND values already seen** (before the freeze, exploratory seeds only, at the draft K = 10 and s = 1.0, synthetic catalogue): pilot mean paired difference -0.15881 rad, SD 0.01587 rad, 10 seeds 900002 to 900011 (per-arm means RAND 0.642, SIM 0.483); one-seed screen at seed 900012 for all 18 EXP-003 cell pairs. Paths: `results/exploratory/EXP-001/report/summary.md` and `summary.json`; journal J-0002. The freeze record repeats them.

### 10.3 Implementation details frozen with the code

The implementation choices of DEC-006 (cluster spreads 0.1, Zipf weights over a random rank permutation, warm-up applied to the oracle profile too, MMR over the whole candidate set, synchronous POP counts, drift computed as 2 arcsin(||p_0 - p_T|| / 2)) are part of the frozen model as implemented at the freeze revision.

Any amendment after the freeze is dated, justified and kept separate from the frozen analysis.
