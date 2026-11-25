<!-- SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0 -->
# ECHO research report (summary of the manuscript)

**Status: independent research report, not peer-reviewed. Simulation results only.** M4 draft, 2026-11-25. The canonical, complete text is `research/paper/manuscript.md`; this report is the short form required by master prompt section 8. Every number here also appears in the manuscript and is mapped in `research/publication/artifact_manifest.json`.

## Abstract

ECHO asks whether recommendation policies can change exposure and simulated taste rather than simply reflect it. In a seeded simulation with an owner-frozen protocol, a similarity policy (SIM) produced less preference drift than uniform-random exposure (RAND) on a synthetic catalogue calibrated on FMA metadata (EXP-002: Delta = -0.0355 rad, 95 % CI [-0.0535, -0.0200]; reject H0, practical size unresolved). The pre-registered sensitivity test withdrew this interpretation as assumption-dependent (EXP-003), and the pre-specified real-catalogue second test reversed its sign (EXP-004: +0.1652 rad, CI [0.1560, 0.1735]; does not replicate). In descriptive secondary outcomes SIM concentrated exposure more than RAND on both catalogues, largely by construction. The direction of simulated taste change depends on the update rule, the update rate and the catalogue, not on the policy alone.

## Related work

Prior simulations report homogenisation and popularity amplification under feedback loops (chaney2018, mansoury2020) and model preference amplification and degenerate loops (kalimeris2021, jiang2019); carroll2022 evaluates induced shift against a natural-shift reference operationalised as a random recommender, which ECHO's RAND follows. All eight cited sources were read in full (seven at M6, 2026-11-25). The novelty and diversity metrics follow Vargas and Castells (vargas2011). See manuscript section 2 and `research/literature_review.md`.

## Method

Five policies (RAND, POP, SIM, MMR, EXPLORE), fixed and adaptive preferences, 200 simulated listeners, 100 steps, 10 confirmatory seeds with common random numbers. Primary metric: mean angular drift between initial and final preference (rad). Seed-paired 95 % percentile bootstrap, SESOI 0.05 rad, Holm-adjusted intervals for the four drift contrasts. EXP-003 varies the update rule, rate and profile (360 runs); EXP-004 repeats EXP-002 on 4,951 real FMA tracks (100 runs). Protocol v1.0 was frozen by the owner before any confirmatory run (DEC-010).

## Results

- EXP-002: SIM minus RAND -0.0355 rad [-0.0535, -0.0200], d_z -1.24, reject H0. POP +0.1630, MMR -0.1162, EXPLORE -0.0381 rad, all rejected after Holm. Negative control: drift exactly 0 in all 50 fixed runs.
- EXP-003: withdrawn as assumption-dependent. Bounded-confidence rule at eta 0.05: +0.0069 rad [-0.0130, 0.0303] (estimated profile, practically equivalent) and +0.1883 rad [0.1598, 0.2196] (oracle profile, opposite sign). The sign also flips with the update rate.
- EXP-004: +0.1652 rad [0.1560, 0.1735], opposite sign; does not replicate. MMR and EXPLORE also reverse; POP is inconclusive (-0.0357 rad [-0.0723, 0.0005]) and dominated by its skip rate (0.325).
- Exposure (descriptive): SIM minus RAND exposure Gini +0.5118 [0.4883, 0.5336] (synthetic) and +0.6796 [0.6652, 0.6925] (FMA).

## Uncertainty

Intervals are over 10 seeds; listeners within a seed are aggregated. On FMA the seeds share tracks, so those intervals may be too narrow. The percentile bootstrap with n = 10 can under-cover; paired t intervals agree in sign. All 560 confirmatory runs completed.

## Sensitivity

The pre-registered rule withdrew the primary interpretation. An exploratory confounder inspection (J-0008) found that skip rates do not explain the SIM contrasts but do explain the POP contrast on FMA, that every seed shares the sign of the SIM contrast in EXP-002 and EXP-004, that listener-level drift has no hard ceiling at pi/2, and that the two catalogues differ sharply in geometry (resultant length of the mean track 0.4138 synthetic, 0.0777 FMA).

## Threats to validity

Simulated listeners and assumed update rules; at eta 0.05 the drift outcome largely re-measures recent consumption; one real embedding of freely licensed music; 10 seeds; a judgement-based SESOI; implementation choices frozen with the code. No claim about human listeners or any commercial recommender follows. Full list: manuscript section 7 and `research/limitations.md`.

## Conclusion

Policies change exposure in this model. Whether a similarity policy changes simulated taste more or less than random exposure is not a property of the policy alone.

## Future work

Locate the rate threshold of the sign change per rule; separate embedding, genre balance and popularity tail on the real catalogue; add a directional drift outcome; complete citation chaining. Each would be a new registered experiment.
