<!-- SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0 -->
# Literature review (M0 seed, 2026-11-24)

**Scope:** a targeted, non-systematic search, done with web search and fetch in the M0 session. It is not a systematic review.

**What "verified" means here:** the abstract page or full text was opened in this session, and the bibliographic metadata below was read from it. Claims about a paper are limited to what was read; for most entries only the abstract was read. Access date for all entries: 2026-11-24.

## 1. Verified sources

| Key | Reference | Opened | What was read | Relevance |
|---|---|---|---|---|
| chaney2018 | A. J. B. Chaney, B. M. Stewart, B. E. Engelhardt. "How Algorithmic Confounding in Recommendation Systems Increases Homogeneity and Decreases Utility." arXiv:1710.11214 (v2, 2018). Related DOI listed on arXiv: 10.1145/3240323.3240370 (RecSys 2018, venue not confirmed from the page itself). | https://arxiv.org/abs/1710.11214 | Abstract | Simulation showing that feedback loops homogenise user behaviour without raising utility. Motivates the homogenisation metric. |
| jiang2019 | R. Jiang, S. Chiappa, T. Lattimore, A. György, P. Kohli. "Degenerate Feedback Loops in Recommender Systems." AIES 2019. DOI 10.1145/3306618.3314288; arXiv:1902.10730. | https://arxiv.org/abs/1902.10730 | Abstract | Theory of user-interest dynamics under recommendation; separates echo chamber from filter bubble. Motivates the adaptive-preference model. |
| mansoury2020 | M. Mansoury, H. Abdollahpouri, M. Pechenizkiy, B. Mobasher, R. Burke. "Feedback Loop and Bias Amplification in Recommender Systems." arXiv:2007.13019 (2020). | https://arxiv.org/abs/2007.13019 | Abstract | Offline simulation of popularity-bias amplification, with reduced aggregate diversity and taste-representation shift. Motivates the POP arm and the exposure Gini. |
| kalimeris2021 | D. Kalimeris, S. Bhagat, S. Kalyanaraman, U. Weinsberg. "Preference Amplification in Recommender Systems." KDD 2021. DOI 10.1145/3447548.3467298 (from a search result; DOI not opened). | https://research.facebook.com/publications/preference-amplification-in-recommender-systems/ | Abstract | Matrix-factorisation model of users drifting toward recommended content. The closest prior model of "shaping" taste. |
| carroll2022 | M. Carroll, A. Dragan, S. Russell, D. Hadfield-Menell. "Estimating and Penalizing Induced Preference Shifts in Recommender Systems." ICML 2022, PMLR 162:2686-2708. arXiv:2204.11966. | https://arxiv.org/abs/2204.11966 | Abstract | Defines induced preference shift against a "natural shift" reference. This supports using a non-steering reference (RAND) as the comparator. |
| ie2019 | E. Ie, C. Hsu, M. Mladenov, V. Jain, S. Narvekar, J. Wang, R. Wu, C. Boutilier. "RecSim: A Configurable Simulation Platform for Recommender Systems." arXiv:1909.04847 (2019). | https://arxiv.org/abs/1909.04847 | Abstract | Configurable user-state simulation. Design reference. Not used as a dependency. |
| vargas2011 | S. Vargas, P. Castells. "Rank and Relevance in Novelty and Diversity Metrics for Recommender Systems." RecSys 2011, pp. 109-116. DOI 10.1145/2043932.2043955 (from a search result; DOI not opened). | https://castells.github.io/papers/recsys2011.pdf | Title and author block of the PDF (page 1 text) | Framework for novelty and diversity metrics. Motivates the self-information novelty and intra-list diversity definitions. The metric formulas are not yet checked against the paper. |
| defferrard2017 | M. Defferrard, K. Benzi, P. Vandergheynst, X. Bresson. "FMA: A Dataset For Music Analysis." arXiv:1612.01840 (v3, ISMIR 2017 camera-ready). | https://arxiv.org/abs/1612.01840 and https://github.com/mdeff/fma | Abstract and repository README (licence lines) | Candidate public music metadata. See `data/manifest.json`. |

## 2. Unverified (not opened, or opened without the needed content)

- Bertin-Mahieux, Ellis, Whitman, Lamere. "The Million Song Dataset." ISMIR 2011.
  - The official site (millionsongdataset.com) refused the connection, and the Dryad record page shows no dataset licence.
  - Licence terms are unverified.
- O. Celma. Last.fm 1K and 360K datasets. The Zenodo record was opened (see manifest); the Celma 2010 book chapter was not.

## 3. Gap and narrow contribution (proposed, to be revised)

Prior simulations (chaney2018, mansoury2020, kalimeris2021) show homogenisation and amplification, usually for one drift mechanism at a time. ECHO's proposed narrow contribution, if it holds up after review:

- a small, fully reproducible, seeded comparison of five simple policy families against a uniform-random reference, with fixed and adaptive preferences modelled separately;
- an explicit test of whether the policy effect on simulated drift survives a change of drift mechanism (EXP-003).

No novelty is claimed. A broader search (citation chaining from kalimeris2021 and carroll2022) is an M1 task.
