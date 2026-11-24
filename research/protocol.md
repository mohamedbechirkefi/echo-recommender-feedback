<!-- SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0 -->
# ECHO research protocol

**Status: DRAFT v0.1 (2026-11-24). NOT FROZEN.** Freezing is the owner's decision (G-FREEZE). No run made under this draft is confirmatory. Protocol hash: none yet (assigned at freeze).

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

## 10. Amendments

None. Any amendment after freeze is dated, justified and kept separate from the frozen analysis.
