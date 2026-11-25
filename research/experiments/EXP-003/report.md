<!-- SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0 -->
# EXP-003 report: Drift-assumption sensitivity and adaptation ablation (CONFIRMATORY)

## 1. Identification

- **Experiment:** EXP-003, confirmatory sensitivity analysis of the EXP-002 contrast.
- **Run date:** 2026-11-25. In UTC, runs started 2026-11-24T23:39:24Z and ended 23:52:09Z.
- **Protocol:** `research/experiments/EXP-003/protocol.md`, v1.0, SHA-256 `f0a3e1061d05bd5b58b9998112426b02eb62ef6f34d8783f42a787f19924e49a`. It is governed by `research/protocol.md` v1.0, which the owner froze on 2026-11-24.
- **Config:** `experiments/EXP-003/config.json`, file SHA-256 `285e3dd6b52f271454f0d443934fc7588201247e09ec60d2f1496850254771c0`.
- **Code revisions:**
  - Provenance revision: afc08509847ac362b6b95d8097aea08a615f286b, with `code_dirty: false` in all 360 manifests.
  - Analysis code: 04bc350, committed before any output.
  - Results: f40e935.
- **Status:** complete, 360 of 360 runs ok.
- **Authorship:** Mohamed Bechir Kefi (owner-approved, C3); the AI assisted. Written on the owner's approval of 2026-11-25 (DEC-014) from committed results only.

## 2. Executive summary

- **Question.** Does the SIM versus RAND drift contrast of EXP-002 survive other plausible update rules, drift rates and an oracle recommender profile?
- **Method:**
  - RAND and SIM, under 3 update rules (consumed-item, exposure, bounded-confidence) x eta in {0.01, 0.05, 0.2} x {estimated, oracle} profile x 10 confirmatory seeds = 360 runs.
  - Same calibrated synthetic catalogue as EXP-002.
- **Outcome.** Under the frozen rule the EXP-002 interpretation is **withdrawn as assumption-dependent**. At eta 0.05, under the bounded-confidence rule, SIM minus RAND is:
  - practically equivalent to 0 with the estimated profile: +0.0069 rad, CI [-0.0130, 0.0303];
  - of the opposite sign with the oracle profile: +0.1883 rad, CI [0.1598, 0.2196].
  The sign also changes with eta under the consumed and exposure rules.
- **Principal caveat.** Only three rules and three rates were tested. Other mechanisms remain untested.

## 3. Rationale

- EXP-002 assumes that listeners move toward the item they consume.
- Mere exposure (moving toward the slate mean) and bounded-confidence updating (moving only toward items close to current taste) are competing assumptions of equal simplicity.
- If the conclusion depends on which assumption holds, it is a property of the model, not of the policy (protocol section 7).
- The oracle profile isolates the profile estimator from the policy rule.

## 4. Hypotheses and operational definitions

- **Estimand:** Delta(rule, eta, profile), SIM minus RAND mean drift paired by seed, in radians.
- **Frozen rule** (EXP-003 item 4), with EXP-002's sign as the reference (negative):
  - **Retained** if, in every cell with eta >= 0.05, Delta has the EXP-002 sign and the 95 % CI excludes 0.
  - **Withdrawn as assumption-dependent** if any cell at eta = 0.05 has the opposite sign with a CI excluding 0, or is practically equivalent to 0.
  - **Partially robust** otherwise.
- **Equivalence readings** (DEC-012, ratified by the owner on 2026-11-25): "practically equivalent" is evaluated two ways.
  - The band reading: the CI lies inside [-0.05, 0.05].
  - The label reading: the decision label is exactly "practically equivalent".
  A divergence between them would be flagged.
- **Second check** (protocol section 7): whether Delta under the oracle profile differs in sign from Delta under the estimated profile. It is reported by point-estimate signs and by both CIs excluding 0 with opposite signs.
- **Uncertainty:** 95 % paired bootstrap per cell. Holm-adjusted intervals over the 18 cells are also reported; they do not enter the decision rule.

## 5. Methodology

- **Model:** as EXP-002 (`research/protocol.md` sections 3 and 10), with the update rule, eta and profile varied.
- **Policies:** RAND and SIM only.
- **Seeds:** 20261124 to 20261133, with common random numbers.
- **Hardware:** Apple M1 Pro. One of two worker processes ran under `nice` on a shared machine (load average up to about 87).
- **Analysis:** `src/echo/analysis.py`, `analyse_sensitivity`, with the reference taken from the EXP-002 `analysis.json`.
- **Budget:** at most 1 hour; actual 12 min 45 s.

## 6. Implementation verification

- The same code, revision and pre-run checks as EXP-002 (see the EXP-001 and EXP-002 reports).
- This experiment has no fixed-preference arm, so the negative control does not apply.
- **Internal consistency:** the cell consumed / eta 0.05 / estimated has the same configuration and seeds as the EXP-002 primary contrast. It reproduces it exactly: -0.0355 rad, CI [-0.0535, -0.0200].

## 7. Execution record

