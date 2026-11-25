<!-- SPDX-License-Identifier: LicenseRef-ECHO-NC-Research-1.0 -->
# Reproducibility report

Status: not started (M6 task). It will record the actual output of a clean-clone install from uv.lock, the test run, the smoke reproduction, the report build and the checksum comparison.

- [ ] Clean clone into a separate directory
- [ ] uv sync --frozen
- [ ] Test suite (actual counts recorded)
- [ ] Smoke reproduction matches the committed checksums within the documented tolerance
- [ ] Report and PDF build
- [ ] Demo build

## M4 partial check (2026-11-25, not the M6 clean-clone check)

- `echo.analysis` re-run on copies of the committed EXP-002, EXP-003 and EXP-004 runs and manifests, in a scratch directory outside the repository, with the committed commands: all 20 analysis files byte-identical to the committed ones.
- `shasum -a 256 -c SHA256SUMS` in each `results/EXP-00N/`: every entry OK.
- Simulation runs were not repeated (no confirmatory reruns in M4).
