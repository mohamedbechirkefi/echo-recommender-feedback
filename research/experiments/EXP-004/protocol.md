<!-- SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0 -->
# EXP-004: The policy contrast on a real music catalogue (FMA), second test

**Status:** frozen by the owner on 2026-11-24 (v1.0), not yet run. Confirmatory secondary test.
**Protocol version:** 1.0, 2026-11-24. **Hash:** recorded in `research/freeze.json` and the registry.
**Depends on:** EXP-001 (simulator checks) and the FMA ingestion (`scripts/build_fma_catalogue.py`). Analysed alongside EXP-002.
**Origin:** owner approval of real data, 2026-11-24, second round ("Approve all"): "FMA metadata, CC BY 4.0. Real catalogue and genres; listening stays simulated." Method fixed in `research/protocol.md` section 10.1 before any fit.

Section numbers follow master prompt 11.2.

1. **Question.** Does the SIM vs RAND drift contrast of EXP-002 hold when the synthetic catalogue is replaced by real FMA tracks (real audio-feature geometry, real genres, real play-count popularity), with listeners still simulated?
2. **Mechanism and rationale.** The EXP-002 catalogue is Gaussian clusters on a sphere. Real music similarity spaces are less separated and less regular. If the policy effect depends on the stylised geometry, it should change on a real catalogue.
3. **Competing explanations.** A difference between EXP-002 and EXP-004 may come from the embedding (PCA of librosa statistics is one of many possible similarity spaces), from the unbalanced genre sizes, or from the heavier popularity tail, not from "realism" in general. These are reported as alternatives.
4. **Hypotheses.** H0: Delta_FMA = 0. H1: Delta_FMA != 0, where Delta_FMA is the seed-level paired mean difference in angular drift, SIM minus RAND, adaptive preferences, on the FMA catalogue. SESOI 0.05 rad. Decision rule as in `research/protocol.md` section 2 and section 10.2 item 4. Reading against EXP-002 (fixed in protocol 10.1): replicates, does not replicate, or inconclusive on the real catalogue.
5. **Estimand.** Delta_FMA in radians, over the distribution of 1000-track samples of the eligible FMA test-split tracks and simulated listener populations.
6. **Unit and scope.** The seed: one sampled 1000-track catalogue and 200 simulated listeners. Scope: FMA test-split tracks with a top-level genre and finite features; the simulated listener model of section 3.
7. **Independent variables.** Policy (RAND, POP, SIM, MMR lambda 0.5, EXPLORE epsilon 0.2); preference model (fixed, adaptive eta 0.05).
8. **Dependent variables.** As in EXP-002.
9. **Treatment, control and baseline.** RAND is the baseline. The fixed preference model is the negative control (drift exactly 0).
10. **Seeds.** The 10 confirmatory seeds 20261124 to 20261133, common random numbers across policies. The catalogue sample depends on the seed only.
11. **Sample size.** 5 x 2 x 10 = 100 runs. The seed count follows EXP-002 (precision rule of section 5); no separate pilot on the real catalogue was run, so no real-catalogue contrast was seen before the freeze.
12. **Compute budget.** At most 1 hour of wall-clock, local CPU.
13. **Metrics.** `research/protocol.md` section 4. Clusters are the K = 16 FMA top-level genres; novelty uses listens + 1 as base popularity.
14. **Uncertainty.** As in EXP-002: 95 % percentile bootstrap over seeds (10,000 resamples, bootstrap seed 7), paired t interval, d_z; Holm-adjusted intervals for the POP, MMR and EXPLORE drift contrasts.
15. **Exclusion and stopping.** Track eligibility is fixed by the ingestion (counts in `data/fma_calibration_v1.json`). No run is excluded. The 10 % failure stop rule applies. Fixed matrix, no optional stopping.
16. **Anticipated failure modes.** Genre centres in PCA space may be close together, so listener home clusters overlap; the discovery metric then has a different meaning. A processed catalogue whose SHA-256 differs from the configured one stops the run (fail closed).
17. **Sensitivity.** None beyond EXP-003, which stays on the synthetic catalogue.
18. **What contradicts H1.** A 95 % CI for Delta_FMA inside [-0.05, 0.05] rad.
19. **Reproduction.**
    - `python3 scripts/download_fma_metadata.py`
    - `PYTHONPATH=src .venv/bin/python scripts/build_fma_catalogue.py` (checks nothing by itself; the run checks the SHA-256)
    - `PYTHONPATH=src .venv/bin/python -m echo.cli run --config experiments/EXP-004/config.json`
