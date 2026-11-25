<!-- SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0 -->
# Supplementary material: Does a similarity recommender shape simulated taste?

**Status: independent research manuscript / preprint draft, not peer-reviewed.** Companion to `research/paper/manuscript.md`, M4 draft, 2026-11-25. Simulation results only.

## S1. Complete experimental matrix

| Experiment | Type | Factors | Seeds | Runs planned | Runs ok | Report |
|---|---|---|---|---|---|---|
| EXP-001 | exploratory, verification | smoke 5 policies x fixed/adaptive x 2 seeds (N 100, U 20, T 20); variance pilot SIM, RAND x 10 seeds; timing block; one-seed screen of the 36 EXP-003 cells | 900000 to 900012 | 86 (two executions) | 86 and 86 | `research/experiments/EXP-001/report.md` |
| EXP-001 FMA-path smoke | exploratory | smoke block on the FMA catalogue | 900000, 900001 | 20 | 20 | same |
| EXP-002 | confirmatory, primary | 5 policies x {fixed, adaptive eta 0.05} | 20261124 to 20261133 | 100 | 100 | `research/experiments/EXP-002/report.md` |
| EXP-003 | confirmatory, sensitivity | RAND, SIM x {consumed, exposure, bounded} x eta {0.01, 0.05, 0.2} x {estimated, oracle} | 20261124 to 20261133 | 360 | 360 | `research/experiments/EXP-003/report.md` |
| EXP-004 | confirmatory, second test | as EXP-002 on the FMA catalogue | 20261124 to 20261133 | 100 | 100 | `research/experiments/EXP-004/report.md` |
| M4 confounder inspection | exploratory, no simulation | reads committed results; regenerates inputs only | confirmatory seeds (inputs only) | none | none | `results/exploratory/M4-confounders/confounders.md` (J-0008) |

No confirmatory run failed, was retried or was excluded (560 of 560 ok).

## S2. EXP-003, all 18 cells (SIM minus RAND drift, rad, n = 10 seeds)

Source: `results/EXP-003/analysis/contrasts.csv` and `analysis.json`; figure `results/EXP-003/analysis/fig-contrasts.svg`. The sign counts (seeds below and above 0) are exploratory (J-0008).

| Cell (rule / eta / profile) | Mean diff | 95 % bootstrap CI | Holm CI | d_z | Decision | Seeds < 0 / > 0 |
|---|---|---|---|---|---|---|
| bounded / 0.01 / estimated | 0.0363 | [0.0275, 0.0466] | [0.0237, 0.0525] | 2.23 | statistically detectable, practically negligible | 0 / 10 |
| bounded / 0.01 / oracle | 0.0794 | [0.0669, 0.0930] | [0.0620, 0.1005] | 3.52 | reject H0 | 0 / 10 |
| bounded / 0.05 / estimated | 0.0069 | [-0.0130, 0.0303] | [-0.0130, 0.0303] | 0.19 | practically equivalent | 6 / 4 |
| bounded / 0.05 / oracle | 0.1883 | [0.1598, 0.2196] | [0.1478, 0.2362] | 3.72 | reject H0 | 0 / 10 |
| bounded / 0.2 / estimated | -0.1012 | [-0.1318, -0.0617] | [-0.1390, -0.0405] | -1.69 | reject H0 | 9 / 1 |
| bounded / 0.2 / oracle | 0.1564 | [0.1037, 0.2145] | [0.0823, 0.2417] | 1.66 | reject H0 | 0 / 10 |
| consumed / 0.01 / estimated | 0.1364 | [0.1234, 0.1484] | [0.1170, 0.1535] | 6.45 | reject H0 | 0 / 10 |
| consumed / 0.01 / oracle | 0.0254 | [0.0197, 0.0313] | [0.0174, 0.0343] | 2.58 | statistically detectable, practically negligible | 0 / 10 |
| consumed / 0.05 / estimated | -0.0355 | [-0.0535, -0.0200] | [-0.0621, -0.0149] | -1.24 | reject H0 | 10 / 0 |
| consumed / 0.05 / oracle | -0.0607 | [-0.0761, -0.0466] | [-0.0825, -0.0424] | -2.41 | reject H0 | 10 / 0 |
| consumed / 0.2 / estimated | -0.0978 | [-0.1186, -0.0770] | [-0.1265, -0.0688] | -2.77 | reject H0 | 10 / 0 |
| consumed / 0.2 / oracle | -0.0710 | [-0.0908, -0.0517] | [-0.0983, -0.0453] | -2.14 | reject H0 | 10 / 0 |
| exposure / 0.01 / estimated | 0.1710 | [0.1421, 0.1983] | [0.1303, 0.2079] | 3.55 | reject H0 | 0 / 10 |
| exposure / 0.01 / oracle | 0.0517 | [0.0310, 0.0742] | [0.0244, 0.0830] | 1.40 | reject H0 | 1 / 9 |
| exposure / 0.05 / estimated | -0.1510 | [-0.1838, -0.1257] | [-0.1947, -0.1213] | -3.04 | reject H0 | 10 / 0 |
| exposure / 0.05 / oracle | -0.1674 | [-0.1930, -0.1472] | [-0.1997, -0.1438] | -4.37 | reject H0 | 10 / 0 |
| exposure / 0.2 / estimated | -0.2688 | [-0.3046, -0.2354] | [-0.3119, -0.2286] | -4.53 | reject H0 | 10 / 0 |
| exposure / 0.2 / oracle | -0.2238 | [-0.2554, -0.1933] | [-0.2589, -0.1895] | -4.20 | reject H0 | 10 / 0 |

