<!-- SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0 -->
# EXP-002: Policy effect on simulated taste and exposure (primary)

**Status:** frozen by the owner on 2026-11-24 (v1.0), not yet run. Confirmatory.
**Protocol version:** 1.0, 2026-11-24. **Hash:** recorded in `research/freeze.json` and the registry.
**Depends on:** EXP-001 passing all verification checks.

Section numbers follow master prompt 11.2.

1. **Question.** Under adaptive simulated preferences, does a personalised similarity policy change listeners' end-of-session taste differently from uniform-random exposure? How do the five policies differ in exposure, discovery, novelty, diversity and relevance under fixed and adaptive preferences?
2. **Mechanism and rationale.**
   - If preferences move toward consumed items, a policy that controls exposure controls the direction of that movement.
   - kalimeris2021 and jiang2019 model such amplification. chaney2018 and mansoury2020 report homogenisation in simulation. carroll2022 defines induced shift against a natural reference.
   - All of these were verified from their abstracts; see `research/literature_review.md`.
3. **Competing explanations.**
   - A drift difference may come from slate relevance (skip rate), not from steering. Skips do not update preferences, so arms with different skip rates have different numbers of updates. Skip rate is reported, and drift per accepted item is a pre-specified secondary.
   - A drift difference may come from the profile estimator, not from the policy family. This is tested in EXP-003.
4. **Hypotheses.**
   - H0: Delta = 0.
   - H1: Delta != 0.
   - Delta is the seed-level paired mean difference in angular drift, SIM minus RAND, with adaptive preferences.
   - SESOI is 0.05 rad.
   - Decision rule as in `research/protocol.md` section 2.
5. **Estimand.** Delta in radians, the population mean over the seed-generating distribution at the draft parameters.
6. **Experimental unit and scope.** The seed is the unit: one catalogue (N = 1000) and 200 listeners. Listeners are aggregated within a seed. Scope: the synthetic model of `research/protocol.md` section 3 only.
7. **Independent variables.**
   - Policy: RAND, POP, SIM, MMR (lambda = 0.5), EXPLORE (epsilon = 0.2).
   - Preference model: fixed or adaptive (eta = 0.05).
8. **Dependent variables.** Drift (primary), homogenisation, discovery, novelty, diversity, relevance (initial and current), exposure Gini, skip rate, and drift per accepted item.
9. **Treatment, control and baseline.** RAND is the baseline. The fixed preference model is the control for "reflect only". The treatment is the personalised policy under adaptive preferences.
10. **Seeds.** 10 confirmatory seeds, 20261124 to 20261133, with common random numbers across policies. (The pilot rule to raise the count to 30 was checked before the freeze and not triggered: projected half-width 0.0114 rad.)
11. **Sample-size rationale.** Precision-based, as in `research/protocol.md` section 5.
12. **Compute budget.** 100 runs, at most 1 hour of wall-clock, local CPU.
13. **Metric formulas.** `research/protocol.md` section 4.
14. **Uncertainty.**
    - Primary: 95 % percentile bootstrap over seeds (10,000 resamples, bootstrap seed 7) of the paired difference, plus the paired t interval and d_z.
    - Secondary drift contrasts (POP, MMR, EXPLORE vs RAND): Holm-adjusted.
    - Other metrics: descriptive, with seed-level bootstrap CIs.
15. **Exclusion and stopping.** No exclusions. Failed runs are reported. If more than 10 % of runs in an arm fail, the experiment stops. The fixed matrix is run in full with no optional stopping.
16. **Anticipated failure modes.**
    - Drift saturates near pi/2 for large eta, so the contrast is compressed.
    - POP counts couple the listeners within a seed. This is the reason the seed, not the listener, is the unit.
17. **Sensitivity.** EXP-003 (drift rule, eta, profile).
18. **What contradicts H1.** A 95 % CI for Delta inside [-0.05, 0.05] rad.
19. **Reproduction (planned commands).**
    - `PYTHONPATH=src .venv/bin/python -m echo.cli run --config experiments/EXP-002/config.json`
    - `PYTHONPATH=src .venv/bin/python -m echo.cli report results/EXP-002`

## Amendments before freeze (owner-approved 2026-11-24, round 2)

See `research/protocol.md` section 10, which governs. For this experiment:

- K = 16 genre clusters with FMA-fitted cluster weights and Zipf exponent s = 1.3065 replace K = 10 (uniform) and s = 1.0 (fitted on the FMA training split before the freeze, method in protocol 10.1, journal J-0003; values in `experiments/EXP-002/config.json` and `data/fma_calibration_v1.json`).
- RAND is the confirmed baseline; `skip_utility = 0` is kept and disclosed (skips are near zero except under POP).
- 10 confirmatory seeds, 20261124 to 20261133.
- When the 95 % CI excludes 0 and lies inside [-0.05, 0.05] rad, the result reads "statistically detectable, practically negligible".
- SIM minus RAND drift values seen before the freeze (exploratory seeds, draft parameters) are disclosed in protocol 10.2 item 6 and `research/freeze.json`.
- The same matrix is repeated on a real FMA catalogue as the pre-specified second test EXP-004.
