<!-- SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0 -->
# EXP-003: Drift-assumption sensitivity and adaptation ablation

**Status:** frozen by the owner on 2026-11-24 (v1.0), not yet run. Confirmatory.
**Protocol version:** 1.0, 2026-11-24. **Hash:** recorded in `research/freeze.json` and the registry.
**Depends on:** EXP-001. It is analysed alongside EXP-002.

Section numbers follow master prompt 11.2.

1. **Question.** Does the SIM vs RAND drift contrast of EXP-002 survive plausible changes to the assumed drift mechanism, drift rate and recommender profile? Equivalently, could the main interpretation be an artefact of the model assumptions?
2. **Mechanism and rationale.** EXP-002 assumes that listeners move toward the item they consume. Exposure alone (mere exposure to the slate) and bounded-confidence updating (moving only toward items close to current taste) are competing, equally simple assumptions. If the conclusion depends on which one holds, it is a property of the model, not of the policy.
3. **Competing explanations.** Differences between the oracle profile and the estimated profile isolate the profile estimator from the policy rule.
4. **Hypotheses.** This is a robustness test, not a new effect. Delta(cell) is defined as in EXP-002 for each cell.
   - The EXP-002 interpretation is **retained** if the sign of Delta agrees with EXP-002 and the CI excludes 0 in every cell with eta >= 0.05.
   - It is **withdrawn as assumption-dependent** if any update-rule cell at eta = 0.05 has the opposite sign with a CI excluding 0, or is practically equivalent to 0.
   - Otherwise the result is "partially robust". The cells are reported in full.
5. **Estimand.** Delta(rule, eta, profile), in radians.
6. **Unit and scope.** The seed, as in EXP-002.
7. **Independent variables.**
   - Update rule: consumed-item, exposure (move toward the slate mean), or bounded-confidence (update only if cos > 0.5).
   - eta in {0.01, 0.05, 0.2}.
   - Profile: estimated or oracle.
   - Policy: RAND or SIM.
8. **Dependent variables.** Drift (primary), homogenisation and skip rate (secondary).
9. **Baseline.** RAND in each cell.
10. **Seeds.** The same 10 confirmatory seeds as EXP-002, under common random numbers.
11. **Sample size.** 3 x 3 x 2 x 2 x 10 = 360 runs. Precision rationale as in EXP-002.
12. **Compute budget.** At most 1 hour of wall-clock.
13. **Metrics.** `research/protocol.md` section 4.
14. **Uncertainty.** 95 % paired bootstrap per cell. No multiplicity correction for the decision rule above, which is deliberately strict (any adverse cell withdraws the interpretation). Holm-adjusted intervals are also reported.
15. **Exclusion and stopping.** As in EXP-002.
16. **Anticipated failure modes.** Under the exposure rule, RAND moves listeners toward the catalogue centroid, so drift may be large for every policy.
17. **Ablation of adaptation.** The fixed vs adaptive ablation is in EXP-002. The oracle vs estimated profile ablation is here.
18. **What contradicts robustness.** Defined in item 4.
19. **Reproduction.** `PYTHONPATH=src .venv/bin/python -m echo.cli run --config experiments/EXP-003/config.json`

## Amendments before freeze (owner-approved 2026-11-24, round 2)

See `research/protocol.md` section 10, which governs. For this experiment:

- K = 16 genre clusters with FMA-fitted cluster weights and Zipf exponent s = 1.3065 replace K = 10 (uniform) and s = 1.0 (fitted on the FMA training split before the freeze, method in protocol 10.1, journal J-0003; values in `experiments/EXP-003/config.json` and `data/fma_calibration_v1.json`).
- RAND is the confirmed baseline; `skip_utility = 0` is kept and disclosed (skips are near zero except under POP).
- 10 confirmatory seeds, 20261124 to 20261133.
- When the 95 % CI excludes 0 and lies inside [-0.05, 0.05] rad, the result reads "statistically detectable, practically negligible".
- SIM minus RAND drift values seen before the freeze (exploratory seeds, draft parameters) are disclosed in protocol 10.2 item 6 and `research/freeze.json`.
- EXP-003 stays on the synthetic (calibrated) catalogue.