Verdict: withdrawn as assumption-dependent under both equivalence readings (DEC-012, DEC-014). Cells triggering withdrawal: bounded / 0.05 / estimated and bounded / 0.05 / oracle. Cells failing the retain condition: those two and bounded / 0.2 / oracle.

## S3. Oracle versus estimated profile (protocol section 7)

| Rule | eta | Estimated | Oracle | Point signs differ | Both CIs exclude 0 with opposite signs |
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

## S4. Pre-specified secondary: drift per accepted item, and the skip confounder

Seed-paired differences versus RAND, adaptive. The SIM rows are the pre-specified secondary; the other rows are descriptive and were set side by side in the exploratory inspection (J-0008). Units: rad per accepted track.

| Experiment / contrast | Drift diff (rad) | Per-accept diff | 95 % CI | Skip-rate diff | Same sign |
|---|---|---|---|---|---|
| EXP-002 SIM-RAND | -0.0355 | -0.000419 | [-0.000605, -0.000263] | -0.0050 | yes |
| EXP-002 POP-RAND | 0.1630 | 0.002363 | [0.002036, 0.002722] | 0.0452 | yes |
| EXP-002 MMR-RAND | -0.1162 | -0.001226 | [-0.001403, -0.001074] | -0.0048 | yes |
| EXP-002 EXPLORE-RAND | -0.0381 | -0.000445 | [-0.000641, -0.000282] | -0.0050 | yes |
| EXP-004 SIM-RAND | 0.1652 | 0.001581 | [0.001489, 0.001664] | -0.0101 | yes |
| EXP-004 POP-RAND | -0.0357 | 0.002818 | [0.002458, 0.003111] | 0.3142 | no |
| EXP-004 MMR-RAND | 0.0570 | 0.000499 | [0.000435, 0.000569] | -0.0100 | yes |
| EXP-004 EXPLORE-RAND | 0.1631 | 0.001560 | [0.001467, 0.001650] | -0.0101 | yes |

Note: the analysis code also attaches a decision label to the per-accept contrast using the 0.05 rad SESOI band, whose unit (rad) differs from the per-accept unit (rad per track). That label is not meaningful and is not used anywhere (evidence-audit finding F-3).

## S5. Exploratory: listener-level drift distribution (J-0008)

Pooled over 10 seeds x 200 listeners per arm; listeners are not independent, so this is descriptive only.

| Arm | P10 (rad) | Median (rad) | P90 (rad) | Max (rad) | Share above pi/2 |
|---|---|---|---|---|---|
| EXP-002 RAND | 0.3919 | 1.2292 | 1.4912 | 1.8046 | 0.042 |
| EXP-002 POP | 0.8860 | 1.2978 | 1.6367 | 1.9125 | 0.163 |
| EXP-002 SIM | 0.3714 | 1.1932 | 1.5015 | 2.2116 | 0.059 |
| EXP-002 MMR | 0.3674 | 1.0916 | 1.3880 | 1.8373 | 0.019 |
| EXP-002 EXPLORE | 0.3688 | 1.1858 | 1.4961 | 2.2282 | 0.059 |
| EXP-004 RAND | 0.4924 | 0.6579 | 0.9761 | 1.5441 | 0.000 |
| EXP-004 POP | 0.4543 | 0.6232 | 0.9076 | 1.3076 | 0.000 |
| EXP-004 SIM | 0.5981 | 0.8025 | 1.2379 | 1.8302 | 0.018 |
| EXP-004 MMR | 0.5394 | 0.7082 | 1.0765 | 1.4677 | 0.000 |
| EXP-004 EXPLORE | 0.5877 | 0.7987 | 1.2465 | 1.7869 | 0.019 |

## S6. Exploratory: catalogue and initial-taste geometry (inputs only, J-0008)

Mean over the 10 confirmatory seeds, with [min, max]. Regenerated from the frozen configs and each seed's catalogue and listener streams; no session or outcome was simulated.

