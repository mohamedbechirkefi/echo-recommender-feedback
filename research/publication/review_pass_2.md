<!-- SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0 -->
# Second review pass: arguing against the preferred reading (M4, 2026-11-25)

**Purpose.** Master prompt 11.5 requires a second pass that challenges the preferred hypothesis rather than polishing the text. This pass is AI internal quality control, not peer review. It was run on the first full manuscript draft of 2026-11-25.

**The preferred reading under challenge.** After M3, the reading the project leans toward is: "policies change exposure robustly; the direction of their effect on simulated taste is assumption-dependent." Because the primary hypothesis was already withdrawn by its own robustness test, the pass also challenges the *negative* reading (that the policy does not matter) and the claim that exposure effects are robust.

## Challenges

| Id | Challenge | Holds? | Revision |
|---|---|---|---|
| R-1 | **RAND is not a neutral reference.** Under the consumed rule, RAND moves listeners toward wherever the catalogue's mass lies. On the synthetic catalogue that mass has a strong common direction (resultant length 0.4138, J-0008), so the EXP-002 sign may say more about RAND's pull than about SIM "narrowing". | Yes | The manuscript already states that RAND moves taste (C-008) and makes no narrowing claim; C-001 now says so explicitly. |
| R-2 | **The exposure result is near-tautological.** A top-k similarity policy concentrates impressions and lowers within-slate diversity by design; calling this a finding overstates it, and the contrasts were descriptive, without multiplicity control. | Yes | Abstract, section 6 and conclusion now say "descriptive" and "largely by construction"; C-009 limitation added; limitations item 19. |
| R-3 | **The withdrawal could be a multiplicity artefact.** EXP-003 applies an uncorrected rule to 18 cells, so any adverse cell withdraws. | No | The oracle trigger cell excludes 0 after Holm ([0.1478, 0.2362]); the equivalence cell's paired t CI [-0.0194, 0.0331] is also inside the band. Added to section 5.2 and C-004. |
| R-4 | **Equivalence from 10 seeds.** "Practically equivalent" from a percentile bootstrap with n = 10 may rest on under-coverage. | Partly | The t interval agrees (R-3). The cell is split 6/4 across seeds. The limitation on percentile-bootstrap coverage stays in section 7. |
| R-5 | **EXP-004 intervals are too narrow.** The ten FMA samples overlap within 4,951 tracks, so seeds are not independent and d_z 11.15 overstates precision. | Yes, for widths | Section 7 and limitations item 17 now say so; the sign (all 10 seeds positive) is less exposed. C-006 limitation added. |
| R-6 | **Leakage.** Could calibration or pre-freeze peeking have shaped the confirmatory result? | No, with one caveat | Calibration used the FMA training split and no simulation; EXP-004 uses the test split with a training-split basis. The pilot value was seen at draft parameters and disclosed. Caveat: the claim that the FMA-path smoke's SIM minus RAND values were not inspected rests on the session record only. Added to section 7 and limitations item 20. |
| R-7 | **Stale or wrong text.** The M3 "pi/2 ceiling" phrase; registry statuses saying reports were not written; the skeleton manuscript said "no confirmatory results". | Yes | Corrected (claims audit F-4, F-5); manuscript rewritten. |
| R-8 | **Missing failed runs.** Are there runs not reported? | No | 560/560 confirmatory runs ok; every directory under `results/exploratory/` (EXP-001, EXP-001-m3-smoke, EXP-004-smoke, M4-confounders) is listed in supplementary S1. |
| R-9 | **Construct: drift is just exposure.** With eta 0.05 and about 100 updates, the weight left on the initial taste is about 0.95^100, about 0.006. Final "taste" is close to a recency-weighted average of recent consumption, so the "taste" outcome re-measures exposure, and the research question's separation of the two is weaker than claimed. This also offers an untested explanation of the sign change with eta. | Yes | New paragraph in section 6, limitations item 16 and claim C-013 (labelled analytical, not tested). |
| R-10 | **Overgeneralisation to "the policy".** "SIM" here is one estimator (mean of consumed embeddings) with one warm-up; the bounded / 0.2 cell shows the sign can come from the estimator. | Yes | Already in section 5.2 (C-005); the conclusion speaks of "a similarity recommender" in this model only. |
| R-11 | **"Slightly less drift"** in the abstract is a practical judgement while practical size is unresolved. | Yes | Abstract reworded. |
| R-12 | **Unsupported gap claim.** The introduction said single-mechanism results are "rarely tested" for robustness, which a non-systematic, abstract-level reading cannot support. | Yes | Reworded as a statement about the sources read, with an explicit disclaimer. |
| R-13 | **Agreement with prior work.** "POP homogenises most, in line with chaney2018 and mansoury2020" compares with abstracts only. | Partly | Kept, with "only abstracts were read, no finer comparison is made" (section 6). |
| R-14 | **Geometry story told as mechanism.** Section 5.4 might be read as explaining the EXP-004 reversal. | Partly | Text already says "consistent with, but does not establish"; C-012 limitation repeats it; future work names the separating experiment. |
| R-15 | **POP results read without skips.** POP's FMA drift contrast is negative but its per-accept contrast is positive. | Yes | Section 5.3, C-007 limitation, limitations item 18. |

## What the pass did not change

- No frozen verdict, protocol, config or seed. No confirmatory computation was re-run; the exploratory inspection (J-0008) runs no simulation.
- The primary decision (reject H0), the withdrawal and the non-replication stand as computed.

## Residual risks the owner should know

- The SESOI (0.05 rad) is judgement-based; every "practically" statement inherits it.
- The model choices of DEC-006 were frozen as implemented and never varied.
- The literature base is thin (abstracts) and non-systematic.
