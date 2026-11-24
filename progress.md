<!-- SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0 -->
# Progress journal (append-only)

## 2026-11-24: Session 1 (M0, with M1 drafts)

**Milestone:** M0 bootstrap and feasibility. M1 drafts started.

**Starting state:** `git status` reported a clean tree on `main` at commit 44081a3 (master prompt and the owner's licence package).

### Commands run and actual outputs

```
$ sysctl -n machdep.cpu.brand_string hw.ncpu hw.memsize
Apple M1 Pro
10
17179869184
$ sw_vers
ProductName: macOS  ProductVersion: 15.3.1  BuildVersion: 24D70
$ df -h /Users/bechir/research/labs | tail -1
/dev/disk3s1   460Gi   311Gi   128Gi    71%  ...  /System/Volumes/Data
$ /usr/local/bin/python3 --version
Python 3.12.1
$ .tools/py/bin/uv --version
uv 0.9.5 (d5f39331a 2025-10-21)
$ .tools/pandoc --version | head -1
pandoc 3.6.3
$ /Users/bechir/research/helix/.tools/node/bin/node --version
v22.23.3
$ git --version
git version 2.42.1
$ which tex pdflatex xelatex typst
tex not found / pdflatex not found / xelatex not found / typst not found
$ .tools/py/bin/python -c "...versions"
typst 0.15.0 pypdf 6.20.0 pillow 11.3.0
$ uv lock --python /usr/local/bin/python3
Using CPython 3.12.1 interpreter at: /usr/local/bin/python3
Resolved 10 packages in 267ms
$ grep upload-time uv.lock | sort | tail -1
upload-time = "2026-10-15T09:50:58.343Z"
$ shasum -a 256 uv.lock
8f8a4bbcd5e8d8b7713ad14d02bd565324ef0722d077d080fed7932a34594a42  uv.lock
$ uv sync --frozen --python /usr/local/bin/python3
(installed numpy==2.2.6, pytest==8.3.5, hypothesis==6.131.9 and their dependencies into .venv/)
$ .venv/bin/python -c "import numpy; print(numpy.__version__)"
2.2.6
```

### Exploratory toolchain smoke check

This check is not research output. Its files were kept in the session scratchpad and are not committed. Journal entry: J-0001.

```
$ pandoc smoke.md -s -t typst -o smoke.typ && python -c "typst.compile(...)"
typst.TypstError: font fallback list must not be empty
$ pandoc smoke.md -s -t typst -V mainfont="Libertinus Serif" -o smoke.typ && python -c "typst.compile(...); pypdf..."
pages 1
Smoke / Toolchain check with an equation 𝑥2 and a table. / a b / 1 2 / 1
$ typst.compile(..., format="png", ppi=60)   # PNG inspected visually: heading, equation, table, page number render
$ pandoc smoke.md -s -t latex -o smoke.tex   # generated; not compiled (no TeX)
```

### Source audit (WebSearch and WebFetch, 2026-11-24)

- **Opened:** arXiv abstract pages for 1710.11214, 1902.10730, 2007.13019, 2204.11966, 1909.04847 and 1612.01840; the Meta Research publication page for Kalimeris et al. 2021; page 1 of the Vargas and Castells 2011 PDF; the FMA GitHub README; the MusicBrainz data licence page; Zenodo record 6090214 (Last.fm); the Dryad page for the Million Song Dataset.
- **Failed:** millionsongdataset.com (ECONNREFUSED); ocelma.net (self-signed certificate); dblp (bot protection).
- No dataset was downloaded.

### Decisions

DEC-001 to DEC-005 in `research/decision_log.md`. DEC-002 and DEC-005 are proposals that await the owner.

### Files created or changed

- Created:
  - `CLAUDE.md`, `roadmap.md`, `progress.md`, `README.md`, `CITATION.cff`, `pyproject.toml`, `uv.lock`
  - `research/{protocol,feasibility,literature_review,limitations,decision_log}.md`, `research/claims_register.csv` (header only), `research/experiment_journal.jsonl`, `research/experiment_registry.csv`
  - `research/experiments/EXP-00{1,2,3}/protocol.md`, `research/paper/manuscript.md` (skeleton), `research/paper/figures/README.md`, `research/publication/*`
  - `data/manifest.json`, README files in `results/`, `src/`, `tests/`, `experiments/`, `demo/`, `articles/`
- Appended: a development-commands section to `CONTRIBUTING.md`. The licence files are unchanged.

### Not done

- No code and no tests, so no test run.
- `research/paper/references.bib`, `manuscript.tex` and `supplementary.md` are deferred to M1 or M4. A PDF is not claimed.
- Not done in this session, by design: the protocol freeze, which is the owner's.

### Outstanding risks

- Drift results may be artefacts of the assumed update rule. EXP-003 addresses this.
- The parameter values are AI proposals.
- `manuscript.tex` cannot be compile-tested without TeX.

### Next action

M2: implement the RAND baseline, the catalogue and listener generators, the metrics and the result schema with tests. Then run EXP-001 as an exploratory run. In parallel, the owner reviews DEC-002, DEC-005, the SESOI and the parameters, and decides on the freeze.