| Quantity | Synthetic calibrated (EXP-002) | FMA (EXP-004) |
|---|---|---|
| Mean pairwise cosine of cluster centres | 0.0082 [-0.0233, 0.0366] | 0.1692 [0.1692, 0.1692] |
| Mean pairwise cosine of tracks | 0.1721 [0.1192, 0.2029] | 0.0052 [0.0024, 0.0092] |
| Resultant length of the mean track embedding | 0.4138 [0.3466, 0.4513] | 0.0777 [0.0582, 0.1008] |
| Mean cosine of a track to its own centre | 0.9313 [0.9304, 0.9321] | 0.3327 [0.3226, 0.3454] |
| Mean nearest-neighbour cosine | 0.9509 [0.9502, 0.9517] | 0.8263 [0.8212, 0.8297] |
| Largest cluster share | 0.2819 [0.2530, 0.3100] | 0.2946 [0.2680, 0.3280] |
| Gini of base popularity | 0.9014 [0.9014, 0.9014] | 0.6705 [0.6587, 0.6934] |
| Mean pairwise cosine of initial tastes | 0.0618 [0.0342, 0.0858] | 0.1960 [0.1208, 0.2462] |
| Mean cosine of initial tastes to tracks | 0.0674 [0.0257, 0.1215] | -0.0061 [-0.0122, 0.0064] |

The FMA genre centres are fixed (calibration split), hence the zero range. The synthetic base-popularity Gini is constant because Zipf weights over a permutation of ranks have the same distribution in every seed.

## S7. Configurations and hashes

| Item | SHA-256 |
|---|---|
| `research/protocol.md` v1.0 | a81ed32c5e21f06e68d61e00250119762d1a56cdf4230a05ac3d89ff48c8f5dc |
| EXP-001 protocol | 5d869d0f418956cdac48cb94a97a8a890aa96ba81193bb4a898664704830cff4 |
| EXP-002 protocol | 3852ad1950f73740378c6f19339d912da57c69daab82d218c3b8efb33af192b2 |
| EXP-003 protocol | f0a3e1061d05bd5b58b9998112426b02eb62ef6f34d8783f42a787f19924e49a |
| EXP-004 protocol | 4f6a5ca60c788a2bee49abaef5af3ca2c039152d1ec0569ab4d54c0f79d75402 |
| `experiments/EXP-002/config.json` (file) | 903f524679afb4a67fe4e6d36ff5b17f7f398475fa7f58c0c993846a64ef174c |
| `experiments/EXP-003/config.json` (file) | 285e3dd6b52f271454f0d443934fc7588201247e09ec60d2f1496850254771c0 |
| `experiments/EXP-004/config.json` (file) | efb26feb7078799642631b15e6ec4604b59aebf49405c6ff3dec8bf3ad55560d |
| `data/manifest.json` | 0db8d76f8dbc693496e7d5e5b35d9034fb98fd913d44ce379a9bb77669e0fae3 |
| `data/fma_calibration_v1.json` | e3c763c27492dd7c7c06bbd73d5cf3a1cba232bf6bed1db80078791b6c208b98 |
| Processed FMA catalogue | e5a0084a28a4afbcb8cc2f6b212c7de678ab21ebf3146e0066bef43172a8dd30 |
| Raw `fma_metadata.zip` | d9527a5297a65da31c5676484d5047c3e2b8a8060ce72a46e26158be736bf265 |

Code revisions: freeze 17ac055; analysis code 04bc350 (committed before any confirmatory output); provenance revision of all 560 confirmatory runs afc0850 (clean tree); results committed in f40e935. Per-run configuration hashes are in `results/EXP-00N/provenance.csv`.

## S8. Deviations and owner decisions

| Id | Date | What | Effect |
|---|---|---|---|
| DEC-009 | 2026-11-24 | Pre-freeze amendments (FMA calibration, RAND baseline, `skip_utility = 0`, 10 seeds, the "statistically detectable, practically negligible" reading, EXP-001 additions, disclosure of values seen) | Owner-approved before the freeze |
| DEC-010 | 2026-11-24 | Protocol v1.0 frozen by the owner | All hashes recorded |
| DEC-011 | 2026-11-24 | Reproduction-command correction ratified | No hash change |
| DEC-012 | 2026-11-25 | Holm construction, two equivalence readings, two-way sign check, fixed before output | Ratified by the owner (DEC-014); readings agreed in every verdict |
| DEC-013 | 2026-11-25 | M3 execution: no protocol deviation; FMA-path smoke added (exploratory); reports deferred | Reports later approved |
| DEC-014 | 2026-11-25 | Owner ratifies DEC-012 and approves the experiment reports | |
| DEC-015 | 2026-11-25 | M4: exploratory confounder inspection; evidence-audit findings and corrections | No verdict changed |

## S9. Report links

- EXP-001: `research/experiments/EXP-001/report.md`
- EXP-002: `research/experiments/EXP-002/report.md`
- EXP-003: `research/experiments/EXP-003/report.md`
- EXP-004: `research/experiments/EXP-004/report.md`
- Evidence audit: `research/publication/claims_audit.md`; second review pass: `research/publication/review_pass_2.md`.
