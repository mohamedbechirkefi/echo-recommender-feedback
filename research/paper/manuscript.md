<!-- SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0 -->
# Does a similarity recommender shape simulated taste? A pre-registered simulation with an assumption-sensitivity test and a real-catalogue second test

**Status: independent research manuscript / preprint draft, not peer-reviewed.** Release candidate 0.1.0-rc1, 2026-11-26. All findings are simulation results; simulated preference change is not evidence of human persuasion.

## Author and affiliation metadata

Mohamed Bechir Kefi, independent researcher (owner-approved; owner, 2026-11-26, decision sheet). An AI system (Claude, Anthropic) assisted with research engineering, analysis code and drafting as a disclosed research and development assistant. It is not an author. See section 11.

Data: FMA metadata (Defferrard et al., arXiv:1612.01840), CC BY 4.0. No audio was downloaded and no listener data exists in this study.

## Abstract

Recommender systems decide what listeners are exposed to; if tastes adapt to what is consumed, the recommender may shape the preferences it is meant to reflect. We ask, in a seeded simulation, whether a personalised similarity policy (SIM) changes simulated listeners' end-of-session taste differently from uniform-random exposure (RAND). The protocol, decision rule and smallest effect size of interest (0.05 rad) were frozen by the owner before any confirmatory run. The primary experiment (EXP-002; 5 policies, fixed and adaptive preferences, 10 seeds, synthetic catalogue calibrated on FMA metadata) found that SIM produced less angular preference drift than RAND: Delta = -0.0355 rad, 95 % bootstrap CI [-0.0535, -0.0200], so H0 was rejected; whether the difference is practically relevant is unresolved. The pre-registered sensitivity experiment (EXP-003, 360 runs) withdrew this interpretation as assumption-dependent: under a bounded-confidence update rule at the same rate the contrast was practically equivalent to zero (+0.0069 rad, CI [-0.0130, 0.0303]) or reversed with an oracle profile (+0.1883 rad, CI [0.1598, 0.2196]), and the sign also changed with the update rate. A pre-specified second test on 4,951 real FMA tracks (EXP-004) reversed the sign (+0.1652 rad, CI [0.1560, 0.1735]): the result does not replicate. In descriptive secondary outcomes, SIM concentrated exposure more than RAND on both catalogues, as a personalised top-k policy does largely by construction. Within this model, the direction of simulated taste change is not a property of the policy alone; it depends on the update rule, the update rate and the catalogue geometry.

## Keywords

recommender systems; feedback loops; preference drift; simulation; pre-registration; sensitivity analysis; music recommendation

## 1. Introduction

A recommender that learns from consumption can also change what is consumed. If listeners' tastes adapt to what they hear, a policy could shape taste rather than simply reflect it. Simulation studies have described homogenisation and preference amplification under such feedback loops [chaney2018, mansoury2020, kalimeris2021, jiang2019], and recent work defines a policy-induced preference shift relative to a "natural" reference [carroll2022]. Of the simulation studies read for this work, two hold the users' intrinsic preferences fixed and measure homogenisation or a shift in the system's representation of taste [chaney2018, mansoury2020], and two model one specified form of preference or interest dynamics [kalimeris2021, jiang2019]. In the limited, non-systematic set of sources read, we did not find a pre-registered test of whether a policy comparison survives a change of that mechanism; this is a statement about our reading, not a claim that no such test exists.

**Research question.** Can recommendation policies change exposure and simulated taste rather than simply reflect it? Operationally: in a seeded simulation of listeners with fixed or adaptive preference vectors, does the policy change end-of-session preferences beyond what a non-personalised uniform-random policy induces, and does it change what listeners are exposed to?

**Hypotheses** (frozen, protocol v1.0). Primary estimand: under adaptive preferences, Delta = E_seed[mean_u theta_u(SIM) - mean_u theta_u(RAND)], in radians, where theta_u is the angle between listener u's initial and final preference vectors. H0: Delta = 0; H1: Delta != 0 (non-directional, because the literature motivates both narrowing and amplification).

**Contributions** (what was actually done):

1. A small, fully reproducible, seed-paired comparison of five simple policy families against uniform-random exposure, with fixed and adaptive preferences modelled separately (EXP-002, 100 runs).
2. A pre-registered retain-or-withdraw sensitivity test of the primary contrast across three update rules, three update rates and two recommender profiles (EXP-003, 360 runs). It withdrew the primary interpretation.
3. A pre-specified second test of the primary contrast on a real music catalogue (FMA test split, real genres, audio features and play counts, simulated listeners; EXP-004, 100 runs). It did not replicate the primary direction.
4. An open evidence trail: frozen protocols with hashes, per-run manifests, byte-reproducible analysis outputs and a claims register.

No novelty claim is made beyond this specific combination; the literature search was targeted, not systematic (section 2).

## 2. Related work

