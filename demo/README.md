<!-- SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0 -->
# ECHO interactive page (demo)

A static research page for ECHO: overview and status, the published results with effect sizes and 95 % intervals (printed exactly as in the manuscript), every registered experiment with its status, frozen verdict and claim ids, the assumptions, the method and limitations, an exploratory taste map, and a sandbox. It runs offline after the first load, collects nothing about visitors and makes no request to any other host.

## Labels

- **Measured result:** a number from the committed confirmatory runs (`demo/public/data/results.json`, written by `scripts/export_demo_data.py`). The page fails closed: if the file is missing or malformed, it shows no numbers.
- **Exploratory illustration:** the taste map and drift curves come from one exploratory seed (950001) of the Python research engine (`results/exploratory/M5-taste-map/trace.json`, `scripts/m5_exploratory_engine_traces.py`). They support no claim.
- **Sandbox output:** produced in the browser from the visitor's settings by a port of the session loop (`src/engine.ts`) in a Web Worker. Given the same random inputs, the port reproduces the Python engine's slates and choices exactly and its preferences and metrics within 1e-9 (`src/engine.test.ts`, fixture `src/fixtures/engine_fixture.json`). The sandbox world is smaller (300 tracks, 40 listeners, 60 steps) and uses its own random-number generator, so a sandbox seed does not reproduce any research seed.
- **Assumption:** model parameters fixed by the frozen protocol.

## Commands

Node from a local install (the project used Node 22); dependencies are pinned in `package-lock.json`.

```sh
cd demo && npm ci && npm run build && npm run preview
npm test                                             # vitest: results validation and the engine-port fixture test
node tools/a11y_check.mjs dist --screenshots <dir>   # offline, keyboard, contrast, 360 px and reduced-motion checks
```

To refresh the data after a change to committed results: `PYTHONPATH=src .venv/bin/python scripts/export_demo_data.py` from the repository root (and `scripts/m5_exploratory_engine_traces.py` for the fixture and taste map). `tests/test_demo_export.py` fails if `results.json` differs from a fresh export or if any displayed number is not printed in the manuscript.

Public demo URL: [placeholder, not published; publication requires the owner's approval].
