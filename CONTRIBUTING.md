<!-- SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0 -->
# Contributing to ECHO

ECHO is an independent, source-available research project maintained by Mohamed Bechir Kefi: music recommendation feedback.

Technical suggestions, bug reports, reproducibility results, corrections and Pull Requests are welcome. The project is available for non-commercial research under the ECHO Source-Available Non-Commercial Research License v1.0 ([LICENSE](LICENSE)); it is not OSI-approved open-source software.

## 1. Before you start

For major changes, open an Issue first. Read `master_prompt.md`, `research/protocol.md` and `research/claims_register.csv`: frozen protocols are never changed silently, and every reported number must trace to a result file.

## 2. Pull Request requirements

- Your contribution is original or appropriately licensed, and you have the right to submit it.
- No credentials, secrets, confidential information or personal data.
- Relevant tests are included and pass; you report what you actually ran.
- Third-party dependencies and data sources are identified with their licenses.
- New files carry the header `SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0` where the format allows.
- You accept the Contributor License Agreement before your contribution is merged.

## 3. Contributor License Agreement

A recorded acceptance of [CLA.md](CLA.md) is required before merging copyrightable contributions. When you open a Pull Request, the "CLA Assistant" check comments on it; read the CLA, then post this exact comment:

    I have read the ECHO CLA v1.0 and I hereby sign it

The check records your public GitHub username and account ID, the date and the PR. You sign once. If the check does not update, comment `recheck`. Checking a box is not a signature; the comment is.

The CLA lets the maintainer use, modify, distribute, relicense and commercially exploit accepted contributions. You keep the copyright in your original contributions.

## 4. Governance

Mohamed Bechir Kefi is the project owner and lead maintainer, and the only person who can change the protected `main` branch. The maintainer decides the research direction, protocol freezes, claims, releases and licensing.

## 5. Privacy and disclosure

Never commit an e-mail address, a name or any other personal identifier in code, logs, fixtures or results. Report security issues privately through GitHub's private vulnerability reporting.

## 6. Development commands

Run from the repository root with uv 0.9.5:

    uv sync --frozen          # install the locked environment into .venv/
    uv lock                   # re-resolve (exclude-newer in pyproject.toml applies)
    uv run pytest             # test suite (no tests exist yet at M0)

Planned at M2 (not yet implemented): `uv run python -m echo.cli smoke|run|report`.

### M2 commands (implemented 2026-11-24)

The package lives in `src/echo`; put `src` on the path:

    PYTHONPATH=src uv run --frozen python -m echo.cli test                 # full test suite
    PYTHONPATH=src uv run --frozen python -m echo.cli smoke                # exploratory EXP-001 matrix and checks V1 to V6
    PYTHONPATH=src uv run --frozen python -m echo.cli report results/exploratory/EXP-001
    PYTHONPATH=src uv run --frozen python -m echo.cli run --config experiments/EXP-002/config.json   # refused until the owner freezes the protocol

### Real data (FMA metadata, added 2026-11-24)

```
python3 scripts/download_fma_metadata.py                                  # data/raw/ (git-ignored), checks the published SHA-1
PYTHONPATH=src .venv/bin/python scripts/build_fma_catalogue.py            # data/fma_calibration_v1.json and data/processed/ (git-ignored)
python3 tests/fixtures/make_fma_fixture.py                                # regenerates the synthetic FMA-schema test fixture
```

### M5 demo commands (added 2026-11-25)

```
PYTHONPATH=src .venv/bin/python scripts/m5_exploratory_engine_traces.py   # exploratory fixture and taste map (about 9 s)
PYTHONPATH=src .venv/bin/python scripts/export_demo_data.py               # demo/public/data/results.json from committed results
cd demo && npm ci && npm test && npm run build && node tools/a11y_check.mjs dist
```

### M6 publication commands (added 2026-11-25)

```
.venv/bin/python scripts/build_publication_pdfs.py --png-dir <scratch>/png   # manuscript, supplementary and report PDFs, manuscript.tex; optional page PNGs
.venv/bin/python scripts/check_links.py                                       # relative Markdown links, anchors and inline-code paths
```