The sources below were opened and read in full (seven on 2026-11-25, at M6; the FMA licence statement comes from the repository README); the section or page that supports each statement is given in `research/publication/claims_audit.md` (M6 reference table). The search was targeted and non-systematic (`research/literature_review.md`); citation chaining from kalimeris2021 and carroll2022 was not completed.

- **Feedback loops and homogenisation.** Chaney, Stewart and Engelhardt [chaney2018] report a simulation in which algorithmic confounding in recommendation feedback loops homogenises user behaviour without raising utility; their users' preferences are fixed (their assumption 3). Mansoury et al. [mansoury2020] simulate popularity-bias amplification with reduced aggregate diversity and a shift in the representation of user taste; they state that this shift is in the system's representation of preferences, not in intrinsic preferences (their section 4.3.2). ECHO reuses the idea of a homogenisation outcome and includes a popularity arm (POP) and an exposure-concentration metric.
- **Preference dynamics.** Jiang et al. [jiang2019] study degenerate feedback loops in user-interest dynamics and distinguish echo chambers from filter bubbles. Kalimeris et al. [kalimeris2021] model preference amplification in a matrix-factorisation recommender, with users drifting toward recommended content. ECHO's consumed-item update rule is a simple member of this family. ECHO does not replicate either model; it uses a simpler angular-drift model.
- **Reference for induced shift.** Carroll et al. [carroll2022] evaluate induced preference shifts against "safe" shifts and operationalise "natural preference shifts" as the preferences a user would have when interacting with a random recommender, an approximation of having no recommender at all (their section 5). ECHO's uniform-random comparator (RAND) follows this operationalisation. As in their setting, RAND itself moves preferences under adaptive preferences (section 5.1), so the contrast measures shift beyond the random reference, not shift relative to no change.
- **Simulation platforms.** RecSim [ie2019] is a configurable simulation platform whose user latent state and its dynamics are configurable. It served as a design reference only and is not a dependency.
- **Metrics.** Vargas and Castells [vargas2011] (full text read on 2026-11-25) unify novelty and diversity metrics. Their equation 5 defines item novelty as self-information, -log2 p(i | seen), and their mean self-information and average intra-list distance (equation 16, without rank discount and relevance weighting) match ECHO's novelty (base-popularity share as p) and intra-list diversity (distance 1 - cos).
- **Data.** FMA [defferrard2017] (paper and repository README read) provides the metadata, genres, audio features and play counts used for calibration and for EXP-004.

**Positioning.** Relative to these works, ECHO is an extension in method, not in mechanism: it adds a frozen protocol, a negative control, a pre-registered withdrawal rule and a real-catalogue second test to a deliberately simple model. Its main finding is negative for the generality of the primary contrast.

## 3. Background and formal model

The full specification is `research/protocol.md` sections 3, 4 and 10; implementation choices frozen with the code are in DEC-006.

- **Catalogue.** N = 1000 tracks with unit-norm embeddings x_i in R^d, d = 16. In the synthetic catalogue (EXP-002, EXP-003), embeddings are drawn around K = 16 Gaussian cluster centres with cluster weights fitted on the FMA training split, then L2-normalised; base popularity follows a Zipf law with exponent s = 1.3065, fitted on the same split (journal J-0003). In EXP-004, each seed samples 1000 of 4,951 eligible FMA test-split tracks; embeddings are the first 16 principal components of standardised librosa statistics (training-split basis), L2-normalised; clusters are the 16 FMA top-level genres; popularity is listens + 1.
- **Listeners.** U = 200 per seed. The initial preference p_u,0 is a unit vector near a uniformly chosen cluster centre.
- **Session.** T = 100 steps. Each step, the policy shows a slate of k = 10 tracks from the candidates the listener has not consumed (candidate exclusion). The listener picks one track or skips, by a softmax over cos(p_u,t, x_i)/tau with tau = 0.1 and a skip option of utility 0.
- **Preference models.** Fixed: p_u,t+1 = p_u,t. Adaptive, consumed-item rule (primary): p_u,t+1 = normalise((1 - eta) p_u,t + eta x_chosen), eta = 0.05, no update on skip. EXP-003 adds an exposure rule (move toward the slate mean) and a bounded-confidence rule (update only if cos(p_u,t, x_chosen) > 0.5).
- **Policies.** RAND: uniform-random slate (baseline). POP: top-k by global consumption count plus base popularity. SIM: top-k by cos(p_hat, x_i), where p_hat is the normalised mean of consumed embeddings after a 5-step random warm-up (the recommender never sees p_u,t, except in the oracle ablation of EXP-003). MMR: maximal marginal relevance re-ranking of SIM, lambda = 0.5. EXPLORE: epsilon-greedy SIM, epsilon = 0.2.
- **Primary metric.** theta_u = arccos(clip(<p_u,0, p_u,T>, -1, 1)), computed stably as 2 arcsin(||p_u,0 - p_u,T|| / 2), averaged over listeners. Its range is [0, pi]; two unrelated directions in R^16 lie close to pi/2 apart, so drift near pi/2 means the final taste is nearly unrelated to the initial one.
- **Secondary metrics.** Homogenisation (change in mean pairwise cosine of preferences), discovery (share of clusters consumed), novelty (mean self-information of consumed tracks, bits), intra-list diversity (mean pairwise 1 - cos within slates), relevance to initial and current taste, exposure Gini over slate impressions, skip rate, and drift per accepted item.
- **Cost.** One run scores U x T x N = 2 x 10^7 cosines; runs take seconds on a laptop CPU.

