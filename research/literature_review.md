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
| vargas2011 | S. Vargas, P. Castells. "Rank and Relevance in Novelty and Diversity Metrics for Recommender Systems." RecSys 2011, pp. 109-116. DOI 10.1145/2043932.2043955 (from a search result; DOI not opened). | https://castells.github.io/papers/recsys2011.pdf | Full text (8 pages), read 2026-11-25 (PDF SHA-256 3b5fad522fde2b4bd03451927edda02f62903529705005c85e96f9725445aa23, not committed) | Framework for novelty and diversity metrics. Checked at M4: equation 5 defines item novelty as self-information, -log2 p(i given seen), and the mean self-information of recommended items is the rank- and relevance-free special case; equation 16 without rank discount and relevance weighting reduces to the average intra-list distance. ECHO's novelty (base-popularity share as p) and intra-list diversity (distance 1 - cos) are these special cases. |
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

## 4. M4 update (2026-11-25)

- The Vargas and Castells check (an M1 item carried to M4) is closed: see the vargas2011 row.
- Citation chaining from kalimeris2021 and carroll2022 (the other carried item) was not done in M4. The manuscript discloses that the review is targeted and non-systematic and that seven of eight sources were read at abstract level only.

## 5. M6 update (2026-11-25)

The full texts of the seven sources that had been read at abstract level were opened from free, legal copies (arXiv PDFs; for kalimeris2021, the PDF linked from the Meta Research publication page) and checked against the statements made about them. The PDFs were not committed; their SHA-256 values and the supporting page or section for each statement are in `research/claims_register.csv` (X-001 to X-008) and `research/publication/claims_audit.md` (M6 reference table). The "What was read" column of section 1 records the M0 state and is superseded by this section.

- chaney2018, mansoury2020, jiang2019, kalimeris2021, ie2019: the statements in manuscript section 2 hold against the full text. Added precision: chaney2018 holds intrinsic preferences fixed (assumption 3), and mansoury2020 states that the taste shift it reports is in the system's representation of preferences, not in intrinsic preferences (section 4.3.2).
- carroll2022: correction. Section 5 operationalises "natural preference shifts" as the preferences a user would have when interacting with a random recommender. The M4 manuscript said that ECHO's RAND "is not the same construct as their natural shift"; it is the same operationalisation, and the manuscript was corrected (DEC-019).
- defferrard2017: the paper describes the metadata, the 16 top-level genres, the librosa features, the listen counts and the proposed split. It states that the audio is Creative Commons licensed and does not state the metadata licence; the CC BY 4.0 metadata licence rests on the repository README.
- Citation chaining remains not done.
