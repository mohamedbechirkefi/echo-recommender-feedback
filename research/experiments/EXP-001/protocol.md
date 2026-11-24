<!-- SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0 -->
# EXP-001: Simulator verification and smoke matrix (exploratory)

**Status:** planned (protocol draft, awaiting owner freeze).
**Type:** exploratory and verification. This experiment never supports a confirmatory claim.
**Protocol version:** draft 0.1, 2026-11-24. **Hash:** none yet.

Section numbers follow master prompt 11.2.

1. **Question.** Does the simulator behave correctly (determinism, negative control, bounds, schema)? What are the runtime and the between-seed variance needed to size EXP-002?
2. **Mechanism and rationale.** EXP-002 is only interpretable if the simulator is correct. A zero-drift negative control under fixed preferences tests that the drift metric measures only the update rule. See `research/protocol.md` sections 3 to 5.
3. **Competing explanations.** Non-zero drift under fixed preferences would indicate a defect, for example a mutated preference buffer or a normalisation error, not an effect.
4. **Hypotheses (verification checks, pass or fail):**
   - V1: identical config and seed give byte-identical result JSON.
   - V2: with eta = 0, theta_u = 0 exactly for all users and policies.
   - V3: no consumed track ever reappears in a slate (candidate exclusion).
   - V4: all embeddings and preferences have unit norm within 1e-12.
   - V5: every metric lies inside its stated bounds.
   - V6: the result JSON validates against schema v1.
5. **Estimand.** None (verification). Descriptive outputs: per-run wall-clock time, peak memory, and the between-seed SD of the SIM minus RAND drift difference.
6. **Unit and scope.** One run = one policy x one preference model x one smoke seed.
7. **Variables.**
   - Policy (RAND, POP, SIM, MMR, EXPLORE).
   - Preference model (fixed with eta = 0; adaptive with eta = 0.05).
8. **Treatment, control and baseline.** RAND is the baseline. The fixed preference model is the negative control.
9. **Seeds.** Smoke seeds 900000 and 900001, disjoint from confirmatory seeds. A separate variance pilot uses seeds 900002 to 900011 at the full EXP-002 size, SIM and RAND only, adaptive preferences.
10. **Sample size.** 5 x 2 x 2 = 20 smoke runs, plus 20 pilot runs. Chosen for speed, not power.
11. **Compute budget.** 10 minutes of wall-clock at most.
12. **Metrics.** All metrics of `research/protocol.md` section 4, with the same formulas and units.
13. **Uncertainty.** Not applicable to the pass or fail checks. The pilot SD is reported with its n.
14. **Exclusion and stopping.** None excluded. Any failed check stops EXP-002 until the defect is fixed and recorded.
15. **Anticipated failure modes.**
    - Floating-point non-determinism across numpy builds.
    - arccos of values slightly above 1 (handled by clipping).
    - The candidate pool exhausted when T x k is close to N at smoke size (N = 100, T = 20, k = 10). The design check is T <= N - k.
16. **Sensitivity.** None (verification).
17. **Disconfirmation.** Any failed check V1 to V6 means the implementation does not operationalise the protocol.
18. **Reproduction (planned commands; they do not exist yet).**
    - `uv run python -m echo.cli smoke --out results/EXP-001/`
    - `uv run pytest`