## 4. Methods

- **Design.** EXP-001 (exploratory): simulator verification and smoke matrix (checks V1 to V6: determinism, zero drift under fixed preferences, candidate exclusion, unit norms, metric bounds, schema). EXP-002 (confirmatory, primary): 5 policies x {fixed, adaptive eta 0.05} x 10 seeds = 100 runs. EXP-003 (confirmatory sensitivity): RAND and SIM x 3 update rules x eta in {0.01, 0.05, 0.2} x {estimated, oracle} profile x 10 seeds = 360 runs. EXP-004 (confirmatory secondary, second test): the EXP-002 matrix on the FMA catalogue, 100 runs.
- **Unit and pairing.** The seed (one catalogue and one listener population) is the independent unit; listeners within a seed share the catalogue and POP counts, so they are aggregated to a seed mean. Common random numbers: every policy within a seed sees the same catalogue, listeners and choice uniforms. Confirmatory seeds 20261124 to 20261133 were fixed in advance and disjoint from exploratory seeds.
- **Sample size.** Precision-based. An exploratory pilot (draft parameters, seeds 900002 to 900011) gave a paired-difference SD of 0.01587 rad and a projected 95 % half-width of 0.0114 rad at 10 seeds, below SESOI/2 = 0.025 rad, so 10 seeds were kept.
- **Analysis.** 95 % percentile bootstrap over seeds (10,000 resamples, bootstrap seed 7) of the paired mean difference, the paired t interval, and d_z. SESOI 0.05 rad. Decision rule: "reject H0" if the CI excludes 0; "statistically detectable, practically negligible" if it excludes 0 and lies inside [-0.05, 0.05]; "practically equivalent" if it includes 0 and lies inside the band; otherwise "inconclusive". Secondary drift contrasts (POP, MMR, EXPLORE and SIM versus RAND) get Holm-adjusted intervals; other metrics are descriptive. The Holm construction and the two readings of "practically equivalent" (band and label) were fixed before any confirmatory output (DEC-012) and ratified by the owner (DEC-014); the two readings agreed in every verdict.
- **Pre-registered rules for EXP-003 and EXP-004.** EXP-003: the EXP-002 interpretation is retained if every cell with eta >= 0.05 has the EXP-002 sign with a CI excluding 0; withdrawn as assumption-dependent if any cell at eta = 0.05 has the opposite sign with a CI excluding 0 or is practically equivalent to 0; partially robust otherwise. A second check compares oracle and estimated profiles. EXP-004: replicates if Delta_FMA has the EXP-002 sign with a CI excluding 0; does not replicate if its CI excludes 0 with the opposite sign or it is practically equivalent to 0; otherwise inconclusive.
- **Exclusions and stopping.** No listener or seed is excluded; runs that fail are reported; more than 10 % failures in an arm stops the experiment. Fixed matrices, no optional stopping.
- **Registration and freeze.** The owner froze protocol v1.0 on 2026-11-24 (DEC-010; `research/freeze.json`, revision 17ac055; SHA-256 of `research/protocol.md` a81ed32c...f8c5dc). The run guard refuses any confirmatory config whose hash differs from the freeze record. SIM minus RAND values seen before the freeze (exploratory seeds, draft parameters) are disclosed: pilot mean -0.15881 rad (protocol 10.2 item 6). No simulation on the real catalogue was run before the freeze.
- **Execution.** All 560 confirmatory runs were made at code revision afc0850 with a clean tree, on 2026-11-24 23:39 to 23:52 UTC, on an Apple M1 Pro shared with other sessions (runtimes are upper bounds). 560 of 560 runs completed; none failed, was retried or was excluded.
- **Exploratory work, labelled.** EXP-001 and its FMA-path smoke; and an M4 confounder inspection (journal J-0008, `results/exploratory/M4-confounders/`) that reads committed results and regenerates only the input catalogues and initial tastes. It runs no simulation and changes no verdict.
- **Resources.** Zero cost; local CPU; wall-clock 4 min 51 s (EXP-002), 12 min 45 s (EXP-003), 4 min 18 s (EXP-004).

## 5. Results

Every number in this section is generated from `results/EXP-00N/analysis/analysis.json` (confirmatory) or `results/exploratory/M4-confounders/confounders.json` (exploratory, labelled). The mapping is in `research/publication/artifact_manifest.json`.

### 5.1 EXP-002: the primary contrast on the calibrated synthetic catalogue

**Negative control.** With fixed preferences, drift was exactly 0 for every listener in all 50 fixed runs (claim C-003). This checks the implementation, not the model.