- **Commands:**
  - `nice -n 10 env PYTHONPATH=src .venv/bin/python -m echo.cli run --config experiments/EXP-003/config.json`, through the run guard.
  - `PYTHONPATH=src .venv/bin/python -m echo.analysis results/EXP-003 --planned 360 --kind sensitivity --reference results/EXP-002/analysis/analysis.json`
- **Runs:** 360 planned, 360 ok, 0 failed, 0 retried, 0 excluded.
- **Run IDs:** `EXP-003_sensitivity_<rule>_<eta>_<profile>_<POLICY>_s<seed>`.
- **Provenance:** `results/EXP-003/provenance.csv`. Log: `results/logs/EXP-003.log`.
- **Deviations from the frozen protocol:** none. The equivalence readings were fixed in DEC-012 before output and ratified by the owner (DEC-014); both readings gave the same verdict.

## 8. Results

All values come from `results/EXP-003/analysis/analysis.json` (`contrasts.csv`, `per_seed.csv`, `arms.csv`, `analysis.md`).

### 8.1 SIM minus RAND drift per cell (rad, n = 10 seeds)

| Cell (rule / eta / profile) | Mean diff | SD | 95 % bootstrap CI | 95 % paired t CI | d_z | Decision | Holm CI | Holm reject |
|---|---|---|---|---|---|---|---|---|
| bounded / 0.01 / estimated | 0.0363 | 0.0163 | [0.0275, 0.0466] | [0.0247, 0.0480] | 2.23 | statistically detectable, practically negligible | [0.0237, 0.0525] | yes |
| bounded / 0.01 / oracle | 0.0794 | 0.0225 | [0.0669, 0.0930] | [0.0633, 0.0955] | 3.52 | reject H0 | [0.0620, 0.1005] | yes |
| bounded / 0.05 / estimated | 0.0069 | 0.0367 | [-0.0130, 0.0303] | [-0.0194, 0.0331] | 0.19 | practically equivalent | [-0.0130, 0.0303] | no |
| bounded / 0.05 / oracle | 0.1883 | 0.0506 | [0.1598, 0.2196] | [0.1521, 0.2244] | 3.72 | reject H0 | [0.1478, 0.2362] | yes |
| bounded / 0.2 / estimated | -0.1012 | 0.0600 | [-0.1318, -0.0617] | [-0.1442, -0.0583] | -1.69 | reject H0 | [-0.1390, -0.0405] | yes |
| bounded / 0.2 / oracle | 0.1564 | 0.0940 | [0.1037, 0.2145] | [0.0891, 0.2236] | 1.66 | reject H0 | [0.0823, 0.2417] | yes |
| consumed / 0.01 / estimated | 0.1364 | 0.0212 | [0.1234, 0.1484] | [0.1213, 0.1515] | 6.45 | reject H0 | [0.1170, 0.1535] | yes |
| consumed / 0.01 / oracle | 0.0254 | 0.0098 | [0.0197, 0.0313] | [0.0183, 0.0324] | 2.58 | statistically detectable, practically negligible | [0.0174, 0.0343] | yes |
| consumed / 0.05 / estimated | -0.0355 | 0.0286 | [-0.0535, -0.0200] | [-0.0560, -0.0151] | -1.24 | reject H0 | [-0.0621, -0.0149] | yes |
| consumed / 0.05 / oracle | -0.0607 | 0.0252 | [-0.0761, -0.0466] | [-0.0787, -0.0427] | -2.41 | reject H0 | [-0.0825, -0.0424] | yes |
| consumed / 0.2 / estimated | -0.0978 | 0.0353 | [-0.1186, -0.0770] | [-0.1231, -0.0725] | -2.77 | reject H0 | [-0.1265, -0.0688] | yes |
| consumed / 0.2 / oracle | -0.0710 | 0.0331 | [-0.0908, -0.0517] | [-0.0947, -0.0473] | -2.14 | reject H0 | [-0.0983, -0.0453] | yes |
| exposure / 0.01 / estimated | 0.1710 | 0.0482 | [0.1421, 0.1983] | [0.1365, 0.2054] | 3.55 | reject H0 | [0.1303, 0.2079] | yes |
| exposure / 0.01 / oracle | 0.0517 | 0.0370 | [0.0310, 0.0742] | [0.0253, 0.0782] | 1.40 | reject H0 | [0.0244, 0.0830] | yes |
| exposure / 0.05 / estimated | -0.1510 | 0.0497 | [-0.1838, -0.1257] | [-0.1866, -0.1155] | -3.04 | reject H0 | [-0.1947, -0.1213] | yes |
| exposure / 0.05 / oracle | -0.1674 | 0.0383 | [-0.1930, -0.1472] | [-0.1949, -0.1400] | -4.37 | reject H0 | [-0.1997, -0.1438] | yes |
| exposure / 0.2 / estimated | -0.2688 | 0.0593 | [-0.3046, -0.2354] | [-0.3112, -0.2264] | -4.53 | reject H0 | [-0.3119, -0.2286] | yes |
| exposure / 0.2 / oracle | -0.2238 | 0.0532 | [-0.2554, -0.1933] | [-0.2618, -0.1857] | -4.20 | reject H0 | [-0.2589, -0.1895] | yes |

