<!-- SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0 -->
# LinkedIn draft (not published)

*Draft. Status: independent research, preprint draft, not peer-reviewed; simulation only. Numbers identical to `research/paper/manuscript.md`. The owner's full-text review is pending (M6).*

Does a recommender discover your taste or shape it? I tested a narrow version of that question in a pre-registered simulation, and the most useful result was a negative one.

What was built: a seeded simulation of 200 synthetic listeners per seed whose taste vectors adapt to what they choose, five recommendation policies, a frozen protocol, a pre-registered sensitivity test and a second test on 4,951 real tracks from the Free Music Archive.

One defensible finding: the direction of the effect was not a property of the policy. A similarity recommender moved simulated taste less than random exposure on a calibrated synthetic catalogue (-0.0355 rad, 95 % CI [-0.0535, -0.0200]), but the pre-registered sensitivity rule withdrew that interpretation as assumption-dependent, and on the real catalogue the sign reversed (+0.1652 rad, CI [0.1560, 0.1735]; does not replicate).

Caveat: these are synthetic listeners with assumed update rules. Simulated preference change is not evidence of human persuasion, and nothing here describes any commercial service.

Repository: https://github.com/mohamedbechirkefi/echo-recommender-feedback. Interactive page: https://echo-recommender-feedback.kefimohamedbechir.workers.dev.

Mohamed Bechir Kefi, independent researcher.

An AI system (Claude, Anthropic) assisted with code, runs and drafting as a disclosed assistant; it is not an author.