**Primary.** Delta (SIM minus RAND) = -0.0355 rad, SD of paired differences 0.0286, 95 % bootstrap CI [-0.0535, -0.0200], paired t CI [-0.0560, -0.0151], d_z -1.24, n = 10 seeds. Frozen decision: **reject H0**. All 10 seeds had a negative difference (exploratory sign count, J-0008). The point estimate is inside the SESOI, but the CI extends past -0.05 rad, so the effect could be smaller or larger than the smallest effect of interest: its practical size is unresolved.

**Table 1.** Drift contrasts versus RAND, adaptive, seed-paired (rad, n = 10 seeds). Source: `results/EXP-002/analysis/contrasts.csv`; figure `results/EXP-002/analysis/fig-contrasts.svg`.

| Contrast | Mean diff | 95 % bootstrap CI | Holm CI | d_z | Decision |
|---|---|---|---|---|---|
| SIM-RAND (primary) | -0.0355 | [-0.0535, -0.0200] | [-0.0535, -0.0200] | -1.24 | reject H0 |
| POP-RAND | 0.1630 | [0.1443, 0.1810] | [0.1418, 0.1834] | 5.22 | reject H0 |
| MMR-RAND | -0.1162 | [-0.1339, -0.1009] | [-0.1377, -0.0983] | -4.18 | reject H0 |
| EXPLORE-RAND | -0.0381 | [-0.0570, -0.0219] | [-0.0625, -0.0186] | -1.27 | reject H0 |

**Table 2.** Per-policy seed-level means, adaptive preferences (drift with 95 % bootstrap CI). Source: `results/EXP-002/analysis/arms.csv`; figure `results/EXP-002/analysis/fig-arms-drift.svg`.

| Policy | Drift (rad) [95 % CI] | Homogenisation | Discovery | Skip rate | Exposure Gini |
|---|---|---|---|---|---|
| RAND | 1.1119 [1.0805, 1.1404] | 0.358 | 0.376 | 0.006 | 0.040 |
| POP | 1.2749 [1.2513, 1.2966] | 0.901 | 0.664 | 0.052 | 0.950 |
| SIM | 1.0763 [1.0467, 1.1035] | 0.244 | 0.185 | 0.001 | 0.552 |
| MMR | 0.9956 [0.9710, 1.0181] | 0.219 | 0.290 | 0.002 | 0.378 |
| EXPLORE | 1.0738 [1.0446, 1.1005] | 0.243 | 0.190 | 0.001 | 0.440 |

**Exposure (descriptive secondaries, seed-paired SIM minus RAND, adaptive).** Exposure Gini +0.5118 [0.4883, 0.5336]; discovery -0.1909 [-0.2119, -0.1698]; intra-list diversity -0.6727 [-0.6948, -0.6512]; homogenisation -0.1145 [-0.1572, -0.0754]. These are descriptive, not confirmatory.

**Uniform-random exposure is not neutral.** Under the adaptive model, RAND itself moved preferences by 1.1119 rad on average, closer to the angle between unrelated directions than to 0. The question the primary contrast answers is therefore "which policy moves taste more", not "which policy moves taste at all".

### 5.2 EXP-003: sensitivity to the update rule, rate and profile

All 18 cells are in Table S2 (supplementary) and `results/EXP-003/analysis/fig-contrasts.svg`. The cell consumed / 0.05 / estimated has the EXP-002 configuration and reproduces its primary contrast exactly (-0.0355 rad, CI [-0.0535, -0.0200]).

**Table 3.** SIM minus RAND drift by update rule and rate, estimated profile (rad, 95 % bootstrap CI, n = 10 seeds). Source: `results/EXP-003/analysis/contrasts.csv`.

| Rule | eta 0.01 | eta 0.05 | eta 0.2 |
|---|---|---|---|
| consumed | 0.1364 [0.1234, 0.1484] | -0.0355 [-0.0535, -0.0200] | -0.0978 [-0.1186, -0.0770] |
| exposure | 0.1710 [0.1421, 0.1983] | -0.1510 [-0.1838, -0.1257] | -0.2688 [-0.3046, -0.2354] |
| bounded | 0.0363 [0.0275, 0.0466] | 0.0069 [-0.0130, 0.0303] | -0.1012 [-0.1318, -0.0617] |

**Verdict under the frozen rule: withdrawn as assumption-dependent** (both equivalence readings agree; claim C-004). Two cells at eta 0.05 trigger withdrawal: bounded / estimated is practically equivalent to 0 (+0.0069 rad, CI [-0.0130, 0.0303]; the paired t interval [-0.0194, 0.0331] also lies inside the band), and bounded / oracle has the opposite sign (+0.1883 rad, CI [0.1598, 0.2196]; Holm CI [0.1478, 0.2362]). Beyond the trigger, the sign changes with eta under the consumed and exposure rules: positive at 0.01, negative at 0.05 and 0.2, with all 10 seeds sharing the sign in each of these cells (J-0008).

