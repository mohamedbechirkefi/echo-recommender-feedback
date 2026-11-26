<!-- SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0 -->
# ECHO demo: design plan (owner request, 2026-11-26)

## Subject, audience, job

- **Subject.** Whether a music recommender changes the taste it is meant to reflect, in a seeded simulation. The
  study measures taste change as an angle: the angular drift of a listener's preference vector, in radians. The
  vernacular is the record: a sleeve, a spinning disc, a tonearm whose needle sits at an angle, liner notes set in
  a book face.
- **Audience.** A curious technical reader, an admissions committee, a researcher checking the numbers.
- **Primary job.** State the question and the answer in one sentence; show the result as what it literally is, an
  angle (needles on a record), on both catalogues so the reversal is visible at a glance; then give every number,
  the exploratory taste map and the sandbox.

## Palette (light inner-sleeve page, plum sleeve band)

| Name | Hex | Role |
|---|---|---|
| Inner sleeve | `#F4F1F7` | page background, a cool lilac-white paper (not cream) |
| Aubergine ink | `#24182C` | text, rules, the logo in one colour |
| Sleeve plum | `#4A2259` | hero band and footer, the record sleeve |
| Vinyl | `#1E1A22` | the disc in the hero and in the key-result figure |
| Label rose | `#F29CB7` | the record's centre label, focus ring on plum, the logo's label |
| Groove lilac | `#C9B8D6` | secondary text and grooves on plum |

Policy inks keep the study's figure colours: RAND graphite, POP ochre, SIM vermilion, MMR blue, EXPLORE green.
Links on paper are plum `#6B2F7D`.

## Type

- **Bodoni Moda** (OFL 1.1), weights 500 and 700: headlines and the needle labels. A didone, the face of classical
  record sleeves and printed programmes; its hairlines echo the needle.
- **Source Serif 4** (OFL 1.1), weights 400 and 600: liner-notes body, tables and charts, with tabular figures. A
  book face, clearly distinct from the high-contrast display.

Scale (1.25 on an 18 px body): 14.4, 18, 22.5, 28, 35, 44, 55 px. Body 66ch maximum.

## Layout

```
+---------------------------------------------------------------------------+
| (o) ECHO   Overview  Key result  Results  Taste map  Assumptions  ...      |  sticky, compact
+=========================== sleeve plum band ===============================+
| Question (Bodoni 55, pale)             |  [ sleeve ]( disc slides out )   |
| Answer sentence (Source Serif 22)      |        tonearm swings in         |
| author line                            |  "Illustration, not study data"  |
+===========================================================================+
| Key result: two records seen from above                                   |
|   EXP-002 synthetic          EXP-004 real FMA                              |
|   needles at each policy's   same, SIM now beyond RAND                     |
|   mean drift angle + CI arc  legend list with values                       |
+---------------------------------------------------------------------------+
| Overview (liner notes), Published results (forest plot, arm charts,        |
| experiment notes), Taste map (segmented policy control), Assumptions,      |
| Method and limitations, Sandbox (the listening booth), Footer (plum)       |
+---------------------------------------------------------------------------+
```

Text is left aligned in one liner-notes column; figures break out to the full width.

## Motion

- **Hero moment (once, on load).** The disc slides out of its sleeve while spinning and slows to rest (1.6 s,
  strong ease-out), then the tonearm swings onto the run-in groove (500 ms). It stops by itself well under five
  seconds, so nothing moves for long. It is an illustration and is labelled so; it shows no number.
- **Answers to actions.** The key-result needles swing from the start direction (0 rad) to their published
  angles once when scrolled into view (900 ms, 60 ms stagger); the taste-map policy control's indicator slides;
  the drift curves draw in once (clip-path); sandbox Run presses (scale 0.97) and its output rises in with
  `@starting-style`.
- **Reduced motion.** Everything renders in its final state.

## The one memorable thing

Taste as a needle angle: the published mean drift of each policy drawn as a needle on a record, synthetic and real
catalogues side by side, so the sign reversal is something you see rather than read.

## Review against the tells and the other demos

- The previous ECHO page was warm paper with a brick-red accent and a serif: tell 1 (cream plus terracotta).
  Replaced by lilac-white paper, plum and rose.
- A first draft used a near-black page with a neon pink accent (tell 2, and a cliche of music apps). Revised: the
  page is light; the dark is confined to the vinyl objects.
- The search tool proposed a dark OLED style with Righteous and Poppins and a purple and green palette. Rejected as
  a generic music-app look.
- First draft labelled sections "Side A" and "Side B" with track numbers. Removed: the page is not a sequence, and
  the conceit got in the way of plain section names.
- The old page's all-caps tracked tags (tell 5) are replaced by plain sentence-case tags with one border style per
  kind (solid measured, dashed exploratory, double sandbox, dotted assumption).
- Against the other studies: FARE (light itinerary, split-flap boards, condensed sans) is the nearest neighbour in
  structure; ECHO differs in palette (plum and rose against slate and amber), type (didone and book serif against
  condensed sans) and its central object (a rotating disc against a static board). MEMORY uses pencil and index
  cards; PULSE a control room; STREAK a daylight grade book.
- The record imagery is a visual metaphor: no audio is played, no real listener or service is depicted, and
  simulated preference change is not evidence of human persuasion.
