<!-- SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0 -->
# Feasibility audit (M0, 2026-11-24)

All values below come from commands run in this session. The exact outputs are in `progress.md`.

## 1. Hardware

| Item | Command | Observed |
|---|---|---|
| CPU | `sysctl -n machdep.cpu.brand_string hw.ncpu` | Apple M1 Pro, 10 cores |
| Memory | `sysctl -n hw.memsize` | 17179869184 bytes (16 GiB) |
| OS | `sw_vers` | macOS 15.3.1 (24D70) |
| Free disk | `df -h ..` (the shared labs folder) | 128 GiB available (brief stated about 127 GB; consistent) |
| GPU | not used | CPU-only plan |

## 2. Tools

| Tool | Location | Observed version |
|---|---|---|
| Python | `/usr/local/bin/python3` | 3.12.1 |
| uv | `../.tools/py/bin/uv` | 0.9.5 |
| typst (Python package) | same environment | 0.15.0 |
| pypdf, pillow | same environment | 6.20.0, 11.3.0 |
| pandoc | `../.tools/pandoc` | 3.6.3 |
| Node | `../../helix/.tools/node/bin` (read-only) | v22.23.3 |
| git | system | 2.42.1 |
| TeX (tex, pdflatex, xelatex) | none | not installed |
| typst CLI | none | not on PATH (Python package used instead) |

## 3. Zero-cost publication toolchain (decision DEC-003)

There is no TeX distribution. The plan:

- Markdown is the canonical source.
- `pandoc -s -t typst -V mainfont="Libertinus Serif"` produces Typst, which the typst Python package compiles to PDF.
- `pandoc -s -t latex` produces `manuscript.tex`. It is not compiled locally, because there is no TeX.
- Pages are rendered to PNG through `typst.compile(..., format="png")` for visual inspection.

Exploratory smoke check (not research output; files kept in the session scratchpad, not in the repository):

- A Markdown file with an equation and a table was converted to Typst and LaTeX and compiled to a one-page PDF.
- pypdf read it back with the text intact.
- The PNG render was inspected visually.

Failure found and fixed: the default pandoc Typst template emits `font: ()` and typst fails with "font fallback list must not be empty". Passing `-V mainfont="Libertinus Serif"` fixes it.

## 4. Python environment

- `uv lock` resolved 10 packages: numpy 2.2.6, pytest 8.3.5, hypothesis 6.131.9 and their dependencies.
- `exclude-newer = 2026-11-10` enforces the two-week rule. The newest upload time in `uv.lock` is 2026-10-15.
- `uv sync --frozen` installed the environment into `.venv/` (git-ignored), and numpy 2.2.6 imports.

## 5. Time and compute budget

- Five focused days are targeted. The simulation is CPU-light: about 2 x 10^7 cosine evaluations per full run. This is an estimate, to be measured in EXP-001.
- The planned 460 confirmatory runs (EXP-002 plus EXP-003) are expected to fit well inside the 2-hour wall-clock cap. Not yet measured.
- Cost: zero. No paid services.

## 6. Scope and fallback

- Primary data: synthetic catalogue and listeners only.
- Optional real metadata: FMA metadata (CC BY 4.0) could later supply genre structure for item embeddings, but only with owner approval and as an exploratory extension.
- Fallback if the time budget is threatened: cut EXP-003 to the update-rule factor only (keep the invalidation check) and cut optional demo features. Never cut controls or reporting.

## 7. Risks

- R1: drift results may be artefacts of the assumed update rule. Mitigation: EXP-003.
- R2: the draft parameter values are AI proposals. They must be confirmed by the owner before freeze.
- R3: no TeX, so `manuscript.tex` is not compile-tested. The Typst PDF is the inspected artefact.
- R4: the shared tools live outside the repository. A clean clone (M6) needs uv and pandoc available.