**Oracle versus estimated profile** (protocol section 7, second check; C-005). The point signs differ, with both CIs excluding 0, in one rule-rate pair: bounded, eta 0.2 (estimated -0.1012 rad, oracle +0.1564 rad). There, the effect comes from the profile estimator rather than the policy family. In the other eight pairs the point signs agree.

### 5.3 EXP-004: second test on the real FMA catalogue

**Negative control.** Drift was exactly 0 in all 50 fixed runs (C-003).

**Primary.** Delta_FMA = +0.1652 rad, SD 0.0148, 95 % CI [0.1560, 0.1735], paired t CI [0.1546, 0.1758], d_z 11.15, n = 10 seeds (all 10 positive). Frozen decision: reject H0, with the opposite sign to EXP-002. **Frozen reading: does not replicate** (both readings agree; C-006).

**Table 4.** Drift contrasts versus RAND on the FMA catalogue (rad, n = 10 seeds). Source: `results/EXP-004/analysis/contrasts.csv`; figure `results/EXP-004/analysis/fig-contrasts.svg`.

| Contrast | Mean diff | 95 % bootstrap CI | Holm CI | d_z | Decision |
|---|---|---|---|---|---|
| SIM-RAND (primary) | 0.1652 | [0.1560, 0.1735] | [0.1547, 0.1749] | 11.15 | reject H0 |
| POP-RAND | -0.0357 | [-0.0723, 0.0005] | [-0.0723, 0.0005] | -0.58 | inconclusive |
| MMR-RAND | 0.0570 | [0.0502, 0.0643] | [0.0490, 0.0660] | 4.76 | reject H0 |
| EXPLORE-RAND | 0.1631 | [0.1539, 0.1720] | [0.1516, 0.1744] | 10.66 | reject H0 |

**Table 5.** Per-policy seed-level means on FMA, adaptive. Source: `results/EXP-004/analysis/arms.csv`; figure `results/EXP-004/analysis/fig-arms-drift.svg`.

| Policy | Drift (rad) [95 % CI] | Homogenisation | Discovery | Skip rate | Exposure Gini |
|---|---|---|---|---|---|
| RAND | 0.6933 [0.6794, 0.7070] | 0.159 | 0.713 | 0.011 | 0.047 |
| POP | 0.6576 [0.6205, 0.6893] | 0.503 | 0.694 | 0.325 | 0.961 |
| SIM | 0.8585 [0.8427, 0.8739] | 0.187 | 0.660 | 0.001 | 0.726 |
| MMR | 0.7503 [0.7409, 0.7606] | 0.146 | 0.656 | 0.001 | 0.477 |
| EXPLORE | 0.8564 [0.8395, 0.8730] | 0.180 | 0.658 | 0.001 | 0.579 |

**Exposure (descriptive, SIM minus RAND, adaptive).** Exposure Gini +0.6796 [0.6652, 0.6925]; discovery -0.0539 [-0.0657, -0.0422]; intra-list diversity -0.5309 [-0.5429, -0.5198]; homogenisation +0.0275 [0.0118, 0.0455], the opposite sign to EXP-002.

**POP.** Its drift contrast is inconclusive, but POP's skip rate is 0.325 against 0.011 for RAND. Per accepted item, POP drifts more than RAND (+0.002818 rad per track, CI [0.002458, 0.003111]; exploratory side-by-side, J-0008): the sign of the POP contrast depends on whether skips are counted, so the skip-rate confounder dominates it.

### 5.4 Robustness and confounder inspection (exploratory, J-0008)

- **Skip rate.** For SIM, MMR and EXPLORE, drift and drift per accepted item have the same sign in both catalogues, and skip-rate differences are at most about 0.01. Skips do not explain the SIM contrasts. They do explain the POP contrast on FMA (section 5.3).
- **Seed consistency.** In EXP-002 and EXP-004 all 10 seeds share the sign of the SIM, MMR and EXPLORE contrasts. The withdrawal-triggering cell bounded / 0.05 / estimated is split (6 negative, 4 positive), as expected for a near-zero effect.
- **Ceiling.** Listener-level drift is not capped at pi/2: in EXP-002 the median under RAND is 1.2292 rad and 4.2 % of listener values exceed pi/2 (maximum 1.8046 rad). The concern that contrasts are compressed by a ceiling (EXP-002 protocol item 16) is weaker than the M3 report implied; the M3 phrase "pi/2 ceiling" was imprecise and is corrected here.
- **Catalogue geometry (inputs only).** The two catalogues differ sharply. In the synthetic catalogue, tracks sit tightly around their cluster centres (mean cosine to own centre 0.9313) and the catalogue has a strong common direction (resultant length of the mean embedding 0.4138), because the fitted cluster weights put about 28 % of tracks in one cluster. On FMA, tracks are far from their genre centres (0.3327) and spread almost isotropically (resultant length 0.0777), while genre centres are closer to one another (mean pairwise cosine 0.1692 against 0.0082). This is consistent with, but does not establish, the reading that RAND drift on the synthetic catalogue is driven by the catalogue's common direction, and that SIM on FMA follows local neighbourhoods that lead away from the genre-centre start points. The design cannot separate embedding, genre balance and popularity tail (EXP-004 protocol item 3).

