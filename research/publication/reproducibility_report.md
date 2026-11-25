<!-- SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0 -->
# Reproducibility report

Status: M6 clean-clone check done on 2026-11-25 at revision 6fa5f61 (the M5 commit, the current HEAD before M6 changes). The clone was a local `git clone` of the repository into a scratch directory outside it (no network), deleted afterwards. A second fresh clone after the M6 commit is recorded at the end. Machine: Apple M1 Pro, macOS 15.3.1, Python 3.12.1, uv 0.9.5, Node v22.23.3, npm 10.9.9.

- [x] Clean clone into a separate directory
- [x] uv sync --frozen
- [x] Test suite (actual counts recorded)
- [x] Smoke reproduction matches the committed results byte for byte (result files; manifests differ only in run-time fields)
- [x] Report and PDF build (M6 builder, working repository)
- [x] Demo build

## M6 clean-clone check (2026-11-25)

| Step | Command (in the clone) | Actual output |
|---|---|---|
| Clone | `git clone -q <repository> <scratch>/clone` | HEAD 6fa5f61 |
| Locked install | `../.tools/py/bin/uv sync --frozen --all-groups --all-extras` | 8 packages installed from `uv.lock` (numpy 2.2.6, pytest 8.3.5, hypothesis 6.131.9 and 5 dependencies); a second run: "Audited 8 packages" |
| Python tests | `.venv/bin/python -m pytest -q` | 183 passed in 29.45 s |
| Smoke reproduction | `PYTHONPATH=src .venv/bin/python -m echo.cli smoke` | 86 of 86 runs ok; V1 to V6 PASS; "ALL CHECKS PASS"; 112 s wall-clock |
| Smoke versus committed | `git status --short`, `git diff` | 86 files changed, all in `results/exploratory/EXP-001/manifests/`; the 86 result files in `runs/` and `checks.json` are byte-identical to the committed ones. Manifest differences: `started_utc`, `finished_utc`, `runtime_s`, `process_max_rss_bytes`, `git.revision`, and a `data_sha256` block that the M3 manifest writer adds (the committed EXP-001 manifests predate it) |
| Analysis re-run | `PYTHONPATH=src .venv/bin/python -m echo.analysis results/EXP-002 --planned 100 --kind policy` | rc 0; `git status` clean (analysis files byte-identical) |
| Demo export determinism | `PYTHONPATH=src .venv/bin/python scripts/export_demo_data.py` | wrote `demo/public/data/results.json` (197849 bytes); `git status` clean |
| Demo install | `npm ci --prefer-offline` | added 53 packages |
| Demo tests | `npm test` | Test Files 2 passed (2); Tests 29 passed (29) |
| Demo build | `npm run build` | index 253.15 kB JS, worker 10.65 kB, CSS 7.68 kB; built in 652 ms |
| Accessibility check | `node tools/a11y_check.mjs dist` | 9 PASS lines (results render, contrast light and dark, keyboard 29 of 29, focus indicator, no horizontal scroll at 360 px, reduced motion, no external request, offline); `A11Y-CHECK PASS` |

The documented smoke first failed when given `--out` outside the repository: "REFUSED or STOPPED: exploratory output must live under .../results/exploratory" (rc 2). This is the intended guard, not a defect; the README command (without `--out`) was then run as documented.

No failure needed a fix. The full checks were not repeated after the M6 PDF build: the builder only reads Markdown.

## PDFs (M6, working repository)

`.venv/bin/python scripts/build_publication_pdfs.py --typ-dir <scratch>/typ --png-dir <scratch>/png` (pandoc 3.6.3 to Typst, typst 0.15.0; `manuscript.tex` generated, not compiled): manuscript 14 pages, supplementary 7, EXP-001 report 4, EXP-002 6, EXP-003 7, EXP-004 5; every file below 0.2 MB. Every manuscript and supplementary page and every report page with a table was rendered at 60 ppi and inspected (see `progress.md`, M6).

## M4 partial check (2026-11-25, not the M6 clean-clone check)

- `echo.analysis` re-run on copies of the committed EXP-002, EXP-003 and EXP-004 runs and manifests, in a scratch directory outside the repository, with the committed commands: all 20 analysis files byte-identical to the committed ones.
- `shasum -a 256 -c SHA256SUMS` in each `results/EXP-00N/`: every entry OK.
- Simulation runs were not repeated (no confirmatory reruns in M4).
