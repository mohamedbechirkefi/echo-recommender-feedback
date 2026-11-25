<!-- SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0 -->
# Does a recommender discover your taste or shape it? In a pre-registered simulation, the answer depended on the assumptions

*Draft for Medium, not published. Status: independent research, preprint draft, not peer-reviewed. Simulation only. Every number below is identical to the manuscript (`research/paper/manuscript.md`). Article title drafted at M5; the owner's full-text review is pending (M6).*

## The question

A music recommender learns from what you play. But what you play is partly what it showed you. If your taste adapts to what you hear, the recommender may end up shaping the preferences it claims to reflect.

ECHO asks a narrow version of that question in a simulation: **can recommendation policies change exposure and simulated taste rather than simply reflect it?** Nothing here is about real listeners or any real service. The listeners are synthetic agents, and simulated preference change is not evidence of human persuasion.

## What was built

Each simulated listener has a taste vector in a 16-dimensional space. For 100 steps, a policy shows a slate of 10 tracks; the listener picks one or skips, and, under the adaptive model, its taste moves a small step (eta 0.05) toward the track it chose. Five policies were compared: uniform random (RAND, the baseline), popularity (POP), similarity to the listener's history (SIM), a diversified similarity policy (MMR) and an epsilon-greedy explorer (EXPLORE).

The outcome is **drift**: the angle, in radians, between a listener's starting taste and its final taste. The question becomes whether SIM moves taste more or less than random exposure.

*Figure (visual explanation): the taste map on the project's interactive page shows catalogue tracks in a 2-D projection and one simulated listener's taste path under SIM and under RAND. Alt text: grey dots for tracks, a red line for the SIM path and a dark grey line for the RAND path, each from a circle (start) to a square (end). It is an exploratory illustration from one seed, not a result.*

## How it was tested

Before any confirmatory run, the owner froze the protocol: the primary contrast (SIM minus RAND drift), the decision rule, a smallest effect size of interest of 0.05 rad, 10 seeds with matched random numbers, and two pre-registered follow-ups. One follow-up (EXP-003) varied the assumed update rule and rate, with a rule written in advance for withdrawing the interpretation. The other (EXP-004) repeated the experiment on 4,951 real tracks from the Free Music Archive (FMA), with real genres, audio features and play counts, and simulated listeners.

## What happened

**The primary experiment found an effect.** On a synthetic catalogue calibrated on FMA metadata, SIM produced less drift than RAND: -0.0355 rad, 95 % bootstrap CI [-0.0535, -0.0200], over 10 seeds. The frozen rule says "reject H0". Whether the difference matters in practice is unresolved: the point estimate is inside the smallest effect of interest, but the interval extends past it.

**The pre-registered sensitivity test withdrew it.** Under a bounded-confidence update rule (a listener only moves toward tracks already close to its taste) at the same rate, the contrast was practically equivalent to zero (+0.0069 rad, CI [-0.0130, 0.0303]) or, with an oracle profile, reversed (+0.1883 rad, CI [0.1598, 0.2196]). The sign also changed with the update rate. The frozen verdict is "withdrawn as assumption-dependent". Two readings of "practically equivalent" were fixed before any output (DEC-012); both give this verdict.

**The real catalogue reversed it.** On FMA tracks, SIM moved taste *more* than RAND: +0.1652 rad, CI [0.1560, 0.1735]. The frozen reading: does not replicate.

**Exposure did change, as expected.** SIM concentrated what listeners were shown relative to RAND on both catalogues (exposure Gini +0.5118 [0.4883, 0.5336] synthetic, +0.6796 [0.6652, 0.6925] FMA). These were descriptive outcomes, and a personalised top-k policy concentrates exposure largely by construction.

One more observation matters for reading all of this: random exposure is not neutral. Under the adaptive model, RAND itself moved preferences by 1.1119 rad on average on the synthetic catalogue. The study compares *how much* policies move taste, not *whether*.

## What it means, and what it does not

Within this model, the direction of simulated taste change is not a property of the policy alone. It depends on how simulated listeners update, how fast, and on the geometry of the catalogue. The bounded answer to the title is: in this simulation, whether a similarity recommender "shapes" taste more or less than random exposure depends on assumptions that a single-mechanism simulation would hide.

Limitations are real. The listeners are synthetic agents with assumed update rules; three rules and three rates are a small slice of plausible mechanisms. At eta 0.05, a listener's starting taste is almost forgotten after 100 updates, so drift largely re-measures recent consumption. The real catalogue is one audio-feature embedding of freely licensed music. There are 10 seeds per arm, and the smallest effect of interest was a judgement call. No claim about human listeners, Spotify or any commercial recommender follows.

## Reproduce it

Protocols, frozen configs, raw runs, analyses, a claims register and an evidence audit are in the repository: [repository link placeholder, not published; publication requires the owner's approval]. The interactive page (published results with intervals, the taste map and an in-browser sandbox) is in `demo/`: [demo link placeholder]. The manuscript and four experiment reports are in `research/`.

*AI assistance: an AI system (Claude, Anthropic) wrote the simulation and analysis code, ran the experiments under the owner-frozen protocol and drafted the reports, the manuscript and this article. The owner set the question, approved the protocol freeze and retains authority over claims and publication.*