### 5.5 Expected versus observed

**Table 6.** Predictions, observations and verdicts under the frozen rules.

| Experiment | Prediction or rule (frozen) | Observation | Verdict |
|---|---|---|---|
| EXP-001 | V1 to V6 pass; pilot half-width below 0.025 rad | All checks pass in two runs, byte-identical across revisions; half-width 0.0114 rad | Pass (exploratory; no claim) |
| EXP-002 negative control | Drift exactly 0 under fixed preferences | 0 in all 50 fixed runs | Pass |
| EXP-002 primary | H1: Delta != 0 (no sign predicted); disconfirmed if CI inside +/-0.05 | -0.0355 rad [-0.0535, -0.0200] | Reject H0; practical size unresolved |
| EXP-002 secondaries | Holm family of four drift contrasts | POP +, MMR -, EXPLORE - vs RAND, all Holm CIs exclude 0 | All rejected after Holm |
| EXP-003 | Retain if every cell with eta >= 0.05 keeps the sign with CI excluding 0 | Bounded / 0.05: equivalent (estimated) and reversed (oracle); signs change with eta | Withdrawn as assumption-dependent |
| EXP-003 second check | Oracle and estimated signs agree | Differ, both CIs excluding 0, at bounded / 0.2 | Profile-dependent in one pair |
| EXP-004 primary | Replicates if same sign with CI excluding 0 | +0.1652 rad [0.1560, 0.1735] | Does not replicate |
| EXP-004 secondaries | Holm family of four | MMR +, EXPLORE + rejected; POP inconclusive | Signs reversed relative to EXP-002 for MMR and EXPLORE |

The pre-freeze pilot (draft parameters) had shown SIM below RAND by -0.15881 rad. The calibrated confirmatory estimate kept the sign but was much smaller, and its paired SD (0.0286 rad) was larger than the pilot's (0.01587 rad). The 10-seed design was sized on the pilot SD; the achieved CI half-width was about 0.017 rad, still within the SESOI/2 target.

## 6. Discussion

**What the evidence supports.** Within this simulation, two statements survive every test the protocol set. First, recommendation policies change exposure: SIM concentrates impressions (exposure Gini) and lowers within-slate diversity relative to RAND on both catalogues, with consistent signs. This is largely by construction for a personalised top-k policy, and these contrasts were descriptive secondaries, so it is a bounded, unsurprising result. Second, when preferences adapt to consumption, any exposure, including uniform-random exposure, changes simulated taste, and the policy changes how much.

**What the evidence does not support.** It does not support a policy-level statement about the direction of the taste effect. The primary contrast was negative on the calibrated synthetic catalogue, reversed on the real catalogue, reversed at a lower update rate, and vanished or reversed under bounded-confidence updating. The pre-registered rules turned these into a withdrawal (EXP-003) and a non-replication (EXP-004). The direction is a joint property of the policy, the update rule, the update rate and the catalogue geometry.

**Competing explanations, and which the results address.**

| Conclusion | Competing explanation (protocol) | Addressed by | Status |
|---|---|---|---|
| EXP-002 primary | Skip rate (relevance) rather than steering | Skip rates 0.001 and 0.006; per-accept contrast same sign | Addressed: not the explanation for SIM |
| EXP-002 primary | Profile estimator rather than policy family | EXP-003 oracle cells: same sign as estimated at consumed / 0.05 (-0.0607 rad) | Addressed for the primary cell; not for bounded / 0.2 |
| EXP-002 primary | Update rule and rate | EXP-003 | Confirmed as an explanation: interpretation withdrawn |
| EXP-002 primary | Compression near pi/2 | Listener-level distribution (J-0008) | Partly addressed: no hard ceiling observed |
| EXP-002 vs EXP-004 | Embedding, genre balance, popularity tail | Not separable in this design; geometry inspection only | Open |
| EXP-004 POP | Skip rate | Per-accept contrast reverses sign | Confirmed as an explanation for POP |

**Relation to prior work.** Homogenisation under feedback loops [chaney2018] and popularity amplification [mansoury2020] are reported in prior simulations. In ECHO, POP produced the largest homogenisation on both catalogues (POP minus RAND +0.5433 on synthetic, +0.3439 on FMA, descriptive), which is in line with those reports, while SIM's homogenisation effect changed sign between catalogues. Their models differ from ECHO's (fixed intrinsic preferences, rating-based simulation), so no finer comparison is made. The result that the sign of the drift contrast depends on the assumed update rule is consistent with the motivation in carroll2022 for measuring induced shift against a reference, and it argues for reporting assumption sensitivity alongside any single-mechanism simulation.

