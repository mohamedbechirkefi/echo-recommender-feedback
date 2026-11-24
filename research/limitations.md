<!-- SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0 -->
# Limitations (living document, M0 draft)

No results exist yet. This file lists the limitations that are already known from the design.

1. **Simulation only.** Listeners are synthetic agents with an assumed preference-update rule. Simulated preference change is not evidence of human persuasion or of any real listener's behaviour.
2. **Assumed drift mechanism.** The drift magnitude and its sign depend on the update rule and on eta. EXP-003 tests three rules and three rates, but plausible mechanisms beyond these remain untested.
3. **Synthetic catalogue geometry.** Gaussian clusters on a sphere and Zipf popularity are stylised. Real music similarity spaces may differ.
4. **Simple policies.** The policies are not production recommenders. Nothing in this project describes or infers the internals of any commercial or proprietary service.
5. **Single session horizon.** T = 100 steps with no return or churn dynamics.
6. **No human validation.** The project has no user study, and none will be run without an owner-approved protocol and safeguards.
7. **Toolchain.** No TeX is installed, so `manuscript.tex` is generated but not compile-tested locally.