- Holm levels range from 0.95 to 0.9972 by rank (see `contrasts.csv`).
- Figure: `results/EXP-003/analysis/fig-contrasts.svg`, a forest plot of the 18 cells.
  - Thick bars: 95 % bootstrap CI.
  - Thin bars: Holm-level CI.
  - Grey band: the SESOI of plus or minus 0.05 rad.
  - n = 10 seeds per cell.

### 8.2 Robustness verdict (frozen rule)

- **Band reading:** withdrawn as assumption-dependent.
  - Cells triggering withdrawal: bounded / 0.05 / estimated (practically equivalent) and bounded / 0.05 / oracle (opposite sign, CI excluding 0).
  - Cells failing the retain condition: those two, plus bounded / 0.2 / oracle.
- **Label reading:** withdrawn as assumption-dependent.
- **The readings agree. Verdict: withdrawn as assumption-dependent.**

### 8.3 Oracle versus estimated profile (protocol section 7, second check)

| Rule | eta | Estimated mean diff | Oracle mean diff | Point signs differ | Both CIs exclude 0 with opposite signs |
|---|---|---|---|---|---|
| bounded | 0.01 | 0.0363 | 0.0794 | no | no |
| bounded | 0.05 | 0.0069 | 0.1883 | no | no |
| bounded | 0.2 | -0.1012 | 0.1564 | yes | yes |
| consumed | 0.01 | 0.1364 | 0.0254 | no | no |
| consumed | 0.05 | -0.0355 | -0.0607 | no | no |
| consumed | 0.2 | -0.0978 | -0.0710 | no | no |
| exposure | 0.01 | 0.1710 | 0.0517 | no | no |
| exposure | 0.05 | -0.1510 | -0.1674 | no | no |
| exposure | 0.2 | -0.2688 | -0.2238 | no | no |

In one rule-rate pair (bounded, eta 0.2) the sign depends on the profile, with both CIs excluding 0. There, the effect comes from the profile estimator, not the policy family.

### 8.4 Secondary outcomes

Seed-paired homogenisation and skip-rate differences per cell, and per-arm descriptive means for all metrics, are in `analysis.json` and `arms.csv`. They are descriptive and do not enter the verdict.

## 9. Interpretation

- **Expected versus observed.** The test was set up to detect assumption dependence. It found it:
  - The sign of SIM minus RAND depends on the drift rate under the consumed and exposure rules: positive at eta 0.01, negative at 0.05 and 0.2.
  - Under the bounded-confidence rule the contrast is near 0 or positive at eta 0.05, depending on the profile.
  - The exposure rule at eta 0.05 and 0.2 keeps the EXP-002 sign with larger magnitudes (-0.1510 to -0.2688 rad).
- **What is supported:** within this model, whether a similarity policy produces more or less drift than random exposure is not a property of the policy alone. It depends on how simulated listeners update and how fast.
- **What is not supported:** any general statement that similarity recommendation narrows (or amplifies) taste change relative to random exposure.
- **Negative result reported with equal weight:** the EXP-002 primary interpretation is withdrawn by its own pre-registered robustness test.

## 10. Threats to validity

- **External:** three rules and three rates are a small slice of plausible mechanisms, and the catalogue is synthetic.
- **Statistical:**
  - The strict rule applies no multiplicity correction by design (item 14): any adverse cell withdraws the interpretation. This makes withdrawal easier to trigger by chance.
  - The two triggering cells are, however, not marginal: the oracle cell's CI is [0.1598, 0.2196], and the Holm CI also excludes 0.
- **Construct:** the angular drift magnitude does not distinguish movement toward versus away from a listener's home cluster.
- **Internal:** the oracle profile still uses the warm-up (DEC-006), as implemented.

## 11. Conclusion and next experiment

- Under the frozen rule, the EXP-002 interpretation is **withdrawn as assumption-dependent**.
- In M4 the manuscript must report the SIM versus RAND drift direction as conditional on the update rule and rate, with the full 18-cell table.
- A follow-up could characterise where the sign changes (the rate threshold per rule). That would be a new experiment with its own protocol, not a re-analysis of this one.

## 12. Reproduction appendix

- **Environment:** as in the EXP-002 report.
- **Run:** `PYTHONPATH=src .venv/bin/python -m echo.cli run --config experiments/EXP-003/config.json`
- **Analysis:** `PYTHONPATH=src .venv/bin/python -m echo.analysis results/EXP-003 --planned 360 --kind sensitivity --reference results/EXP-002/analysis/analysis.json`
- **Raw results:** `results/EXP-003/runs/`, `manifests/`, `provenance.csv`, `SHA256SUMS`.
- **Records:** journal J-0006; claims C-004, C-005; decisions DEC-012, DEC-013, DEC-014.