**An alternative reading of the drift metric (second review pass).** Under the consumed-item rule each accepted track multiplies the weight of the previous preference by about (1 - eta) before normalisation. With eta = 0.05 and about 100 accepted tracks per session, the weight left on the initial taste is of the order of 0.95^100, about 0.006. End-of-session "taste" is then close to a recency-weighted average of the last few dozen consumed tracks, so the drift outcome largely re-measures exposure through consumption rather than an independent property of the listener. At eta = 0.01 the corresponding weight is about 0.37, so the initial taste still dominates, which is one candidate explanation for the sign change with the rate in EXP-003. This reading is analytical and was not tested; it means that, in this model, "exposure" and "taste" outcomes are less separable than the research question suggests.

**Practical significance.** The drift unit is an angle in a 16-dimensional synthetic taste space; 0.05 rad (about 2.9 degrees) was a judgement-based SESOI. No mapping from these angles to human listening outcomes exists in this study.

## 7. Limitations and threats to validity

- **Simulation only.** Listeners are synthetic agents with assumed update rules. Nothing here is evidence about human persuasion, real listeners or any commercial or proprietary recommender.
- **Assumed mechanisms.** Three update rules and three rates are a small slice of plausible mechanisms. The withdrawal shows that this slice already matters.
- **Catalogue.** The synthetic catalogue is stylised (Gaussian clusters with FMA-fitted weights and popularity). The real catalogue is one embedding (PCA-16 of librosa statistics) of freely licensed music; audio-feature similarity is not perceived similarity. The 10 FMA samples of 1000 tracks overlap within 4,951 tracks.
- **Statistics.** 10 seeds per arm; the percentile bootstrap with n = 10 can under-cover (the paired t intervals agree in sign). EXP-003's withdrawal rule has no multiplicity correction by design; the triggering oracle cell also excludes 0 after Holm. Several bootstrap p-values are exactly 0, and Holm ties are ranked by name, which changes interval levels only. Large d_z values (11.15 on FMA) reflect small between-seed SDs, not large practical effects. On FMA the ten 1000-track samples are drawn from the same 4,951 tracks, so seeds are not fully independent and the EXP-004 intervals may be too narrow; the sign of the EXP-004 contrast, shared by all 10 seeds, is less exposed to this than its width.
- **Construct.** Angular drift measures how far taste moved, not toward what. The SESOI of 0.05 rad was proposed by the AI and kept by the owner; it is not empirically anchored.
- **Model choices.** `skip_utility = 0` makes skips rare except under POP. The implementation choices of DEC-006 (spreads 0.1, warm-up for the oracle profile, synchronous POP counts) may shape results.
- **Pre-freeze exposure.** The pilot SIM minus RAND value at draft parameters was seen before the freeze and disclosed; the calibrated parameters were fitted on FMA metadata without any simulation. The statement that the SIM minus RAND values of the exploratory FMA-path smoke were not inspected before the confirmatory runs rests on the session record and cannot be verified independently; the smoke used smoke-size parameters and exploratory seeds.
- **Construct overlap.** With eta 0.05 the initial taste is almost forgotten after 100 updates, so drift largely reflects recent consumption (section 6).
- **Runtime figures** come from a shared, loaded machine and are upper bounds.
- **Literature.** Eight sources, all read in full; non-systematic search; citation chaining from kalimeris2021 and carroll2022 was not done, so closely related models may have been missed.

The full list is `research/limitations.md`.

## 8. Ethics and responsible research

The study uses public FMA metadata under CC BY 4.0, with attribution; no audio is downloaded, no artist or title fields are processed, and no personal or listener data exists. No human participants were involved and no ethics approval was sought or claimed; a study of human listeners would need an owner-approved protocol with appropriate review. The study evaluates exposure concentration and taste change as outcomes to be understood, not targets to optimise; it should not be read as a recipe for steering preferences. No Spotify or other service was scraped, and no claim is made about any proprietary system.

## 9. Conclusion and future work

Within a pre-registered simulation, a similarity recommender changed exposure relative to uniform-random recommendation on both a calibrated synthetic and a real music catalogue (descriptive outcomes, largely expected by construction). Its effect on the amount of simulated taste change was statistically detectable in the primary experiment, of unresolved practical size, and its direction was not robust: the frozen sensitivity rule withdrew it, and the real-catalogue second test reversed it. The bounded answer to the title question is that, in this model, whether a recommender "shapes" taste more or less than random exposure depends on how simulated listeners update and on the catalogue, not on the policy alone.

Future work, each as a new registered experiment: locate the update-rate threshold at which the SIM minus RAND sign changes for each rule; separate embedding, genre balance and popularity tail on the real catalogue (for example by re-embedding FMA tracks or reweighting genres); add a directional outcome (movement toward or away from the home cluster); complete citation chaining and full-text reading of the closest prior models.

## 10. Data, code and artifact availability

