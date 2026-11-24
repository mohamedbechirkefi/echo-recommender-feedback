<!-- SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0 -->
# Limitations (living document, M0 draft)

No results exist yet. This file lists the limitations that are already known from the design.

1. **Simulation only.** Listeners are synthetic agents with an assumed preference-update rule. Simulated preference change is not evidence of human persuasion or of any real listener's behaviour.
2. **Assumed drift mechanism.** The drift magnitude and its sign depend on the update rule and on eta. EXP-003 tests three rules and three rates, but plausible mechanisms beyond these remain untested.
3. **Synthetic catalogue geometry.** Gaussian clusters on a sphere and Zipf popularity are stylised. Real music similarity spaces may differ. Since the 2026-11-24 amendment, K, the cluster weights and the Zipf exponent are fitted on FMA metadata (protocol 10.1), and EXP-004 repeats the main contrast on real FMA tracks. That real catalogue is one similarity space (PCA of librosa statistics) among many, and FMA is a catalogue of freely licensed music, not of a commercial service.
8. **Skip utility.** `skip_utility = 0` is kept by the owner's decision. Skips are then rare for every policy except POP, so the skip-rate confounder is active for POP only.
9. **Listening is simulated.** FMA play counts set popularity only; no real listening session or listener is used.
4. **Simple policies.** The policies are not production recommenders. Nothing in this project describes or infers the internals of any commercial or proprietary service.
5. **Single session horizon.** T = 100 steps with no return or churn dynamics.
6. **No human validation.** The project has no user study, and none will be run without an owner-approved protocol and safeguards.
7. **Toolchain.** No TeX is installed, so `manuscript.tex` is generated but not compile-tested locally.

## Added after the M3 confirmatory runs (2026-11-25)

10. **The EXP-002 contrast is assumption-dependent.** Under the frozen EXP-003 rule the EXP-002 interpretation is withdrawn: at eta 0.05 the bounded-confidence rule makes SIM minus RAND practically equivalent to 0 (estimated profile) or positive (oracle profile), and the sign also changes with eta under the consumed and exposure rules (C-004). Any statement about SIM "narrowing" or "amplifying" drift must name the update rule and rate.
11. **The direction does not carry over to the real catalogue.** On FMA tracks SIM increases drift relative to RAND (+0.165 rad, C-006), the opposite sign to EXP-002. The catalogue geometry matters at least as much as the policy family.
12. **Practical size of the EXP-002 effect is unresolved.** The point estimate (-0.0355 rad) is inside the SESOI; the CI reaches -0.0535 rad.
13. **Drift is large relative to its ceiling.** RAND drift is about 1.11 rad in EXP-002 (pi/2 is about 1.57), so contrasts may be compressed (EXP-002 protocol item 16).
14. **Holm intervals and ties.** The Holm construction is fixed in DEC-012, pending the owner's ratification. Several bootstrap p-values are exactly 0 (no resample on the other side of 0); ties are ranked by contrast name, which changes only the interval levels, not any rejection.
15. **Runtime figures from M3 are not clean measurements.** The machine was shared with other sessions (load average up to about 87), so per-run runtimes in the manifests are upper bounds.
