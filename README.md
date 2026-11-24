<!-- SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0 -->
# ECHO: music recommendation feedback

**Question.** Can recommendation policies change exposure and simulated taste rather than simply reflect it?

**Status: M2 (core implementation) done; protocol not frozen.** The simulator, metrics, result schema, run manifests, report generator and tests exist. There are no findings: the only runs are exploratory verification and planning runs (EXP-001). The research protocol is a draft and is not frozen.

## Why it matters

Recommenders decide what listeners hear. If what listeners hear also moves what they like, the system's training signal partly reflects its own past choices. ECHO studies this in a small, seeded simulation. It is not a claim about any real service or any real listener.

## What exists now

- Control files: `CLAUDE.md`, `roadmap.md`, `progress.md`.
- Draft protocol: `research/protocol.md`, with per-experiment drafts in `research/experiments/EXP-001` to `EXP-003`.
- Feasibility audit: `research/feasibility.md`.
- Seed literature review: `research/literature_review.md`.
- Data source audit: `data/manifest.json`.
- Experiment registry: `research/experiment_registry.csv`.
- Locked dependencies: `pyproject.toml`, `uv.lock`.
- Simulator package `src/echo` and tests `tests/` (M2). Experiment configs in `experiments/`.
- Exploratory EXP-001 outputs (not findings): `results/exploratory/EXP-001/`.

## Experiments (protocols awaiting owner freeze)

| ID | Purpose | Status |
|---|---|---|
| EXP-001 | Simulator verification and smoke matrix (exploratory) | exploratory run (checks V1 to V6 pass); report not yet written |
| EXP-002 | Policy effect on simulated taste and exposure (primary) | planned |
| EXP-003 | Drift-assumption sensitivity and adaptation ablation | planned |

## Quick start

```sh
uv sync --frozen
PYTHONPATH=src uv run --frozen python -m echo.cli test
PYTHONPATH=src uv run --frozen python -m echo.cli smoke     # exploratory EXP-001, about 2 minutes
PYTHONPATH=src uv run --frozen python -m echo.cli report results/exploratory/EXP-001
```

`echo.cli run` refuses the confirmatory EXP-002 and EXP-003 configs until the owner freezes the protocol.

## Data

Primary data is synthetic. No dataset has been downloaded. Candidate public sources and their licences are listed in `data/manifest.json`.

## Limitations

See `research/limitations.md`. Simulated preference change is not evidence of human persuasion.

## Licence

The ECHO Source-Available Non-Commercial Research License v1.0 (`LICENSE`, SPDX `LicenseRef-ECHO-NC-Research-1.0`). It is source-available and is not an OSI open-source licence. Third-party material keeps its own terms (`NOTICE.md`).

## Citation

See `CITATION.cff`.