- Repository: https://github.com/mohamedbechirkefi/echo-recommender-feedback.
- Interactive page: https://echo-recommender-feedback.kefimohamedbechir.workers.dev.
- Protocols and freeze record: `research/protocol.md`, `research/experiments/EXP-00N/protocol.md`, `research/freeze.json`.
- Experiment reports: `research/experiments/EXP-00N/report.md`.
- Raw results: `results/EXP-00N/runs/` (schema `echo.result.v1`), manifests, `provenance.csv`, `SHA256SUMS`.
- Analysis: `PYTHONPATH=src .venv/bin/python -m echo.analysis results/EXP-00N --planned N --kind {policy|sensitivity|replication}`; re-running it on the committed runs reproduced every analysis file byte for byte on 2026-11-25 (evidence audit). After the owner-approved formatting fix of DEC-016, the regenerated tables hold the same values.
- Exploratory confounder inspection: `PYTHONPATH=src .venv/bin/python scripts/m4_exploratory_confounders.py`.
- Data: `scripts/download_fma_metadata.py` and `scripts/build_fma_catalogue.py` rebuild the git-ignored FMA files; the processed catalogue's SHA-256 is checked at run time. Only aggregate calibration values are committed.
- Evidence trail: `research/claims_register.csv`, `research/publication/artifact_manifest.json`, `research/publication/claims_audit.md`.

## 11. Funding, competing interests and AI assistance

- **Funding:** No funding was received. The only expense was the owner's existing AI coding subscription.
- **Competing interests:** The author declares no competing interests.
- **AI assistance:** an AI system (Claude, Anthropic) wrote the simulation and analysis code, ran the experiments under the owner-frozen protocol and drafted the reports and this manuscript. The owner set the question, approved the protocol freeze, the real-data use and every post-freeze decision (DEC-010, DEC-014), and retains authority over claims and publication. AI review of the manuscript (`research/publication/review_pass_2.md`) is internal quality control, not peer review. Every number was checked mechanically against committed result files (section 10).

## References

Abstract pages were first opened on 2026-11-24. The full texts of all eight sources were read: vargas2011 on 2026-11-25 (M4), the other seven on 2026-11-25 (M6), from the free arXiv PDFs or, for kalimeris2021, the PDF linked from the Meta Research publication page.

- [carroll2022] M. Carroll, A. Dragan, S. Russell, D. Hadfield-Menell. Estimating and Penalizing Induced Preference Shifts in Recommender Systems. ICML 2022, PMLR 162:2686-2708. arXiv:2204.11966. https://arxiv.org/abs/2204.11966 (full text with appendices).
- [chaney2018] A. J. B. Chaney, B. M. Stewart, B. E. Engelhardt. How Algorithmic Confounding in Recommendation Systems Increases Homogeneity and Decreases Utility. arXiv:1710.11214, 2018. https://arxiv.org/abs/1710.11214 (full text, 9 pages; the RecSys 2018 DOI listed on arXiv was not opened).
- [defferrard2017] M. Defferrard, K. Benzi, P. Vandergheynst, X. Bresson. FMA: A Dataset For Music Analysis. ISMIR 2017; arXiv:1612.01840. https://arxiv.org/abs/1612.01840 and https://github.com/mdeff/fma (full text, 8 pages, and repository README).
- [ie2019] E. Ie, C. Hsu, M. Mladenov, V. Jain, S. Narvekar, J. Wang, R. Wu, C. Boutilier. RecSim: A Configurable Simulation Platform for Recommender Systems. arXiv:1909.04847, 2019. https://arxiv.org/abs/1909.04847 (full text).
- [jiang2019] R. Jiang, S. Chiappa, T. Lattimore, A. György, P. Kohli. Degenerate Feedback Loops in Recommender Systems. AIES 2019. DOI 10.1145/3306618.3314288. https://arxiv.org/abs/1902.10730 (full text, 10 pages).
- [kalimeris2021] D. Kalimeris, S. Bhagat, S. Kalyanaraman, U. Weinsberg. Preference Amplification in Recommender Systems. KDD 2021. https://research.facebook.com/publications/preference-amplification-in-recommender-systems/ (full text, 11 pages; DOI 10.1145/3447548.3467298 as printed in the paper, not opened).
- [mansoury2020] M. Mansoury, H. Abdollahpouri, M. Pechenizkiy, B. Mobasher, R. Burke. Feedback Loop and Bias Amplification in Recommender Systems. arXiv:2007.13019, 2020. https://arxiv.org/abs/2007.13019 (full text, 5 pages).
- [vargas2011] S. Vargas, P. Castells. Rank and Relevance in Novelty and Diversity Metrics for Recommender Systems. RecSys 2011, Chicago. https://castells.github.io/papers/recsys2011.pdf (full text, 8 pages, read 2026-11-25; DOI 10.1145/2043932.2043955 taken from a search result, not opened).

## Supplementary appendix

See `research/paper/supplementary.md`: the complete experimental matrix, Table S2 (all 18 EXP-003 cells), the oracle versus estimated table, the exploratory confounder tables, configurations and hashes, report links, and every deviation and owner decision.
