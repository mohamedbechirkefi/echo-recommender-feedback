<!-- SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0 -->
# Author review (owner)

Status: open. Only the owner ticks a box. At M5 (2026-11-25, DEC-018) three boxes that earlier agent sessions had ticked were unticked; the owner decisions they recorded still stand and are noted after each item. The owner reviews and approves the following.

- [ ] Authorship and affiliation metadata (no invented affiliation). Recorded owner decision: "Mohamed Bechir Kefi", no affiliation (C3, owner-approved 2026-11-24).
- [ ] AI-assistance disclosure text
- [ ] Frozen protocols and any amendments
- [ ] Every claim in the manuscript and articles
- [ ] Limitations and ethics sections
- [ ] Decision whether, where and when to publish
- [ ] M4 manuscript draft (`research/paper/manuscript.md`), supplementary and second review pass (`research/publication/review_pass_2.md`)
- [ ] Claims audit findings F-2 (CSV formatting of t intervals) and F-3 (per-accept decision label). Recorded owner decision: fixed (owner, 2026-11-25, "Approve all" (post-M4); DEC-016).
- [ ] Wording of the funding, competing-interest and AI-assistance statements in manuscript section 11. Recorded owner decision: approved (owner, 2026-11-25, "Approve all" (post-M4); DEC-017).
- [ ] M5 interactive page (`demo/`) and article drafts (`articles/medium.md`, `articles/linkedin.md`), including the article titles

## Prepared for the owner (M6, 2026-11-25)

No box above was ticked by an agent at M6; none was ticked when M6 began (the three agent ticks were removed at M5, DEC-018). Under owner, 2026-11-25, "Next" (second), only the owner ticks a box.

What to read for each item:

- **Authorship and affiliation metadata:** `research/paper/manuscript.md`, "Author and affiliation metadata"; `CITATION.cff`, `authors`.
- **AI-assistance disclosure text:** `research/paper/manuscript.md`, section 11, third bullet; `CITATION.cff`, `message`.
- **Frozen protocols and any amendments:** `research/protocol.md`; `research/experiments/EXP-00N/protocol.md`; `research/freeze.json` (`post_freeze_decisions`, `ratifications`); supplementary section S8; `research/decision_log.md`, DEC-009 to DEC-016.
- **Every claim in the manuscript and articles:** `research/claims_register.csv`; `research/publication/claims_audit.md`, including the M6 reference table (findings F-12 and F-13); `articles/medium.md`; `articles/linkedin.md`.
- **Limitations and ethics sections:** `research/paper/manuscript.md`, sections 7 and 8; `research/limitations.md`.
- **Decision whether, where and when to publish:** `research/publication/release_checklist.md`; `research/publication/reproducibility_report.md`; `research/publication/dependency_licences.md`.
- **M4 manuscript draft, supplementary and second review pass:** `research/paper/manuscript.pdf` (14 pages) and `research/paper/supplementary.pdf` (7 pages), built from the Markdown sources; `research/publication/review_pass_2.md`.
- **Claims audit findings F-2 and F-3:** `research/publication/claims_audit.md`, rows F-2 and F-3; DEC-016.
- **Funding, competing-interest and AI-assistance statements:** `research/paper/manuscript.md`, section 11; DEC-017.
- **M5 interactive page and article drafts:** `demo/` (build with `npm ci && npm run build && npm run preview`); `articles/medium.md`; `articles/linkedin.md`; `docs/demo.png`.

Open decisions for this repository, each for the owner:

1. Whether to sign off this checklist; every box above is unticked.
2. Whether, where and when to publish (G-PUBLIC); nothing has been pushed, tagged or released.
3. The public repository URL and the public demo URL, which are placeholders in the files listed below.
4. The manuscript title, which is not among the titles approved on 2026-11-25 (post-M4), so `CITATION.cff` keeps its own title "ECHO: music recommendation feedback" and does not yet match the manuscript.
5. The release-candidate version `0.1.0-rc1` set in `CITATION.cff` at M6, and the re-adding of `date-released` at the owner's publication step.
6. The corrected description of carroll2022 in manuscript section 2 (F-12, DEC-019), which replaced an M4 sentence after the full text was read.
7. Whether the licence files' repository address (`LICENSE` line 186, `CLA.md` line 19, `.github/workflows/cla.yml` lines 32 and 38: `github.com/mohamedbechirkefi/echo-recommender-feedback`) is the intended public URL; agents do not change licence files.
8. Whether citation chaining from kalimeris2021 and carroll2022 (roadmap M1 item, not done) is required before publication.
9. The manuscript status line still reads "Version M4 draft"; whether it should name the release candidate.

Owner placeholders that remain (file and line, at the M6 commit):

- `README.md` line 48 (public demo URL) and line 80 (repository URL).
- `CITATION.cff` line 5 (`message`: repository URL).
- `research/paper/manuscript.md` line 228 (repository URL).
- `articles/medium.md` line 44 (repository link) and `articles/linkedin.md` line 14 (repository and interactive page).
- `demo/README.md` line 25 (public demo URL) and `demo/src/App.tsx` line 53 (repository URL on the page).
- `scripts/export_demo_data.py` line 410, the source of the same notice in `demo/public/data/results.json`.
